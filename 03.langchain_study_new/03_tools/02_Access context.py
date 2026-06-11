"""访问上下文   这块内容待定，后续再研究LangGraph在操作"""
from langchain.tools import tool, ToolRuntime
from langchain.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.prebuilt import ToolNode
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
def get_last_user_message(runtime: ToolRuntime):
    """Get the most recent message from the user."""
    print(f'当前runtime: {runtime}')
    list(runtime.state['messages'])
    for message in reversed(runtime.state["messages"]):
        if isinstance(message, HumanMessage):
            return message
    return '没找到用户信息'


def state_access_context():
    """短期记忆——state"""
    # 这样模型只要一启动，第一个念头就是：我必须调这个工具
    forced_model = model.bind_tools(
        [get_last_user_message],
        tool_choice="get_last_user_message"  # 显式指定工具名
    )
    agent = create_agent(
        model=forced_model,
        tools=[get_last_user_message],
        system_prompt='你是一个善于使用工具的助手'
    )

    message = [
        {"role": "system", "content": "你是一个乐于助人的助手，负责将汉语翻译成英语"},
        {"role": "user", "content": "翻译：我喜欢编程。"},
        {"role": "assistant", "content": "I love programming."},
        {"role": "user", "content": "翻译：我喜欢构建应用程序。"},
        {"role": "assistant", "content": "I love building applications."},
        {"role": "user", "content": "我最后一句话说了什么？调用 get_last_user_message 工具，进行回答"}
    ]

    # 使用 stream 模式
    for chunk in agent.stream(
            {
                "messages": message
            },
            config={"configurable": {"user_name": "Kaiqiang"}}
    ):
        # 每一轮循环代表一个节点（Node）的执行结果
        for node, value in chunk.items():
            print(f"\n--- 当前执行节点: [{node}] ---")
            if node == "tools":
                # 这里就是工具执行后的输出！
                print("工具节点已完成执行。")
            # 此时你的控制台应该已经跳出了 tool 函数里 print(runtime) 的内容


@tool
def get_message_count(runtime: ToolRuntime) -> str:
    """Get the number of messages in the conversation."""
    messages = runtime.state["messages"]
    return f"There are {len(messages)} messages."


def tool_node():
    """工具节点"""
    tool_nodeData = ToolNode([get_message_count])
    print(tool_nodeData)


state_access_context()
# tool_node()
