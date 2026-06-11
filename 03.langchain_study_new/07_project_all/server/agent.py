"""Frontend 章节对应的最小后端案例

这个例子先实现官方 Frontend Overview 里的后端部分：
1. 使用 create_agent 创建 agent
2. 使用一个简单 tool
3. 使用 InMemorySaver 保存会话状态
4. 演示 invoke 和 stream

后面如果接 React / Vue 前端，核心就是把这个 agent 暴露成流式接口，
再由 useStream 去消费。
"""

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

try:
    from .env_utils import API_KEY, BASE_URL, MODEL_NAME
except ImportError:
    from env_utils import API_KEY, BASE_URL, MODEL_NAME


model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
)


@tool
def get_weather(city: str) -> str:
    """获取城市天气。"""
    weather_map = {
        "北京": "晴，25 度",
        "上海": "多云，27 度",
        "杭州": "小雨，24 度",
    }
    return f"{city} 的天气是：{weather_map.get(city, '未知，但体感应该还不错')}"


agent = create_agent(
    model=model,
    tools=[get_weather],
    checkpointer=InMemorySaver(),
    system_prompt="你是一个专业助手，能在需要时调用天气工具。",
)


def invoke_demo():
    """最简单的一次性调用。"""
    print("\n========== invoke 示例 ==========")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "请查询北京天气"}]},
        config={"configurable": {"thread_id": "frontend_demo_1"}},
    )
    result["messages"][-1].pretty_print()


def stream_demo():
    """流式输出示例。"""
    print("\n========== stream 示例 ==========")
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": "请查询上海天气，并简单解释今天适不适合出门"}]},
        config={"configurable": {"thread_id": "frontend_demo_2"}},
        stream_mode="messages",
    ):
        print(chunk)


if __name__ == "__main__":
    invoke_demo()
    stream_demo()
