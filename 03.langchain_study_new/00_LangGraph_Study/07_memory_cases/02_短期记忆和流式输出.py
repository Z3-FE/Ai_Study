"""
短期记忆是“线程内状态记忆”，
存在 state + checkpointer 里，跟着同一个 thread_id 走。
它适合保存当前会话上下文（消息、工具结果、流程中间态），会在多轮对话中延续，但通常是会话级。
"""

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import MessagesState, START, StateGraph, END

from env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE

model = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
    temperature=TEMPERATURE,
)


def call_model(state: MessagesState):
    """把当前线程历史 messages 交给模型。"""
    ai_msg = model.invoke(state["messages"])
    return {"messages": [ai_msg]}


builder = StateGraph(MessagesState)
builder.add_node("llm", call_model)
builder.add_edge(START, "llm")
builder.add_edge("llm", END)

app = builder.compile(checkpointer=InMemorySaver())  #

config_1 = {"configurable": {"thread_id": "1"}}
config_2 = {"configurable": {"thread_id": "2"}}


def consume_and_collect(stream_iter):
    text = ""
    for chunk, _metadata in stream_iter:
        if chunk.content:
            text += chunk.content
    return text


# 第1轮：必须完整消费，checkpoint 才会写入
first_answer = consume_and_collect(
    app.stream(
        {"messages": [HumanMessage(content="你好，我叫Bob，请记住我名字")]},
        config_1,
        stream_mode="messages",
    )
)

r1 = consume_and_collect(
    app.stream(
        {"messages": [HumanMessage(content="我叫什么名字？今天是几号？")]},
        config_1,
        stream_mode="messages",
    )
)
r2 = consume_and_collect(
    app.stream(
        {"messages": [HumanMessage(content="我叫什么名字？")]},
        config_2,
        stream_mode="messages",
    )
)

print("第1轮(thread_id=1):", first_answer)
print("第2轮(thread_id=1):", r1)
print("第3轮(thread_id=2):", r2)
