"""
06_1. 聊天型 Graph + 四层记忆流水线（真实版）

这个版本更接近真实项目：
- graph 主状态使用 MessagesState
- 每轮聊天都会做“记忆提炼 -> 分流存储 -> 治理 -> 召回回答”
- 长期记忆存在 store，短期会话历史存在 checkpointer

你可以把它理解成：
1. 用户发来一条消息
2. agent 先从这条消息里提炼值得记住的信息
3. 结构化资料写 KV，非结构化资料写 memory
4. 做去重 / TTL 清理
5. 再把 relevant memory 召回给模型，生成回答

前端类比：
- MessagesState 像聊天页的 messageList
- checkpointer 像 thread 级会话状态
- store 像长期用户资料库 + 用户笔记库
"""

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore


@dataclass
class Context:
    user_id: str


class MemoryCandidate(BaseModel):
    """LLM 提炼出的单条长期/短期记忆候选。"""

    # preference = 用户偏好
    # interest = 用户当前关注/学习方向
    # temporary = 短期记忆，需要 TTL
    # fact = 相对稳定的事实
    memory_type: Literal["preference", "interest", "temporary", "fact"]
    # 最终要存入 memory store 的记忆文本。
    content: str
    # 为什么值得记，方便审计。
    reason: str
    # 过期天数，仅 temporary 通常会设置。
    expires_in_days: int | None = None


class LLMExtractionResult(BaseModel):
    """LLM 提炼层的结构化输出。"""

    memories: list[MemoryCandidate] = Field(default_factory=list)


model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=TEMPERATURE,
)

NAME_PATTERNS = [
    re.compile(r"我叫(?!什么)([A-Za-z\u4e00-\u9fa5·\-]{1,30})"),
    re.compile(r"我的名字是([A-Za-z\u4e00-\u9fa5·\-]{1,30})"),
]

ROLE_KEYWORDS = {
    "frontend_engineer": ["前端开发", "前端工程师", "做前端", "搞前端", "FE"],
}

STACK_KEYWORDS = {
    "React": ["React", "react.js", "React.js"],
    "TypeScript": ["TypeScript", "TS"],
    "LangGraph": ["LangGraph", "langgraph"],
}

SENSITIVE_PATTERNS = [
    re.compile(r"1\d{10}"),  # 手机号示例
]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


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


def extract_profile_by_rules(texts: list[str]) -> tuple[dict, list[str]]:
    """
    第 2 层的一部分：规则提取。
    适合处理强结构化、命中率高、错误成本高的字段。
    """
    profile_updates: dict = {}
    audit_logs: list[str] = []
    stack_set: set[str] = set()

    for text in texts:
        name = extract_name(text)
        if name:
            profile_updates["name"] = name
            audit_logs.append("规则提取：识别到用户 name")

        role = extract_role(text)
        if role:
            profile_updates["role"] = role
            audit_logs.append(f"规则提取：识别到用户 role={role}")

        # 抽取技术栈
        stack_set.update(extract_stack(text))

        if contains_sensitive_info(text):
            audit_logs.append("敏感信息检测：发现手机号，后续不进入长期记忆")

    if stack_set:
        profile_updates["stack"] = sorted(stack_set)
        audit_logs.append(f"规则提取：识别到技术栈 {sorted(stack_set)}")

    return profile_updates, audit_logs


def build_memory_extraction_prompt(texts: list[str]) -> str:
    joined = "\n".join(f"- {text}" for text in texts)
    return f"""
你是一个“用户长期记忆提炼器”。

请从下面这些用户输入里，提炼适合存进记忆系统的信息。

要求：
1. 只提炼对未来回答有帮助的信息。
2. 临时性任务、只对今天或这周有效的信息可以标记为 temporary。
3. 用户偏好、长期学习主题、稳定事实优先保留。
4. 不要提炼手机号、身份证、银行卡、邮箱、住址等敏感隐私。
5. 输出必须是结构化 JSON，对应字段：
   - memories: 列表
   - 每个 memory 包含：
     - memory_type: preference / interest / temporary / fact
     - content: 记忆文本
     - reason: 为什么值得记
     - expires_in_days: 只有 temporary 才设置，例如 1、3、7；长期记忆填 null

用户输入如下：
{joined}
""".strip()


def extract_memories_by_llm(texts: list[str]) -> tuple[list[dict], list[str]]:
    """
    第 2 层的另一部分：真实 LLM 提炼。
    它更适合提炼“长期偏好 / 当前主题 / 短期任务”这类语义型记忆。
    """
    structured_model = model.with_structured_output(LLMExtractionResult)

    result = structured_model.invoke(build_memory_extraction_prompt(texts))
    memory_candidates: list[dict] = []
    audit_logs = [f"LLM 提炼：产出 {len(result.memories)} 条 memory 候选"]

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
        audit_logs.append(f"LLM 提炼：{item.memory_type} -> {item.content.strip()}")

    return memory_candidates, audit_logs


