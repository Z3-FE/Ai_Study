"""
07. 生产级混合架构（最小版）

这个案例不再只关注“怎么提炼 memory”，而是演示一个更接近真实聊天产品的
最小混合架构：

1. 短期会话层：MessagesState + PostgresSaver
   - 负责同一 thread 的多轮消息历史

2. 用户长期资料层：profile (KV)
   - 负责 name / role / stack 这类结构化长期资料

3. 用户长期记忆层：memories (semantic search)
   - 负责 preference / interest / fact / temporary 这类自然语言记忆

4. 业务会话层：conversations / messages
   - 模拟真实产品里“左侧会话列表 + 消息列表”的存储
   - 为了让学习重点集中，这里仍然用 PostgresStore namespace 来模拟
     业务表分层；真实项目里通常会做成正式业务表

5. 治理与审计层：audit + TTL + 去重
   - 负责解释“为什么写入、为什么删除、什么时候过期”

你可以把它理解成：
06_2 更像“记忆系统已经接进了聊天图”
07   更像“聊天产品的数据分层已经开始成型”
"""

import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.postgres import PostgresStore
from psycopg import Connection
from pydantic import BaseModel, Field

from env_utils import API_KEY, BASE_URL, EMBEDDING_MODEL_NAME, MODEL_NAME

POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql:///postgres")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "0"))

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0,
)


@dataclass
class Context:
    user_id: str


class MemoryCandidate(BaseModel):
    """模型提炼出的单条 memory 候选。"""

    memory_type: Literal["preference", "interest", "temporary", "fact"]
    content: str
    reason: str
    expires_in_days: int | None = None


class LLMExtractionResult(BaseModel):
    """模型提炼的结构化结果。"""

    memories: list[MemoryCandidate] = Field(default_factory=list)


NAME_PATTERNS = [
    re.compile(r"我叫(?!什么)([A-Za-z\u4e00-\u9fa5·\-]{1,30})"),
    re.compile(r"我的名字是([A-Za-z\u4e00-\u9fa5·\-]{1,30})"),
]

ROLE_KEYWORDS = {
    "frontend_engineer": ["前端开发", "前端工程师", "做前端", "搞前端", "FE"],
}

STACK_KEYWORDS = {
    "React": ["React", "React.js", "react.js"],
    "TypeScript": ["TypeScript", "TS"],
    "LangGraph": ["LangGraph", "langgraph"],
}

