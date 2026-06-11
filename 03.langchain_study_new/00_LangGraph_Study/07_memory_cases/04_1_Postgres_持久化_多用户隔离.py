"""
Postgres 持久化 + 多用户隔离

这个案例演示两层记忆：
1. PostgresSaver：按 thread_id 保存线程内的消息历史（短期记忆）
2. PostgresStore：按 user_id 保存跨线程共享的用户资料（长期记忆）

效果：
- 同一个 thread_id：可以直接依赖历史消息继续对话
- 不同 thread_id 但同一个 user_id：可以从 PostgresStore 取回共享资料
- 不同 user_id：彼此隔离
"""

import os
import re
from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.postgres import PostgresStore

from env_utils import API_KEY, BASE_URL, MODEL_NAME


POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql:///postgres")

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0,
)


@dataclass
class Context:
    user_id: str


def call_model(state: MessagesState, runtime: Runtime[Context]):
    """
    先从 PostgresStore 里读共享资料，再把资料注入给模型。
    """
    last_human = next((m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), None)
    if last_human is None:
        return {"messages": [AIMessage(content="我还没有收到你的消息。")]}

    text = last_human.content.strip()
    user_id = runtime.context.user_id
    namespace = (user_id, "profile")

    match = re.search(r"我叫(?!什么)([A-Za-z\u4e00-\u9fa5·\-]{1,30})", text)
    if match:
        name = match.group(1)
        runtime.store.put(namespace, "profile", {"name": name})
        return {
            "messages": [
                AIMessage(
                    content=f"记住了，你叫{name}。我已经写入 PostgresStore，共享给这个 user_id 的所有线程。"
                )
            ]
        }

    item = runtime.store.get(namespace, "profile")
    memory_hint = ""
    if item and item.value.get("name"):
        memory_hint = f"共享资料显示，这个用户的名字是：{item.value['name']}。"

    ai_msg = model.invoke(
        [
            SystemMessage(
                content=(
                    "你是一个会结合共享用户资料回答问题的助手。"
                    "如果系统消息中给了用户资料，请优先依据资料回答。"
                    f"{memory_hint}"
                )
            ),
            *state["messages"],
        ]
    )
    return {"messages": [ai_msg]}


def build_graph(checkpointer, store):
    builder = StateGraph(MessagesState, context_schema=Context)
    builder.add_node("llm", call_model)
    builder.add_edge(START, "llm")
    builder.add_edge("llm", END)
    return builder.compile(checkpointer=checkpointer, store=store)


def main():
    with (
        PostgresSaver.from_conn_string(POSTGRES_URI) as checkpointer,
        PostgresStore.from_conn_string(POSTGRES_URI) as store,
    ):
        checkpointer.setup()
        store.setup()

        app = build_graph(checkpointer, store)

        same_user = Context(user_id="user-A")
        other_user = Context(user_id="user-B")

        thread_1 = {"configurable": {"thread_id": "pg-thread-1"}}
        thread_2 = {"configurable": {"thread_id": "pg-thread-2"}}
        thread_3 = {"configurable": {"thread_id": "pg-thread-3"}}

        q1 = app.invoke(
            {"messages": [HumanMessage(content="你好，我叫帅哥强")]},
            thread_1,
            context=same_user,
        )
        q2 = app.invoke(
            {"messages": [HumanMessage(content="我叫什么名字？")]},
            thread_2,
            context=same_user,
        )
        q3 = app.invoke(
            {"messages": [HumanMessage(content="我叫什么名字？")]},
            thread_3,
            context=other_user,
        )

        print("Q1:", q1["messages"][-1].content)
        print("Q2:", q2["messages"][-1].content)
        print("Q3:", q3["messages"][-1].content)


if __name__ == "__main__":
    main()
