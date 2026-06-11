import os
import re
from dataclasses import dataclass
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.runtime import Runtime
from langgraph.store.postgres import PostgresStore

from env_utils import MODEL_NAME, API_KEY, BASE_URL

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
)

# 配置数据库
POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql:///postgres")


@dataclass
class Context:
    user_id: str


def call_model(state: MessagesState, runtime: Runtime[Context], config: RunnableConfig):
    """调用模型"""
    # print(f"runtime: {runtime}")
    # print(f"state: {state}")
    match = re.search(r"我叫(?!什么)([A-Za-z\u4e00-\u9fa5·\-]{1,30})", state["messages"][0].content)
    name = match.group(1) if match else None

    user_id = runtime.context.user_id
    namespace = (user_id, "info")

    if name:
        old_data = runtime.store.get(namespace, 'info').value or {}

        runtime.store.put(namespace, "info", {
            **old_data,
            "name": name
        })

    item = runtime.store.get(namespace, 'info') or None
    if "我叫什么" in state["messages"][0].content and item:
        memory_hint = f"你从共享记忆中得知，这个用户的名字是：{item.value['name']}。"
        messages = [
            SystemMessage(
                content=(
                    "你是一个会结合共享用户资料回答问题的助手。"
                    "如果系统消息中给了用户资料，请优先依据资料回答。"
                    f"{memory_hint}"
                )
            ),
            *state["messages"],
        ]
        ai_msg = model.invoke(messages)
        return {"messages": [ai_msg]}

    ai_msg = model.invoke(state["messages"])
    return {
        "messages": [ai_msg]
    }


group = StateGraph(MessagesState)

group.add_node("call_model", call_model)

group.add_edge(START, "call_model")
group.add_edge("call_model", END)


def message_handler(messages: MessagesState):
    """从流中提取消息内容"""
    message = ""
    for chunk, metaData in messages:
        if chunk.content:
            message += chunk.content

    return message


def clear_demo_data(checkpointer: PostgresSaver, store: PostgresStore):
    """每次运行前，只清理当前案例自己固定使用的线程和用户数据。"""
    for thread_id in ["pg-thread-1", "pg-thread-2", "pg-thread-3"]:
        checkpointer.delete_thread(thread_id)

    for namespace in [("user-A", "profile"), ("user-B", "profile")]:
        for item in store.search(namespace, limit=100):
            store.delete(namespace, item.key)


def main():
    """
    1. 同uid，不同线程，数据共享
    2. 不同uid，同线程或不同线程，数据不共享
    """
    with (
        PostgresSaver.from_conn_string(POSTGRES_URI) as checkpointer,
        PostgresStore.from_conn_string(POSTGRES_URI) as store,
    ):
        checkpointer.setup()
        store.setup()
        clear_demo_data(checkpointer, store)

        app = group.compile(checkpointer, store=store)

        same_user = Context(user_id="user-A")
        other_user = Context(user_id="user-B")

        thread_1 = {"configurable": {"thread_id": "pg-thread-1"}}
        thread_2 = {"configurable": {"thread_id": "pg-thread-2"}}
        thread_3 = {"configurable": {"thread_id": "pg-thread-3"}}

        q1 = app.stream(
            {"messages": [HumanMessage(content="你好，我叫帅哥强")]},
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
        q3 = app.stream(
            {"messages": [HumanMessage(content="我叫什么名字？")]},
            thread_3,
            context=other_user,
            stream_mode="messages"
        )

        print("Q1:", message_handler(q1))
        print("Q2:", message_handler(q2))  # 同uid，不同线程，数据共享
        print("Q3:", message_handler(q3))  # 不同账号


if __name__ == "__main__":
    main()
