"""动态创建测试词
    1.@dynamic_prompt
    2.采用中间件
"""
from typing import TypedDict

from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain_openai import ChatOpenAI
from env_utils import API_KEY, BASE_URL, MODEL_NAME

model = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
)


class CustomContext(TypedDict):
    user_name: str


@dynamic_prompt
def dynamic_prompt(request: ModelRequest) -> str:
    """根据用户偏好动态创建提示词"""
    print(request)  # 获取不到configurable
    name = request.runtime.context["user_name"]
    return f"你好，{name}！"


agent = create_agent(
    model,
    middleware=[dynamic_prompt],
    context_schema=CustomContext,  # 自定义上下文结构
)
result = agent.invoke({"message": "你好", "user_name": "张三"},
                      context=CustomContext(user_name="李四"),
                      config={"configurable": {"thread_id": "dynamic_prompt_demo"}})

# for msg in result["messages"]:
#     msg.pretty_print()
