"""短期记忆
    1. inMemorySaver , config: 数据在内存里：程序一关闭，Bob 的名字、之前的聊天记录、thread_id 全都消失了。
    2.  state_schema=CustomAgentState, 自定义状态：user_id 和 preferences 是自定义的，程序一关闭，不会消失。
"""
from langchain.agents import create_agent, AgentState
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from langchain.tools import tool, ToolRuntime
from icecream import ic
from rich import inspect
from env_utils import (
    MODEL_NAME,
    API_KEY,
    BASE_URL
)

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
)


@tool
def get_user_info(name: str, runtime: ToolRuntime):
    """Get the user's information."""
    inspect(runtime, methods=False)
    print(f'当前user_id: {runtime.state['user_id']}, preferences: {runtime.state["preferences"]}')
    print(f"thread_id: {runtime.config.get("configurable", {}).get("thread_id")}")
    return f'当前用户信息为：{name}'


class CustomAgentState(AgentState):
    user_id: str
    preferences: dict


def inMemorySaver_test():
    """数据在内存里：程序一关闭，Bob 的名字、之前的聊天记录、thread_id 全都消失了。"""
    agent = create_agent(
        model=model,
        system_prompt="你是一个专业的助手，能够根据用户的问题提供准确的信息。",
        tools=[get_user_info],
        state_schema=CustomAgentState,
        checkpointer=InMemorySaver()  #
    )
    agent_messages = agent.stream({
        "messages": [
            {"role": "user", "content": "Hi! My name is Bob."},
            {"role": "assistant", "content": "你好，你是 Bob。"},
            {"role": "user", "content": "请告诉我用户的信息"}
        ],
        # 自定义状态
        "user_id": "user_123",
        "preferences": {"theme": "dark"}
    },
        config={'configurable': {'thread_id': '1'}},
    )

    """
        输出一共有3个节点
        1. ai调用工具
        2. 工具执行，返回结果
        3. ai根据工具结果，生成回答
    """

    for index, messages in enumerate(agent_messages):

        print("*" * 50)

        print(f'原始数据{index}----->messages: {messages['model'] if messages.get("model") else messages["tools"]}')
        for node, data in messages.items():
            status = 'ai调用工具' if type(data["messages"][0]) == AIMessage and data["messages"][0].tool_calls else node

            print(
                f'当前节点: {status}, data: {data["messages"][0].content}')


inMemorySaver_test()
