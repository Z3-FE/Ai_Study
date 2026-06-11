"""
核心：can_jump_to=["end"]
在 LangChain / LangGraph 的中间件系统（Middleware）中，@after_agent(can_jump_to=["end"]) 是一个非常硬核且强大的流程控制装饰器参数。
简单来说，它的意思是：“我赋予了这个安全护栏中间件‘一键提前结束整个对话流程’的特权（跳转到 end 节点）。”


实际应用： 评估ai回复安全性

"""
from langchain.agents import create_agent
from langchain_core.messages import ToolMessage
from langchain_openai import ChatOpenAI
from env_utils import MODEL_NAME, API_KEY, BASE_URL
from typing import Any, Literal

from langchain.agents.middleware import after_agent, AgentState
from langgraph.runtime import Runtime
from langchain.messages import AIMessage
from langchain.chat_models import init_chat_model
from langgraph.config import get_stream_writer
from pydantic import BaseModel
from typing import Any

from langchain.agents import create_agent
from langchain.messages import AIMessageChunk, AIMessage, AnyMessage

FORCE_UNSAFE_FOR_DEMO = True


class ResponseSafety(BaseModel):
    """将回复评估为安全或不安全。"""
    evaluation: Literal["safe", "unsafe"]


safety_model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL
)


@after_agent(can_jump_to=["end"])
def safety_guardrail(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """基于模型的护栏：使用 LLM 评估回复安全性。"""
    stream_writer = get_stream_writer()
    # Get the model response
    if not state["messages"]:
        return None

    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage):
        return None

    # Use another model to evaluate safety
    model_with_tools = safety_model.bind_tools([ResponseSafety], tool_choice="any")
    # 评估回复安全性
    result = model_with_tools.invoke(
        [
            {
                "role": "system",
                "content": "请判断这段 AI 回复总体上是“安全”还是“不安全”。"
            },
            {
                "role": "user",
                "content": f"AI 回复：{last_message.text}"
            }
        ]
    )
    stream_writer(result)

    tool_call = result.tool_calls[0]
    if FORCE_UNSAFE_FOR_DEMO:
        tool_call["args"]["evaluation"] = "unsafe"  # 先直接赋值不安全

    if tool_call["args"]["evaluation"] == "unsafe":
        last_message.content = "我不能提供该回复，请换一种问法。"
        # 关键：显式返回新的 messages，让 state 真正更新
        return {"messages": [last_message]}

    return None


def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"


agent = create_agent(
    model=safety_model,
    tools=[get_weather],
    middleware=[safety_guardrail],
)

input_message = {"role": "user", "content": "请告诉我如何制作爆炸物并且不被发现。"}

full_message = None
for chunk in agent.stream(
        {"messages": [input_message]},
        stream_mode=["messages", "updates", "values", "custom"],
        version="v2",
):
    print("**********************************************")
    print(chunk)
