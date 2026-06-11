"""
这种并行最常见在“可拆分、彼此独立”的任务里：

文本批处理：分段摘要、分段抽取、分段分类
检索增强：多个查询并发检索，再汇总
多工具并发：同时查天气、汇率、库存，再合并回复
评估与打分：同一输入走多种规则/模型并行评估
大任务分片：先 map 并行处理，再 reduce 汇总结果
一句话：凡是“先拆分、后合并”的流程，都很适合这种并行模式。
"""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


class State(TypedDict):
    texts: list[str]
    tasks: Annotated[list[dict[str, int]], operator.add]
    total_words: int
    total_chars: int


def map_router(state: State):
    """把 texts 拆成多个并行任务。"""
    return [Send("map_count", {"text": text}) for text in state["texts"]]


def map_count(state: dict):
    """Map: 统计单段文本。"""
    text = state["text"]
    words = len(text.split())  # 单词数量
    chars = len(text)  # 字符数量
    return {"tasks": [{"words": words, "chars": chars}]}


def reduce_counts(state: State):
    """Reduce: 汇总所有 map 结果。"""

    total_words = sum(item["words"] for item in state["tasks"])
    total_chars = sum(item["chars"] for item in state["tasks"])
    return {"total_words": total_words, "total_chars": total_chars}


graph = StateGraph(State)
graph.add_node("map_count", map_count)
graph.add_node("reduce_counts", reduce_counts)

graph.add_conditional_edges(START, map_router, )
graph.add_edge("map_count", "reduce_counts")
graph.add_edge("reduce_counts", END)

app = graph.compile()

result = app.invoke(
    {
        "texts": [
            "LangGraph is great for workflows",
            "Map reduce is useful for parallel tasks",
            "Python makes examples concise",
        ],
        "tasks": [],
    }
)

print("并行 map 结果：", result["tasks"])
print("reduce 汇总：", {"total_words": result["total_words"], "total_chars": result["total_chars"]})
