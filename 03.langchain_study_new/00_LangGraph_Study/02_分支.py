import operator
from pathlib import Path
from typing import Annotated

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

from IPython.display import display, Image

"""
Annotated 是 Python 的类型注解增强语法：给类型附加“额外元数据”。

例如：
Annotated[list, operator.add]
意思是：
基础类型是 list
额外附加了 operator.add 这个元数据
"""


class State(BaseModel):
    aggregate: Annotated[list, operator.add]


def a(state: State):
    return {"aggregate": ["A"]}


def b(state: State):
    return {"aggregate": ["B"]}


def c(state: State):
    return {"aggregate": ["C"]}


def d(state: State):
    return {"aggregate": ["D"]}


graph = StateGraph(State)

graph.add_node(b)
graph.add_node(c)
graph.add_node(d)
graph.add_node(a)

graph.add_edge(START, "a")
graph.add_edge("a", "b")
graph.add_edge("a", "c")
graph.add_edge("b", "d")
graph.add_edge("c", "d")
graph.add_edge("d", END)
graph = graph.compile()

png = graph.get_graph().draw_mermaid_png()
out = Path("graph.png")
out.write_bytes(png)
print(out.resolve())
res = graph.invoke({"aggregate": []})
print(res)
# graph.invoke({"aggregate": ["A", "B"]})
