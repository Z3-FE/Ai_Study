"""PostgreSQL 持久化记忆示例

运行前请先安装：
    uv add langgraph-checkpoint-postgres psycopg[binary]

本例演示：
1. 使用 PostgreSQL 保存会话状态
2. 程序再次运行时，使用相同的 thread_id 继续上次对话

如果你本地已经安装了 PostgreSQL，默认会尝试用当前系统用户连接本地库：
postgresql:///postgres
"""

import os

from langchain.agents import AgentState, create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver

from env_utils import API_KEY, BASE_URL, MODEL_NAME

model = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
)


class CustomAgentState(AgentState):
    user_id: str
    preferences: dict


DB_URI = os.getenv("POSTGRES_URI", "postgresql:///postgres")


def postgres_memory_demo():
    """演示 PostgreSQL 持久化记忆。"""
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        # 第一次运行时创建 checkpoint 相关数据表，后续重复执行也安全
        checkpointer.setup()

        agent = create_agent(
            model=model,
            system_prompt=(
                "你是一个专业的助手。"
                "如果用户说过自己的名字，请优先根据历史消息回答。"
            ),
            state_schema=CustomAgentState,  # 自定义会话状态结构
            checkpointer=checkpointer,
        )

        config = {"configurable": {"thread_id": "postgres_demo_1"}}

        print("\n========== 第一次对话 ==========")
        result_1 = agent.invoke(
            {
                "messages": [
                    {"role": "user", "content": "你好，我叫 Bob。请记住我的名字。"}
                ],
                "user_id": "user_123",
                "preferences": {"theme": "dark"},
            },
            config=config,
        )
        print(result_1["messages"][-1].content)

        print("\n========== 第二次对话 ==========")
        result_2 = agent.invoke(
            {
                "messages": [
                    {"role": "user", "content": "你还记得我叫什么吗？"}
                ],
                "user_id": "user_123",
                "preferences": {"theme": "dark"},
            },
            config=config,
        )
        print(result_2["messages"][-1].content)


if __name__ == "__main__":
    postgres_memory_demo()