def get_last_human_text(state: MessagesState) -> str:
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            return message.content.strip()
    return ""


def append_audit_logs(runtime: Runtime[Context], thread_id: str, logs: list[str]):
    """
    第 3 层：审计层。 通常是正常的数据库表，不要存到store里边
    审计日志也进 store，方便观察真实项目里“记忆为什么被写入/删除”。
    """
    audit_namespace = (runtime.context.user_id, thread_id, "audit")
    for log in logs:
        runtime.store.put(
            audit_namespace,
            str(uuid.uuid4()),
            {"message": log, "created_at": utcnow().isoformat()},
        )


def merge_profile(old_profile: dict, profile_updates: dict) -> dict:
    """
    真实项目里结构化资料更新通常不是简单覆盖。
    这里演示一个常见策略：
    - 普通字段后写覆盖前写
    - stack 这类列表字段做并集合并
    """
    merged = {**old_profile, **profile_updates}

    old_stack = old_profile.get("stack", [])
    new_stack = profile_updates.get("stack", [])
    if old_stack or new_stack:
        merged["stack"] = sorted(set(old_stack) | set(new_stack))

    return merged


def govern_memories(runtime: Runtime[Context], thread_id: str) -> list[str]:
    """
    第 4 层：治理层。
    当前演示两件最关键的事：
    - TTL 清理
    - 重复内容清理
    """
    user_id = runtime.context.user_id
    memories_namespace = (user_id, "memories")
    logs: list[str] = []

    items = runtime.store.search(memories_namespace, limit=100)
    seen_content: dict[str, str] = {}
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

        seen_content[content] = item.key

    append_audit_logs(runtime, thread_id, logs)
    return logs


def extract_and_store_memory(state: MessagesState, runtime: Runtime[Context], config):
    """
    第 1/2/3/4 层在聊天型 graph 里的真实落点：
    - 从 messages 里取最新用户输入
    - 规则提取 + LLM 提炼
    - 分流到 profile / memories
    - 做治理
    """
    thread_id = config["configurable"]["thread_id"]
    text = get_last_human_text(state)
    if not text:
        return {}

    profile_updates, rule_logs = extract_profile_by_rules([text])
    memory_candidates, llm_logs = extract_memories_by_llm([text])

    user_id = runtime.context.user_id
    profile_namespace = (user_id, "profile")
    memories_namespace = (user_id, "memories")

    old_profile_item = runtime.store.get(profile_namespace, "main")
    old_profile = old_profile_item.value if old_profile_item else {}
    merged_profile = merge_profile(old_profile, profile_updates)
    runtime.store.put(profile_namespace, "main", merged_profile)

    store_logs = ["存储分流：结构化资料写入 KV/profile"]

    # 先读取当前用户已有的 memory，建立一个“按 content 查重”的索引。
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
        )
        existing_memory_contents.add(content)
        store_logs.append(f"存储分流：新增 memory -> {content}")

    all_logs = [
        "第 1 层：从 MessagesState 采集最新用户输入",
        *rule_logs,
        *llm_logs,
        *store_logs,
    ]
    append_audit_logs(runtime, thread_id, all_logs)
    govern_memories(runtime, thread_id)

    return {}


def build_chat_prompt(state: MessagesState, runtime: Runtime[Context]) -> list:
    """
    回答前做 memory 召回，把相关长期记忆再注入给模型。
    这就是“记忆系统”真正影响聊天回答的地方。
    """
    user_id = runtime.context.user_id
    user_question = get_last_human_text(state)

    profile_item = runtime.store.get((user_id, "profile"), "main")
    memory_items = runtime.store.search(
        (user_id, "memories"),
        query=user_question,
        limit=5,
    )

    profile_hint = ""
    if profile_item:
        profile_hint = json.dumps(profile_item.value, ensure_ascii=False)

    memory_hint = "\n".join(
        f"- [{item.value.get('type')}] {item.value.get('content')}"
        for item in memory_items
        if item.value.get("content")
    )

    system_prompt = (
        "你是一个会结合用户长期记忆来回答问题的助手。\n"
        "优先使用结构化资料（profile），再参考召回到的长期记忆。\n"
        "如果某些信息没有把握，不要编造。\n"
        "不要扩展出 store 里不存在的细节，不要擅自增加用户偏好或经历。\n"
        "回答时只基于当前消息、profile 和召回到的长期记忆。\n"
        f"当前用户资料：{profile_hint or '{}'}\n"
        f"当前相关长期记忆：\n{memory_hint or '- 无'}"
    )

    return [SystemMessage(content=system_prompt), *state["messages"]]


