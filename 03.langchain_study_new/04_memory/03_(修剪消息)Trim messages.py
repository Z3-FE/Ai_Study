"""修剪消息

参考 LangChain / LangGraph 官方方案：
在模型调用前，通过 middleware 只保留最近几条消息，避免上下文越来越长。

本例重点：
1. 使用 InMemorySaver 保存当前线程的会话状态
2. 使用 before_model 中间件修剪 messages
3. 即使修剪消息，也尽量保留“用户名字”这类关键信息
"""

from typing import Any

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import before_model, after_model
from langchain.messages import RemoveMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime
from rich import inspect

from env_utils import API_KEY, BASE_URL, MODEL_NAME

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
)


@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """在模型调用前修剪消息，只保留首条消息和最近几条消息。"""
    del runtime  # 本例不使用 runtime，但保留参数以匹配官方 middleware 签名

    messages = state["messages"]

    # 消息较少时不修剪
    if len(messages) <= 3:
        return None

    # 保留第一条消息，避免太早丢掉“我叫 Bob”这类关键上下文
    first_message = messages[0]

    # 尽量保留完整的一轮对话，避免只截到半轮消息
    recent_messages = messages[-3:] if len(messages) % 2 == 0 else messages[-4:]
    new_messages = [first_message, *recent_messages]

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),  # 删除所有历史记录
            *new_messages,  # 写入新消息
        ]
    }


@after_model
def delete_old_messages(state: AgentState, runtime: Runtime) -> dict | None:
    messages = state['messages']
    #
    if len(messages) > 2:
        print(f"触发移除工具：{messages[:2]}")
        return {
            "messages": [
                RemoveMessage(id=m.id) for m in messages[:2]
            ]
        }
    return None


def trim_messages_demo():
    """演示修剪消息后的记忆效果。"""
    agent = create_agent(
        model=model,
        tools=[],
        middleware=[trim_messages],
        checkpointer=InMemorySaver(),
        system_prompt=(
            "你是一个专业的助手。"
            "如果用户之前说过自己的名字，请根据保留下来的上下文回答。"
        ),
    )

    config: RunnableConfig = {"configurable": {"thread_id": "trim_messages_demo_1"}}

    print("\n========== 第 1 轮 ==========")
    agent.invoke({"messages": "Hi, my name is Bob."}, config)
    print("用户：Hi, my name is Bob.")

    print("\n========== 第 2 轮 ==========")
    agent.invoke({"messages": "Write a short poem about cats."}, config)
    print("用户：Write a short poem about cats.")

    print("\n========== 第 3 轮 ==========")
    agent.invoke({"messages": "Now do the same but for dogs."}, config)
    print("用户：Now do the same but for dogs.")

    print("\n========== 第 4 轮 ==========")
    final_response = agent.invoke({"messages": "What's my name?"}, config)
    inspect(final_response["messages"])


def Remove_messages():
    agent = create_agent(
        model=model,
        middleware=[
            delete_old_messages
        ],
        checkpointer=InMemorySaver()
    )
    config = {"configurable": {"thread_id": '11111'}}
    for event in agent.stream(
            {"messages": [{"role": "user", "content": "hi! I'm bob"}]},
            config,
            stream_mode="values",  # stream_mode="values" 是其中最直观、最常用的模式。它的核心作用是：每当状态（State）发生任何变化时，就返回当前完整的、合并后的所有数据。
    ):
        print([(message.type, message.content) for message in event["messages"]])

    for event in agent.stream(
            {"messages": [{"role": "user", "content": "what's my name?"}]},
            config,
            stream_mode="values",
    ):
        print([(message.type, message.content) for message in event["messages"]])


if __name__ == "__main__":
    # 1,删除所有信息
    # trim_messages_demo()
    # 2.删除指定信息
    Remove_messages()
