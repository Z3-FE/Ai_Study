from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel


class State(BaseModel):
    value1: str
    value2: str | None = None
    value3: str | None = None


def node_1(state: State):
    return {
        "value1": state.value1,
    }


def node_2(state: State):
    return {
        "value2": state.value1 + '第二个节点',
    }


def node_3(state: State):
    return {
        "value3": state.value2 + '第三个节点',
    }


graph = StateGraph(State)

graph.add_node(node_1)
graph.add_node(node_2)
graph.add_node(node_3)

graph.add_edge(START, "node_1")
graph.add_edge("node_1", "node_2")
graph.add_edge("node_2", "node_3")
graph.add_edge("node_3", END)

graph = graph.compile()

result = graph.invoke({"value1": "hello"})
print(result)
