"""LangGraph backend aligned with assistant-ui langgraph template.

This file mirrors the template expectation:
1. Export a compiled graph as `graph`
2. Use a single messages state graph
3. Keep streaming enabled on the model
"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph


load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")


model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    streaming=True,
)


def call_model(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}


graph = (
    StateGraph(MessagesState)
    .add_node("agent", call_model)
    .add_edge(START, "agent")
    .add_edge("agent", END)
    .compile()
)
