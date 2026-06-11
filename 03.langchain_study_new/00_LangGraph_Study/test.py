from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver, MemorySaver

from langgraph.graph import MessagesState, StateGraph, START, END

from env_utils import MODEL_NAME, API_KEY, BASE_URL

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL
)


def call_model(state: MessagesState, config: RunnableConfig):
    ai_msg = model.invoke(state["messages"])
    return {"messages": [ai_msg]}


group = StateGraph(MessagesState)

group.add_node("llm", call_model)
group.add_edge(START, "llm")
group.add_edge("llm", END)

group = group.compile(checkpointer=MemorySaver(), store=in_memory_store)

group.invoke({"messages": [{"role": "user", "content": "我叫tom，请记住我"}]}, {
    "configurable": {"thread_id": "1"}
})
res1 = group.invoke({"messages": [{"role": "user", "content": "我叫什么"}]}, {
    "configurable": {"thread_id": "1"}
})
res2 = group.invoke({"messages": [{"role": "user", "content": "我叫什么"}]}, {
    "configurable": {"thread_id": "2"}
})

print("回答1:", res1)
print("回答2：", res2)
