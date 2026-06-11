"""
利用store: 不同线程，但是user_id相同可以相同的用户信息
"""

import re
from dataclasses import dataclass

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.memory import InMemoryStore
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime
from rich import inspect

from env_utils import MODEL_NAME, API_KEY, BASE_URL

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
)


@dataclass
class Context:
    user_id: str


def call_model(state: MessagesState, runtime: Runtime[Context], config: RunnableConfig):
    match = re.search(r"我叫(?!什么)([A-Za-z\u4e00-\u9fa5·\-]{1,30})", state["messages"][0].content)

    name = match.group(1) if match else None
    namespace = (runtime.context['user_id'], "profile")
    if name:
        # 记录store, store是覆盖更新
        item = runtime.store.get(namespace, 'info')

        old_value = item.value if item else {}

        runtime.store.put(namespace, "info", {
            **old_value,
            "name": name,
            "age": 18,
            "sex": "男"
        })
        print(f"runtime.store{runtime.store.get(namespace, 'info').value}")
        return {
            "messages": [
                AIMessage(
                    content=f"记住了，你叫{name}。我已经写入当前线程记忆，也同步到共享 store。"
                ),
            ]
        }

    if "我叫什么" in state["messages"][0].content:
        item = runtime.store.get(namespace, "info")
        print(f"item:{item}")
        if item:
            memory_hint = f"你从共享记忆中得知，这个用户的名字是：{item.value['name']}。"
            # 把 store 中的记忆显式注入给模型，而不是只在 Python 逻辑里读取
            prompt_messages = [
                SystemMessage(
                    content=(
                        "你是一个会结合共享记忆回答问题的助手。"
                        "如果系统消息里提供了用户资料，请优先依据该资料回答。"
                        f"{memory_hint}"
                    )
                ),
                *state["messages"],
            ]
            ai_msg = model.invoke(prompt_messages)
            return {"messages": [ai_msg]}

    ai_msg = model.invoke(state["messages"])
    return {"messages": ai_msg}


group = StateGraph(MessagesState)

group.add_node("call_model", call_model)

group.add_edge(START, "call_model")
group.add_edge("call_model", END)

group = group.compile(checkpointer=InMemorySaver(), store=InMemoryStore())


def message_handler(messages: MessagesState):
    message = ""
    for chunk, metaData in messages:
        if chunk.content:
            message += chunk.content

    return message


Q1 = message_handler(group.stream(
    {"messages": [{"role": "user", "content": "我叫帅哥强"}], },
    config={"configurable": {"thread_id": "11"}},
    context={
        "user_id": 'AA'
    },
    stream_mode="messages",
))
print(f"Q1的回答: {Q1}")

Q2 = message_handler(group.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": "还记得我叫什么吗？"
            }
        ]
    },
    config={
        "configurable": {
            "thread_id": "22"
        }
    },
    context={
        "user_id": 'AA'
    },
    stream_mode="messages"
))

print(f"Q2的回答: {Q2}")
Q3 = message_handler(group.stream(
    {
        "messages": [
            {
                "role": "user",
                "content": "还记得我叫什么吗？"
            }
        ]
    },
    config={
        "configurable": {
            "thread_id": "22"
        }
    },
    context={
        "user_id": 'CC'
    },
    stream_mode="messages"
))

print(f"Q3的回答: {Q3}")
