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

app.invoke({"messages": [{"role": "user", "content": "你好，我叫Bob，请记住我名字"}]}, config_1)
r1 = app.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config_1)
r2 = app.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config_2)

print("同线程追问：", r1["messages"][-1].content)
print("新线程追问：", r2["messages"][-1].content)