SENSITIVE_PATTERNS = [
    re.compile(r"1\d{10}"),  # 手机号
]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def reset_store_schema():
    """
    这个案例同时用到了普通 KV 和语义检索。
    为了保证每次重跑都是干净的，这里重建本案例依赖的 store/vector 表。
    """
    with Connection.connect(POSTGRES_URI, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS store_vectors CASCADE;")
            cur.execute("DROP TABLE IF EXISTS store CASCADE;")
            cur.execute("DROP TABLE IF EXISTS vector_migrations CASCADE;")
            cur.execute("DROP TABLE IF EXISTS store_migrations CASCADE;")


def extract_name(text: str) -> str | None:
    for pattern in NAME_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def extract_role(text: str) -> str | None:
    for role, keywords in ROLE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return role
    return None


def extract_stack(text: str) -> set[str]:
    stacks: set[str] = set()
    lower_text = text.lower()
    for stack_name, keywords in STACK_KEYWORDS.items():
        if any(keyword.lower() in lower_text for keyword in keywords):
            stacks.add(stack_name)
    return stacks


def contains_sensitive_info(text: str) -> bool:
    return any(pattern.search(text) for pattern in SENSITIVE_PATTERNS)


def get_last_human_text(state: MessagesState) -> str:
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            return message.content.strip()
    return ""


def get_last_ai_text(state: MessagesState) -> str:
    for message in reversed(state["messages"]):
        if isinstance(message, AIMessage):
            return message.content.strip()
    return ""


def append_audit_logs(runtime: Runtime[Context], logs: list[str]):
    """
    审计层：演示真实项目里“处理过程日志”应独立于 profile/memories。
    这里仍用独立 namespace 模拟，真实项目通常会落到单独业务表。
    """
    audit_namespace = (runtime.context.user_id, "audit")
    for log in logs:
        runtime.store.put(
            audit_namespace,
            str(uuid.uuid4()),
            {"message": log, "created_at": utcnow().isoformat()},
        )


def merge_profile(old_profile: dict, profile_updates: dict) -> dict:
    merged = {**old_profile, **profile_updates}
    if old_profile.get("stack") or profile_updates.get("stack"):
        merged["stack"] = sorted(
            set(old_profile.get("stack", [])) | set(profile_updates.get("stack", []))
        )
    return merged


def rule_extract_profile(text: str) -> tuple[dict, list[str]]:
    profile_updates: dict = {}
    logs: list[str] = []
    stack_set: set[str] = set()

    name = extract_name(text)
    if name:
        profile_updates["name"] = name
        logs.append(f"规则提取：识别到用户 name={name}")

    role = extract_role(text)
    if role:
        profile_updates["role"] = role
        logs.append(f"规则提取：识别到用户 role={role}")

    stack_set.update(extract_stack(text))
    if stack_set:
        profile_updates["stack"] = sorted(stack_set)
        logs.append(f"规则提取：识别到技术栈 {sorted(stack_set)}")

    if contains_sensitive_info(text):
        logs.append("敏感信息检测：命中手机号，后续不进入长期记忆")

    return profile_updates, logs


def build_memory_extraction_prompt(text: str) -> str:
    return f"""
你是一个“用户长期记忆提炼器”。

请从下面这段最新用户输入里，提炼适合进入长期记忆系统的信息。

要求：
1. 只提炼对未来回答有帮助的信息。
2. 用户偏好、长期学习主题、稳定事实优先保留。
3. 临时性任务可标记为 temporary，并给出过期天数。
4. 不要提炼手机号、身份证、银行卡、邮箱、住址等敏感隐私。
5. 你只能输出合法 JSON，不能输出 markdown 代码块，不能附加解释。
6. JSON 结构必须是：
   {{
     "memories": [
       {{
         "memory_type": "preference | interest | temporary | fact",
         "content": "记忆文本",
         "reason": "为什么值得记",
         "expires_in_days": 1
       }}
     ]
   }}
7. 如果没有值得提炼的记忆，请输出：{{"memories": []}}

用户输入如下：
{text}
""".strip()


def llm_extract_memories(text: str) -> tuple[list[dict], list[str]]:
    """
    为了保持运行稳定，这里使用：
    - 普通 invoke
    - JSON 解析
    - Pydantic model_validate

    真实项目里通常优先使用 with_structured_output；
    当前写法更偏“兼容性更稳的 demo 版”。
    """
    ai_msg = model.invoke(
        [
            SystemMessage(content="你是一个严格输出 JSON 的长期记忆提炼助手。"),
            HumanMessage(content=build_memory_extraction_prompt(text)),
        ]
    )
    output_text = ai_msg.content.strip() if isinstance(ai_msg.content, str) else ""
    parsed = json.loads(output_text)
    result = LLMExtractionResult.model_validate(parsed)

    memory_candidates: list[dict] = []
    logs = [f"LLM 提炼：产出 {len(result.memories)} 条 memory 候选"]

    for item in result.memories:
        expires_at = None
        if item.expires_in_days:
            expires_at = (utcnow() + timedelta(days=item.expires_in_days)).isoformat()

        memory_candidates.append(
            {
                "type": item.memory_type,
                "content": item.content.strip(),
                "reason": item.reason.strip(),
                "source": "llm_extraction",
                "expires_at": expires_at,
            }
        )
        logs.append(f"LLM 提炼：{item.memory_type} -> {item.content.strip()}")

    return memory_candidates, logs


def upsert_conversation_meta(runtime: Runtime[Context], thread_id: str, latest_text: str):
    """
    业务层：模拟 conversations 表。 对话表
    真实产品里左侧会话列表通常是独立业务表，这里先用 namespace 模拟。

    这里模拟的 conversations 表字段含义：
    - thread_id:
        当前会话在线上运行时对应的 thread 标识。
        在这个 demo 里，它临时兼任了 conversation_id 的角色。
    - title:
        左侧会话列表展示的标题。通常来自第一轮用户输入的摘要，
        真实项目里也可以异步用模型生成更自然的标题。
    - last_message_preview:
        左侧会话列表里展示的最后一条消息预览。
        它的意义是让列表页快速展示“最近聊了什么”，不用每次都去消息明细里查最后一条。
    - updated_at:
        会话最近一次活跃时间。左侧会话列表通常按它倒序排列。
    - created_at:
        会话创建时间。用于会话归档、统计和排序。
    """
    namespace = (runtime.context.user_id, "conversations")
    existing = runtime.store.get(namespace, thread_id)
    now = utcnow().isoformat()
    title = latest_text[:18] + ("..." if len(latest_text) > 18 else "")

    payload = {
        # 当前会话标识。真实项目里通常会单独有 conversation_id，
        # 这里只是用 thread_id 模拟业务会话主键。
        "thread_id": thread_id,
        # 左侧会话标题：首次进入时由用户输入生成，后续保留已有标题。
        "title": existing.value["title"] if existing and existing.value.get("title") else title,
        # 最后一条消息的预览文本：服务左侧列表快速展示。
        "last_message_preview": latest_text[:60],
        # 最近活跃时间：最后一条 user/assistant 消息写入时更新。
        "updated_at": now,
        # 会话创建时间：只在第一次创建 conversation 时写入。
        "created_at": existing.value["created_at"] if existing else now,
    }
    runtime.store.put(namespace, thread_id, payload)


def persist_business_message(runtime: Runtime[Context], thread_id: str, role: str, content: str):
    """
    业务层：模拟 messages 表。
    真实产品里通常是正式业务表；这里用 namespace 分层演示数据职责。

    这里模拟的 messages 表字段含义：
    - role:
        这条消息是谁发的。常见值是 user / assistant。
        真实产品里有时也会有 system / tool。
    - content:
        消息正文。右侧聊天区域真正展示的内容。
    - created_at:
        这条消息的创建时间。用于按时间排序、分页、审计。

    说明：
    - 这里没有额外存 conversation_id 字段，
      是因为当前 demo 把 (user_id, thread_id, "messages") 这个 namespace
      当成了“某个会话下的消息集合”。
    - 真实项目里更常见的正式字段通常会是：
      message_id / conversation_id / user_id / role / content / created_at
    """
    namespace = (runtime.context.user_id, thread_id, "messages")
    runtime.store.put(
        namespace,
        str(uuid.uuid4()),
        {
            # 谁发的消息。真实项目里常见值：user / assistant / tool / system
            "role": role,
            # 消息正文。右侧聊天记录真正展示的内容。
            "content": content,
            # 消息创建时间。真实项目里通常用于排序和分页。
            "created_at": utcnow().isoformat(),
        },
    )


def govern_memories(runtime: Runtime[Context]) -> list[str]:
    memories_namespace = (runtime.context.user_id, "memories")
    logs: list[str] = []
    items = runtime.store.search(memories_namespace, limit=100)
    seen_content: set[str] = set()
    now = utcnow()

    for item in items:
        value = item.value
        content = value.get("content", "")
        expires_at = value.get("expires_at")

        if expires_at:
            expire_time = datetime.fromisoformat(expires_at)
            if expire_time <= now:
                runtime.store.delete(item.namespace, item.key)
                logs.append(f"治理层：TTL 清理已过期 memory -> {content}")
                continue

        if content in seen_content:
            runtime.store.delete(item.namespace, item.key)
            logs.append(f"治理层：删除重复 memory -> {content}")
            continue

        seen_content.add(content)

    return logs


def collect_and_persist(state: MessagesState, runtime: Runtime[Context], config: RunnableConfig):
    """
    这一层同时做 3 件事：
    1. 采集最新用户输入
    2. 提炼并写入长期记忆
    3. 写入业务侧 conversations/messages
    """
    thread_id = config["configurable"]["thread_id"]
    text = get_last_human_text(state)
    if not text:
        return {}

    upsert_conversation_meta(runtime, thread_id, text)
    persist_business_message(runtime, thread_id, "user", text)

    profile_updates, rule_logs = rule_extract_profile(text)
    memory_candidates, llm_logs = llm_extract_memories(text)

    user_id = runtime.context.user_id
    profile_namespace = (user_id, "profile")
    memories_namespace = (user_id, "memories")

    old_profile_item = runtime.store.get(profile_namespace, "main")
    old_profile = old_profile_item.value if old_profile_item else {}
    merged_profile = merge_profile(old_profile, profile_updates)
    runtime.store.put(profile_namespace, "main", merged_profile)

    store_logs = ["存储分流：结构化资料写入 KV/profile"]
    existing_memory_items = runtime.store.search(memories_namespace, limit=100)
    existing_memory_contents = {
        item.value.get("content")
        for item in existing_memory_items
        if item.value.get("content")
    }

    for memory in memory_candidates:
        content = memory["content"]

        if contains_sensitive_info(content):
            store_logs.append("治理前过滤：命中敏感内容，跳过写入 memory")
            continue

        if content in existing_memory_contents:
            store_logs.append(f"存储分流：检测到重复 memory，暂不重复写入 -> {content}")
            continue

        runtime.store.put(
            memories_namespace,
            str(uuid.uuid4()),
            {
                "type": memory["type"],
                "content": content,
                "reason": memory["reason"],
                "source": memory["source"],
                "expires_at": memory["expires_at"],
                "created_at": utcnow().isoformat(),
            },
            index=["content"],
        )
        existing_memory_contents.add(content)
        store_logs.append(f"存储分流：新增 memory -> {content}")

    governance_logs = govern_memories(runtime)
    append_audit_logs(
        runtime,
        [
            "会话层：新消息进入当前 thread",
            "业务层：写入 conversations/messages",
            *rule_logs,
            *llm_logs,
            *store_logs,
            *governance_logs,
        ],
    )
    return {}


def build_hybrid_prompt(state: MessagesState, runtime: Runtime[Context], config: RunnableConfig) -> list:
    """
    回答层：统一消费三类上下文
    1. 当前 thread 的短期消息（来自 MessagesState + Checkpointer）
    2. 用户 profile（结构化长期资料）
    3. 相关 memories（语义召回）
    """
    user_id = runtime.context.user_id
    thread_id = config["configurable"]["thread_id"]
    user_question = get_last_human_text(state)

    profile_item = runtime.store.get((user_id, "profile"), "main")
    conversation_item = runtime.store.get((user_id, "conversations"), thread_id)
    memory_items = runtime.store.search(
        (user_id, "memories"),
        query=user_question,
        limit=5,
    )

    profile_hint = json.dumps(profile_item.value, ensure_ascii=False) if profile_item else "{}"
    conversation_hint = (
        json.dumps(conversation_item.value, ensure_ascii=False) if conversation_item else "{}"
    )
    memory_hint = "\n".join(
        f"- [{item.value.get('type')}] {item.value.get('content')}"
        for item in memory_items
        if item.value.get("content")
    )

    system_prompt = (
        "你是一个会结合多层记忆来回答问题的助手。\n"
        "请综合使用：当前 thread 的消息历史、用户 profile、语义召回到的长期 memories。\n"
        "不要扩展出 store 中不存在的细节，不要擅自脑补新的用户事实。\n"
        f"当前会话元信息：{conversation_hint}\n"
        f"当前用户 profile：{profile_hint}\n"
        f"当前相关长期 memories：\n{memory_hint or '- 无'}"
    )
    return [SystemMessage(content=system_prompt), *state["messages"]]


def reply(state: MessagesState, runtime: Runtime[Context], config: RunnableConfig):
    ai_msg = model.invoke(build_hybrid_prompt(state, runtime, config))
    return {"messages": [ai_msg]}


def persist_assistant_reply(state: MessagesState, runtime: Runtime[Context], config: RunnableConfig):
    """
    业务层：把最终 assistant 回复也写入消息列表。
    这一步强调：业务消息表和 graph state/checkpoint 是两层不同职责。
    """
    thread_id = config["configurable"]["thread_id"]
    ai_text = get_last_ai_text(state)
    if not ai_text:
        return {}

    persist_business_message(runtime, thread_id, "assistant", ai_text)
    upsert_conversation_meta(runtime, thread_id, ai_text)
    append_audit_logs(runtime, [f"业务层：持久化 assistant 消息 -> {ai_text[:40]}"])
    return {}


def build_graph():
    builder = StateGraph(MessagesState, context_schema=Context)
    builder.add_node("collect_and_persist", collect_and_persist)
    builder.add_node("reply", reply)
    builder.add_node("persist_assistant_reply", persist_assistant_reply)

    builder.add_edge(START, "collect_and_persist")
    builder.add_edge("collect_and_persist", "reply")
    builder.add_edge("reply", "persist_assistant_reply")
    builder.add_edge("persist_assistant_reply", END)
    return builder


def clear_namespace(store: PostgresStore, namespace: tuple[str, ...]):
    for item in store.search(namespace, limit=200):
        store.delete(item.namespace, item.key)


def clear_demo_data(checkpointer: PostgresSaver, store: PostgresStore):
    for thread_id in ["hybrid-1", "hybrid-2", "hybrid-3", "hybrid-4"]:
        checkpointer.delete_thread(thread_id)

    for user_id in ["user-A", "user-B"]:
        clear_namespace(store, (user_id, "profile"))
        clear_namespace(store, (user_id, "memories"))
        clear_namespace(store, (user_id, "conversations"))
        clear_namespace(store, (user_id, "audit"))
        for thread_id in ["hybrid-1", "hybrid-2", "hybrid-3", "hybrid-4"]:
            clear_namespace(store, (user_id, thread_id, "messages"))


def read_snapshot(store: PostgresStore, user_id: str, thread_id: str) -> str:
    profile = store.get((user_id, "profile"), "main")
    conversation = store.get((user_id, "conversations"), thread_id)
    memories = store.search((user_id, "memories"), limit=20)
    messages = store.search((user_id, thread_id, "messages"), limit=20)
    audits = store.search((user_id, "audit"), limit=20)

    snapshot = {
        "profile": profile.value if profile else {},
        "conversation": conversation.value if conversation else {},
        "memories_count": len(memories),
        "messages_count": len(messages),
        "audit_count": len(audits),
    }
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def main():
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL_NAME,
        api_key=API_KEY,
        base_url=BASE_URL,
        check_embedding_ctx_length=False,
    )
    dims = EMBEDDING_DIMS or len(embeddings.embed_query("LangGraph hybrid memory probe"))
    print(f"当前 embedding 维度: {dims}")

    reset_store_schema()

    with (
        PostgresSaver.from_conn_string(POSTGRES_URI) as checkpointer,
        PostgresStore.from_conn_string(
            POSTGRES_URI,
            index={
                "embed": embeddings,
                "dims": dims,
                "fields": ["content"],
            },
        ) as store,
    ):
        checkpointer.setup()
        store.setup()
        clear_demo_data(checkpointer, store)

        app = build_graph().compile(checkpointer=checkpointer, store=store)

        same_user = Context(user_id="user-A")
        other_user = Context(user_id="user-B")

        r1 = app.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="你好，我叫帅哥强，我主要做前端开发，平时用 React 和 TypeScript。"
                    )
                ]
            },
            {"configurable": {"thread_id": "hybrid-1"}},
            context=same_user,
        )
        r2 = app.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="以后尽量用前端类比解释，我最近在学 LangGraph 的 memory 和 middleware。"
                    )
                ]
            },
            {"configurable": {"thread_id": "hybrid-2"}},
            context=same_user,
        )
        r3 = app.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="你记得我的名字、职业、技术栈，还有我最近在学什么吗？"
                    )
                ]
            },
            {"configurable": {"thread_id": "hybrid-3"}},
            context=same_user,
        )
        r4 = app.invoke(
            {"messages": [HumanMessage(content="你记得我的名字吗？")]},
            {"configurable": {"thread_id": "hybrid-4"}},
            context=other_user,
        )

        print("Q1:", r1["messages"][-1].content)
        print("Q2:", r2["messages"][-1].content)
        print("Q3:", r3["messages"][-1].content)
        print("Q4:", r4["messages"][-1].content)

        print("\n[user-A / hybrid-3 snapshot]")
        print(read_snapshot(store, "user-A", "hybrid-3"))
        print("\n[user-B / hybrid-4 snapshot]")
        print(read_snapshot(store, "user-B", "hybrid-4"))


if __name__ == "__main__":
    main()
