"""custom streaming 示例：搜索工具

这个例子演示：
1. tool 如何通过 custom stream 给用户实时反馈
2. custom 适合展示“工具正在做什么”
3. custom + messages 可以同时看到过程提示和最终回答

仔细看输出的类型：【custom】是手动写入的
"""

import time

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer

from env_utils import MODEL_NAME, API_KEY, BASE_URL

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
)


@tool
def search_docs(keyword: str) -> str:
    """模拟搜索资料库并返回搜索结果。"""
    writer = get_stream_writer()  # 自定义 custom stream 写入器

    writer("开始搜索资料库...")
    time.sleep(0.5)

    writer(f"收到搜索关键词: {keyword}")
    time.sleep(0.5)

    writer("正在匹配相关文章...")
    time.sleep(0.5)

    docs = [
        "人工智能是研究如何让机器模拟人类智能的技术。",
        "机器学习是人工智能的重要分支，核心是让机器从数据中学习规律。",
        "深度学习通过多层神经网络处理复杂任务，例如图像识别和自然语言处理。",
    ]

    writer(f"搜索完成，共找到 {len(docs)} 条候选结果")
    time.sleep(0.5)

    return "\n".join(docs)


def run_custom_demo():
    """只看 custom 事件。"""
    print("\n========== custom 模式 ==========")

    agent = create_agent(
        model=model,
        tools=[search_docs],
        system_prompt="你是一个专业的助手，请优先使用工具回答问题。",
    )

    for chunk in agent.stream(
            {"messages": [{"role": "user", "content": "请使用 search_docs 工具搜索人工智能的基础知识"}]},
            stream_mode="custom",
    ):
        print(chunk)


def run_custom_and_messages_demo():
    """同时看 custom 事件和模型输出。"""
    print("\n========== custom + messages 模式 ==========")

    agent = create_agent(
        model=model,
        tools=[search_docs],
        system_prompt="你是一个专业的助手，请优先使用工具回答问题。",
    )

    for chunk in agent.stream(
            {"messages": [
                {"role": "user", "content": "请使用 search_docs 工具搜索人工智能的基础知识，并整理成一段简短介绍"}]},
            stream_mode=["custom", "messages"],
    ):
        mode, data = chunk
        print(f"[{mode}] {data}")


if __name__ == "__main__":
    # run_custom_demo()
    run_custom_and_messages_demo()
