import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.runtime import Runtime
from langgraph.store.postgres import PostgresStore
from pydantic import BaseModel, Field
from rich import inspect

from env_utils import MODEL_NAME, API_KEY, BASE_URL

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
)

# 1.配置数据库
POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql:///postgres")


# 2.定义记忆参数
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


# 定义KV规则
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


# 这里的提取我更倾向于llm进行，而不是使用规则提取
def extract_stack(text: str) -> set[str]:
    stacks: set[str] = set()
    lower_text = text.lower()
    for stack_name, keywords in STACK_KEYWORDS.items():
        if any(keyword.lower() in lower_text for keyword in keywords):
            stacks.add(stack_name)
    return stacks


def contains_sensitive_info(text: str) -> bool:
    return any(pattern.search(text) for pattern in SENSITIVE_PATTERNS)


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

        # 重复内容清理 (数据库级别)
        if content in seen_content:
            runtime.store.delete(item.namespace, item.key)
            logs.append(f"治理层：删除重复 memory -> {content}")
            continue

        seen_content[content] = item.key

    append_audit_logs(runtime, thread_id, logs)
    return logs


def rule_extract_profile(text: str) -> tuple[dict, list[str]]:
    """提取用户最新的一条信息是否包含 name, role, stack"""

    name = extract_name(text)
    role = extract_role(text)
    stack_set: set[str] = set()
    profile_updates: dict = {}
    audit_logs: list[str] = []

    if name:
        audit_logs.append(f"规则提取：识别到用户 name={name}")
        profile_updates["name"] = name

    if role:
        audit_logs.append(f"规则提取：识别到用户 role={role}")
        profile_updates["role"] = role

    if contains_sensitive_info(text):
        audit_logs.append("敏感信息检测：发现手机号，后续不进入长期记忆")
    # 抽取技术栈
    stack_set.update(extract_stack(text))
    if stack_set:
        profile_updates["stack"] = sorted(stack_set)
        audit_logs.append(f"规则提取：识别到技术栈 {sorted(stack_set)}")

    return profile_updates, audit_logs


def llm_extract_memories(text: str) -> tuple[list[dict], list[str]]:
    """使用llm提取用户最新的一条信息"""
    structured_model = model.with_structured_output(LLMExtractionResult)  # 结构化输出
    llm_extraction_result = structured_model.invoke(f"""
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
{text}
""".strip())
    # result = llm_extraction_result
    memory_candidates: list[dict] = []
    audit_logs: list[str] = []
    for item in llm_extraction_result.memories:
        expires_at = None
        if item.expires_in_days:
            expires_at = (utcnow() + timedelta(days=item.expires_in_days)).isoformat()
        # 假设入表格式
        memory_candidates.append(
            {
                "type": item.memory_type,
                "content": item.content.strip(),
                "reason": item.reason.strip(),
                "source": "llm_extraction",
                "expires_at": expires_at,
            }
        )
        audit_logs.append(f"LLM提炼：{item.memory_type} ,原始内容: {item.content.strip()}")

    return memory_candidates, audit_logs


def store_memory(state: MessagesState, runtime: Runtime[Context], config: RunnableConfig):
    """调用模型"""
    # print(f"state: {state}")
    # print(f"runtime: {runtime}")
    # print(f"config: {config}")
    user_id = runtime.context.user_id
    namespace = (user_id, "profile")
    memories_namespace = (user_id, "memories")
    text = state["messages"][0].content
    if text is None:
        return {}

    # 提取记忆
    # 1.规则提取
    profile_updates, rule_logs = rule_extract_profile(text)
    # 2. LLM提炼
    memories_updates, llm_logs = llm_extract_memories(text)

    # 3.写入新数据 (覆盖旧数据)
    old_data = runtime.store.get(namespace, 'main').value or {}
    runtime.store.put(namespace, 'main', {**old_data, **profile_updates})

    # 4.写入记忆 （memories 是多条并存的数据，需要给每条记录一个独立且唯一的 key。）
    # 先读取当前用户已有的 memory，建立一个“按 content 查重”的索引。
    store_logs = ["存储分流：结构化资料写入 KV/profile"]
    existing_memory_items = runtime.store.search(memories_namespace, limit=100)
    existing_memory_contents = {
        item.value.get("content")
        for item in existing_memory_items
        if item.value.get("content")
    }
    print(f"memories_updates: {memories_updates}")
    for memory in memories_updates:
        content = memory["content"]

        if contains_sensitive_info(content):
            store_logs.append("治理前过滤：命中敏感内容，跳过写入 memory")
            continue
        # 重复内容清理 (当前对话级别)
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

    # 5. 写入审核日志
    thread_id = config["configurable"]["thread_id"]
    all_logs = [
        "第 1 层：从 MessagesState 采集最新用户输入",
        *rule_logs,
        *llm_logs,
        *store_logs,
    ]
    append_audit_logs(runtime, thread_id, all_logs)
    govern_memories(runtime, thread_id)
    return {}


