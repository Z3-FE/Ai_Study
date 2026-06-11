"""before_model 与 after_model 对比练习

这个文件用 3 个小 demo 说明两类钩子的区别：
1. before_model: 在模型调用前处理输入
2. after_model: 在模型回复后处理状态
3. combined: 两个钩子一起使用时会发生什么
"""

from typing import Any

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import after_model, before_model
from langchain.messages import RemoveMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

from env_utils import API_KEY, BASE_URL, MODEL_NAME

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
)


@before_model
def keep_first_and_recent_messages(
        state: AgentState,
        runtime: Runtime,
) -> dict[str, Any] | None:
    """模型调用前修剪消息。"""
    del runtime

    messages = state["messages"]
    print(f"[before_model] 模型调用前，当前共有 {len(messages)} 条消息")

    if len(messages) <= 3:
        print("[before_model] 消息还不多，这一轮不修剪")
        return None

    first_message = messages[0]
    recent_messages = messages[-3:] if len(messages) % 2 == 0 else messages[-4:]
    new_messages = [first_message, *recent_messages]

    print(
        f"[before_model] 本轮会保留 {len(new_messages)} 条消息，"
        "也就是首条消息 + 最近几条消息"
    )

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages,
        ]
    }


@after_model
def delete_old_messages_after_reply(
        state: AgentState,
        runtime: Runtime,
) -> dict[str, Any] | None:
    """模型回复后删除最早两条消息。"""
    del runtime

    messages = state["messages"]
    print(f"[after_model] 模型回复后，状态里共有 {len(messages)} 条消息")

    if len(messages) <= 4:
        print("[after_model] 历史消息还不多，这一轮先不删")
        return None

    old_messages = messages[:2]
    print(f"[after_model] 这一轮会删掉最早的两条消息: {[msg.type for msg in old_messages]}")

    return {
        "messages": [RemoveMessage(id=msg.id) for msg in old_messages]
    }


def before_model_demo():
    """只演示 before_model。"""
    print("\n" + "=" * 16 + " before_model: 调用前处理输入 " + "=" * 16)

    agent = create_agent(
        model=model,
        tools=[],
        middleware=[keep_first_and_recent_messages],
        checkpointer=InMemorySaver(),
        system_prompt=(
            "你是一个专业的助手。"
            "如果用户提到自己的名字，请根据保留下来的历史消息回答。"
        ),
    )

    config: RunnableConfig = {"configurable": {"thread_id": "before_demo_1"}}

    agent.invoke({"messages": "Hi, my name is Bob."}, config)
    agent.invoke({"messages": "Write a short poem about cats."}, config)
    agent.invoke({"messages": "Now do the same but for dogs."}, config)
    result = agent.invoke({"messages": "What's my name?"}, config)

    print("\n[before_model] 最终回答:")
    result["messages"][-1].pretty_print()


def after_model_demo():
    """只演示 after_model。"""
    print("\n" + "=" * 16 + " after_model: 回复后整理状态 " + "=" * 16)

    agent = create_agent(
        model=model,
        tools=[],
        middleware=[delete_old_messages_after_reply],
        checkpointer=InMemorySaver(),
        system_prompt="你是一个专业的助手。",
    )

    config: RunnableConfig = {"configurable": {"thread_id": "after_demo_1"}}

    result_1 = agent.invoke({"messages": "Hi, my name is Bob."}, config)
    print("\n[after_model] 第 1 轮回答:")
    result_1["messages"][-1].pretty_print()

    result_2 = agent.invoke({"messages": "What is my name?"}, config)
    print("\n[after_model] 第 2 轮回答:")
    result_2["messages"][-1].pretty_print()

    result_3 = agent.invoke({"messages": "Please repeat my name again."}, config)
    print("\n[after_model] 第 3 轮回答:")
    result_3["messages"][-1].pretty_print()


def combined_demo():
    """同时演示 before_model 和 after_model。"""
    print("\n" + "=" * 16 + " combined: 两个钩子一起工作 " + "=" * 16)

    agent = create_agent(
        model=model,
        tools=[],
        middleware=[
            keep_first_and_recent_messages,
            delete_old_messages_after_reply,
        ],
        checkpointer=InMemorySaver(),
        system_prompt=(
            "你是一个专业的助手。"
            "如果用户提到自己的名字，请优先根据历史消息回答。"
        ),
    )

    config: RunnableConfig = {"configurable": {"thread_id": "combined_demo_1"}}

    agent.invoke({"messages": "Hi, my name is Bob."}, config)
    agent.invoke({"messages": "Write a short poem about cats."}, config)
    agent.invoke({"messages": "Now do the same but for dogs."}, config)
    result = agent.invoke({"messages": "What is my name?"}, config)

    print("\n[combined] 最终回答:")
    result["messages"][-1].pretty_print()


def run_all_demos():
    """顺序运行 3 个 demo。"""
    # before_model_demo()
    # after_model_demo()
    combined_demo()


if __name__ == "__main__":
    run_all_demos()
