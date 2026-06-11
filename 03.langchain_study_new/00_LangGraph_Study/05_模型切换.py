from langchain.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, START, END

from env_utils import API_KEY, BASE_URL, MODEL_NAME, MODEL_NAME_36

model1 = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
)

model2 = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME_36,
)

model = {
    "qianwen": model1,
    "qianwen_36": model2,
}


def model_switch(state: MessagesState, config: RunnableConfig):
    print(config["configurable"])
    model_name = config["configurable"]["model"] or 'qianwen'
    llm = model[model_name]
    ai_msg = llm.invoke(state["messages"])
    return {"messages": [ai_msg]}


graph = StateGraph(MessagesState)

graph.add_node(model_switch)

graph.add_edge(START, "model_switch")
graph.add_edge("model_switch", END)

graph = graph.compile()

config: RunnableConfig = {"configurable": {"model": "qianwen_36"}}
res = graph.invoke({"messages": [{"role": "user", "content": "你好,你是什么模型,要具体的模型型号"}]},
                   config)

print(res)

print(res)