def chat_with_memory(state: MessagesState, runtime: Runtime, config: RunnableConfig):
    """调用模型
        回答前做 memory 召回，把相关长期记忆再注入给模型。
        这就是“记忆系统”真正影响聊天回答的地方。
    """
    user_id = runtime.context.user_id
    user_question = state["messages"][0].content

    profile_item = runtime.store.get((user_id, "profile"), "main")
    memory_items = runtime.store.search(
        (user_id, "memories"),
        query=user_question,
        limit=5,
    )

    profile_hint = ""
    if profile_item:
        profile_hint = json.dumps(profile_item.value, ensure_ascii=False)  # 转换json字符串

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
    print(f"system_prompt: {system_prompt}")
    ai_msg = model.invoke([SystemMessage(content=system_prompt), *state["messages"]])
    return {"messages": [ai_msg]}


# 处理节点消息
def message_handler(messages):
    node_outputs: dict = {}
    for chunk, metaData in messages:
        node_name = metaData.get("langgraph_node", "unknown")
        if not chunk.content:
            continue
        node_outputs.setdefault(node_name, "")
        node_outputs[node_name] += chunk.content

    for node_name, content in node_outputs.items():
        print(f"\n[{node_name} {'-' * 50}]")
        print(content)


# 清理数据
def clear_demo_data(checkpointer: PostgresSaver, store: PostgresStore):
    """每次运行前，只清理当前案例自己固定使用的线程和用户数据。"""
    for thread_id in ["pg-thread-1", "pg-thread-2", "pg-thread-3"]:
        checkpointer.delete_thread(thread_id)

    for namespace in [("user-A", "profile"), ("user-B", "profile")]:
        for item in store.search(namespace, limit=100):
            store.delete(namespace, item.key)


# 初始化数据
def write_test_data(checkpointer: PostgresSaver, store: PostgresStore, user_id: str):
    """写入测试数据"""

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
        }
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
        }
    )


def main():
    with (
        PostgresSaver.from_conn_string(POSTGRES_URI) as checkpointer,
        PostgresStore.from_conn_string(POSTGRES_URI) as store,
    ):
        checkpointer.setup()
        store.setup()
        # 3.清理数据
        clear_demo_data(checkpointer, store)

        # 4. 写入测试数据
        write_test_data(checkpointer, store, "user-A")

        group = StateGraph(MessagesState)

        group.add_node("store_memory", store_memory)
        group.add_node("chat_with_memory", chat_with_memory)

        group.add_edge(START, "store_memory")

        group.add_edge("store_memory", "chat_with_memory")
        group.add_edge("chat_with_memory", END)

        app = group.compile(checkpointer, store=store)

        same_user = Context(user_id="user-A")
        other_user = Context(user_id="user-B")

        thread_1 = {"configurable": {"thread_id": "pg-thread-1"}}
        thread_2 = {"configurable": {"thread_id": "pg-thread-2"}}
        thread_3 = {"configurable": {"thread_id": "pg-thread-3"}}

        q1 = app.stream(
            {"messages": [HumanMessage(content="你好，我叫帅哥强，我主要做前端开发，平时用 React 和 TypeScript。")]},
            thread_1,
            context=same_user,
            stream_mode="messages"
        )

        q2 = app.stream(
            {"messages": [HumanMessage(content="我叫什么名字？")]},
            thread_2,
            context=same_user,
            stream_mode="messages"
        )
        # q3 = app.stream(
        #     {"messages": [HumanMessage(content="我叫什么名字？")]},
        #     thread_3,
        #     context=other_user,
        #     stream_mode="messages"
        # )
        #
        message_handler(q1)
        message_handler(q2)
        # print("Q2:", message_handler(q2))  # 同uid，不同线程，数据共享
        # print("Q3:", message_handler(q3))  # 不同账号


if __name__ == "__main__":
    main()
