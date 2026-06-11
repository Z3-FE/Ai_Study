"""
05. Postgres + 向量检索（轻量 Memory-RAG）

这个 demo 演示同一个 PostgresStore 同时做两件事：
1. profile 走 KV：精确读取结构化资料（如 name）
2. memories 走语义检索：按 query 召回最相关的自然语言记忆

适合理解：
- KV memory 和 vector memory 不是二选一
- 用户资料与用户长期记忆可以共存于同一个 store 体系
"""

import os
import uuid
from dataclasses import dataclass

from psycopg import Connection
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.postgres import PostgresStore

from env_utils import API_KEY, BASE_URL, EMBEDDING_MODEL_NAME, MODEL_NAME

POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql:///postgres")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "0"))  # 允许自动探测真实维度

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0,
)


@dataclass
class Context:
    user_id: str


def clear_demo_data(checkpointer: PostgresSaver, store: PostgresStore):
    """每次运行前，仅清理本案例固定线程和固定 user 的数据。"""
    for thread_id in ["memory-rag-1", "memory-rag-2", "memory-rag-3", "memory-rag-4"]:
        checkpointer.delete_thread(thread_id)

    for namespace in [("user-memory-rag", "profile"), ("user-memory-rag", "memories")]:
        for item in store.search(namespace, limit=100):
            store.delete(item.namespace, item.key)


def reset_vector_schema():
    """
    这个 demo 需要与当前 embedding 维度一致。
    如果之前用别的维度（例如 1536）建过 store_vectors，
    这里直接重建向量相关表，避免 schema 维度冲突。
    """
    with Connection.connect(POSTGRES_URI, autocommit=True) as conn:
        with conn.cursor() as cur:
            # 每次运行前都重置本 demo 用到的 store/vector 表和迁移记录，
            # 确保重新执行时是干净环境。
            cur.execute("DROP TABLE IF EXISTS store_vectors CASCADE;")
            cur.execute("DROP TABLE IF EXISTS store CASCADE;")
            cur.execute("DROP TABLE IF EXISTS vector_migrations CASCADE;")
            cur.execute("DROP TABLE IF EXISTS store_migrations CASCADE;")


def save_profile_and_memories(store: PostgresStore, user_id: str):
    """写入一份结构化资料 + 三条自然语言长期记忆。"""
    store.put((user_id, "profile"), "profile",
              {"name": "帅哥强", "age": "25", "gender": "男", "city": "北京"}
              )

    memory_namespace = (user_id, "memories")
    memories = [
        "用户喜欢 React 和 TypeScript，平时主要做前端开发。",
        "用户最近在学习 LangGraph 的 memory、middleware 和 streaming。",
        "用户喜欢用前端知识类比来理解 AI 框架。",
    ]
    for text in memories:
        store.put(
            memory_namespace,
            str(uuid.uuid4()),
            {"memory": text},
            index=["memory"],
        )


def build_prompt(state: MessagesState, runtime: Runtime[Context]):
    user_id = runtime.context.user_id

    profile_item = runtime.store.get((user_id, "profile"), "profile")
    # 默认用的是余弦相似度
    memory_items = runtime.store.search(
        (user_id, "memories"),
        query=state["messages"][-1].content,
        limit=3,
    )

    profile_hint = ""
    if profile_item and profile_item.value.get("name"):
        profile_hint = f"用户名字是：{profile_item.value['name']}。"

    memory_hint = "\n".join(
        f"- {item.value['memory']}" for item in memory_items if item.value.get("memory")
    )

    return [
        SystemMessage(
            content=(
                "你是一个会结合用户长期记忆来回答问题的助手。"
                "结构化资料请直接使用；非结构化记忆请作为参考上下文。"
                f"{profile_hint}\n"
                f"以下是与当前问题最相关的长期记忆：\n{memory_hint}"
            )
        ),
        *state["messages"],
    ]


def call_model(state: MessagesState, runtime: Runtime[Context]):
    ai_msg = model.invoke(build_prompt(state, runtime))
    return {"messages": [ai_msg]}


def build_graph(checkpointer: PostgresSaver, store: PostgresStore):
    builder = StateGraph(MessagesState, context_schema=Context)
    builder.add_node("llm", call_model)
    builder.add_edge(START, "llm")
    builder.add_edge("llm", END)
    return builder.compile(checkpointer=checkpointer, store=store)


def main():
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL_NAME,
        api_key=API_KEY,
        base_url=BASE_URL,
        check_embedding_ctx_length=False,
    )
    dims = EMBEDDING_DIMS or len(embeddings.embed_query("LangGraph memory dimensions probe"))
    print(f"当前 embedding 维度: {dims}")
    # 重新执行脚本时，先清空本 demo 的 store/vector 数据和向量 schema。
    reset_vector_schema()

    with (
        PostgresSaver.from_conn_string(POSTGRES_URI) as checkpointer,
        PostgresStore.from_conn_string(
            POSTGRES_URI,
            index={
                "embed": embeddings,
                "dims": dims,
                "fields": ["memory"],
            },
        ) as store,
    ):
        checkpointer.setup()
        store.setup()
        save_profile_and_memories(store, "user-memory-rag")  # 写入用户资料和三条喜好的记忆

        app = build_graph(checkpointer, store)
        ctx = Context(user_id="user-memory-rag")

        q1 = app.invoke(
            {"messages": [HumanMessage(content="我最近在学什么？")]},
            {"configurable": {"thread_id": "memory-rag-1"}},
            context=ctx,
        )
        q2 = app.invoke(
            {"messages": [HumanMessage(content="我喜欢什么技术栈？")]},
            {"configurable": {"thread_id": "memory-rag-2"}},
            context=ctx,
        )
        q3 = app.invoke(
            {"messages": [HumanMessage(content="你知道我叫什么吗？")]},
            {"configurable": {"thread_id": "memory-rag-3"}},
            context=ctx,
        )

        print("Q1:", q1["messages"][-1].content)
        print("Q2:", q2["messages"][-1].content)
        print("Q3:", q3["messages"][-1].content)


if __name__ == "__main__":
    main()
