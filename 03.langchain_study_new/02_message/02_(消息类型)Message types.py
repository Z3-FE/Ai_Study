"""消息类型"""
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from env_utils import (
    API_KEY,
    BASE_URL,
    MODEL_NAME
)

model = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
)


def System_message():
    """1.System message (系统消息)"""

    system_msg = SystemMessage(
        "你是一名资深的Python开发人员，在Web框架方面拥有专业知识。始终提供代码示例并解释你的推理过程。你的解释要简洁但详尽。")
    messages = [
        system_msg,
        HumanMessage("我该如何创建一个REST API？")
    ]
    print(model.invoke(messages))


def Human_message():
    """2.Human message (人类信息)"""
    response = model.invoke([
        HumanMessage("什么是机器学习")
    ])
    # 简便写法
    response = model.invoke("What is machine learning?")
    print(response)


def Message_metadata():
    """3. Message metadata (消息元数据)
        作用：对话中有多个用户，用于用户识别
    """
    human_msg = HumanMessage(
        content="我的名字在元数据里，请告诉我我的名字是什么？",
        name="alice",  # 可选：识别不同的用户
        id="msg_123",  # 可选：用于追踪的唯一标识符
    )
    print(model.invoke([human_msg]))


def AI_message():
    """4. AI信息"""
    response = model.invoke("解释人工智能")
    print(type(response))  # <class 'langchain.messages.AIMessage'>

    # 手动创建一个 AI 消息（例如：用于加载之前的对话历史，或者预设模型的回答）
    ai_msg = AIMessage("我很乐意为您解答那个问题！")

    # 构造对话历史列表
    # 这种方式模拟了用户和 AI 之间已经进行过的一段对话
    messages = [
        # 设定系统人设
        SystemMessage("你是一个非常专业的助手"),
        # 用户的第一条消息
        HumanMessage("你能帮我个忙吗？"),
        # 插入手动创建的消息，就像是模型之前亲口说过的一样
        ai_msg,
        # 用户的第二条消息
        HumanMessage("太棒了！请问 2 + 2 等于几？")
    ]

    # 将整段“记忆”发送给模型
    response = model.invoke(messages)

    # 打印模型的最终回答
    print(response)


def Token_usage():
    """5. Token usage (token 使用)"""
    response = model.invoke("Hello!")
    print(response.usage_metadata)


def Streaming_and_chunks():
    """6. 流式传输与区块"""
    res = model.stream('hi!')
    final_message = None
    for chunk in res:
        final_message = chunk if final_message is None else final_message + chunk

    print(final_message.content)


def Tool_message():
    AI_megs = AIMessage(
        content='',
        tool_calls=[
            {
                "name": "get_weather",
                "args": {"location": "San Francisco"},
                "id": "call_123"
            }
        ]
    )
    Tool_megs = ToolMessage(
        content='Sunny, 72°F',
        name="get_weather",
        tool_call_id="call_123"  # 必须id对应 call_123
    )
    
    print(model.invoke([
        HumanMessage("What is the weather in San Francisco?"),
        AI_megs,
        Tool_megs
    ]))


# System_message()
# Human_message()
# Message_metadata()
# AI_message()
# Token_usage()
# Streaming_and_chunks()
Tool_message()
