""""
访问存储器
"""
from langchain.agents import create_agent, AgentState
from langchain_classic.chains.question_answering.map_reduce_prompt import messages
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import before_model, after_model
from langgraph.runtime import Runtime
from langgraph.types import Command
from rich import inspect

from env_utils import API_KEY, BASE_URL, MODEL_NAME

model = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
)


class CustomAgentState(AgentState):
    user_id: str
    user_name: str


# middleware 用于在模型调用后更新状态
@after_model
def update_use(state: CustomAgentState, runtime: Runtime):
    print(inspect(state))
    if state['user_id'] == "123":
        print('是123用户，更新状态')
        return {
            messages: [
                *state['messages'],
            ]
        }
    else:
        return Command(
            update={
                "user_name": '迪丽热巴',
                "messages": [
                    *state['messages'],
                ]
            }
        )


def update_status():
    """更新状态"""

    agent = create_agent(
        model=model,
        system_prompt="你是一个专业的助手。",
        state_schema=CustomAgentState,  # 自定义会话状态结构
        checkpointer=InMemorySaver(),
        middleware=[update_use]
    )
    messages = agent.invoke(
        {
            "messages": [{"role": "user", "content": "你好"}],
            "user_id": "44444",
            "user_name": "z523"
        },
        config={"configurable": {"thread_id": "postgres_demo_1"}}
    )
    print(messages)


if __name__ == "__main__":
    update_status()