def chat_with_memory(state: MessagesState, runtime: Runtime[Context]):
    """真正生成 AI 回复的节点。"""
    ai_msg = model.invoke(build_chat_prompt(state, runtime))
    return {"messages": [ai_msg]}


def read_store_snapshot(store: InMemoryStore, user_id: str, thread_id: str) -> str:
    """把 profile / memories / audit 都读出来，方便教学观察。"""
    profile_item = store.get((user_id, "profile"), "main")
    memories = store.search((user_id, "memories"), limit=100)
    audits = store.search((user_id, thread_id, "audit"), limit=200)

    profile_text = json.dumps(profile_item.value if profile_item else {}, ensure_ascii=False, indent=2)
    memory_lines = [
        f"- [{item.value.get('type')}] {item.value.get('content')}"
        for item in memories
        if item.value.get("content")
    ]
    audit_lines = [
        f"- {item.value.get('message')}"
        for item in audits
        if item.value.get("message")
    ]

    return "\n".join(
        [
            "---- Profile ----",
            profile_text,
            "",
            "---- Memories ----",
            *memory_lines,
            "",
            "---- Audit ----",
            *audit_lines,
        ]
    )


def seed_demo_data(store: InMemoryStore, user_id: str):
    """
    预置旧数据，方便演示治理和跨线程共享：
    - profile 已有 city
    - memories 有一条重复偏好
    - memories 有一条已过期临时记忆
    """
    store.put((user_id, "profile"), "main", {"city": "北京"})

    store.put(
        (user_id, "memories"),
        "seed-duplicate",
        {
            "type": "preference",
            "content": "用户喜欢用前端知识类比来理解 AI 框架。",
            "reason": "用于演示重复治理",
            "source": "seed",
            "expires_at": None,
            "created_at": utcnow().isoformat(),
        },
    )

    store.put(
        (user_id, "memories"),
        "seed-expired",
        {
            "type": "temporary",
            "content": "临时任务：今天调 streaming bug。",
            "reason": "用于演示 TTL 清理",
            "source": "seed",
            "expires_at": (utcnow() - timedelta(days=1)).isoformat(),
            "created_at": utcnow().isoformat(),
        },
    )


def build_graph():
    builder = StateGraph(MessagesState, context_schema=Context)
    builder.add_node("extract_and_store_memory", extract_and_store_memory)
    builder.add_node("chat_with_memory", chat_with_memory)
    builder.add_edge(START, "extract_and_store_memory")
    builder.add_edge("extract_and_store_memory", "chat_with_memory")
    builder.add_edge("chat_with_memory", END)
    return builder


def main():
    store = InMemoryStore()
    seed_demo_data(store, "user-chat-demo")

    app = build_graph().compile(
        checkpointer=InMemorySaver(),
        store=store,
    )

    same_user = Context(user_id="user-chat-demo")
    other_user = Context(user_id="user-chat-demo-2")

    r1 = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content="你好，我叫帅哥强，我主要做前端开发，平时用 React 和 TypeScript。"
                )
            ]
        },
        {"configurable": {"thread_id": "chat-memory-1"}},
        context=same_user,
    )

    r2 = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content="以后尽量用前端知识类比给我解释。我最近在学习 LangGraph 的 memory 和 middleware。"
                )
            ]
        },
        {"configurable": {"thread_id": "chat-memory-1"}},
        context=same_user,
    )

    # 换一个 thread，但还是同一个 user，验证“跨线程共享长期记忆”。
    r3 = app.invoke(
        {
            "messages": [
                HumanMessage(content="你记得我的名字、职业，还有我最近在学什么吗？")
            ]
        },
        {"configurable": {"thread_id": "chat-memory-2"}},
        context=same_user,
    )

    # 换另一个 user，验证用户隔离。
    r4 = app.invoke(
        {
            "messages": [
                HumanMessage(content="你记得我的名字吗？")
            ]
        },
        {"configurable": {"thread_id": "chat-memory-3"}},
        context=other_user,
    )

    print("第1轮回答:", r1["messages"][-1].content)
    print("第2轮回答:", r2["messages"][-1].content)
    print("第3轮回答（同 user，不同 thread）:", r3["messages"][-1].content)
    print("第4轮回答（不同 user）:", r4["messages"][-1].content)
    print()
    print(read_store_snapshot(store, "user-chat-demo", "chat-memory-2"))


if __name__ == "__main__":
    main()
