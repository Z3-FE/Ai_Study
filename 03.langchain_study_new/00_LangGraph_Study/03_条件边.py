import operator
from pathlib import Path
from typing import Annotated, Literal

from langgraph.errors import GraphRecursionError
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel


class State(BaseModel):
    aggregate: Annotated[list, operator.add]


def a(state: State):
    return {"aggregate": ["A"]}


def b(state: State):
    return {"aggregate": ["B"]}


graph = StateGraph(State)

graph.add_node(a)
graph.add_node(b)


# noinspection PyTypeHints
def route(state: State) -> Literal["b", END]:
    print(state.aggregate)
    if len(state.aggregate) <= 4:
        return "b"
    else:
        return END


graph.add_edge(START, 'a')
graph.add_conditional_edges('a', route)  # 条件边
graph.add_edge('b', 'a')

graph = graph.compile()

try:
    result = graph.invoke({"aggregate": []}, {"recursion_limit": 3})  # 递归限制
    print(result)
except GraphRecursionError:
    print("递归限制超过最大深度")

png = graph.get_graph().draw_mermaid_png()
out = Path("graph.png")
out.write_bytes(png)
print("图已保存为 graph.png")
