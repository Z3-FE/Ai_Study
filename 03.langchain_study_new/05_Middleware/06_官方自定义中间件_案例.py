"""LangChain 官方自定义中间件案例：实战篇

资料来源：
1. https://docs.langchain.com/oss/javascript/langchain/middleware/custom
2. https://docs.langchain.com/oss/python/langchain/middleware/custom

这个文件重点覆盖官方页面里的 Examples：
1. Dynamic prompt
2. Dynamic model selection
3. Dynamically selecting tools
4. Tool call monitoring
5. Prompt caching (Anthropic)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
    dynamic_prompt,
    wrap_tool_call,
)
from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain.tools.tool_node import ToolCallRequest
from langchain_openai import ChatOpenAI

from env_utils import API_KEY, BASE_URL, MODEL_NAME


model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
)

mini_model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
)


@tool
def calculator(expression: str) -> str:
    """执行简单计算。"""
    return f"计算结果：{expression}"


@tool
def weather(city: str) -> str:
    """获取城市天气。"""
    return f"{city} 当前 26 度，天气晴朗。"


@tool
def search_web(query: str) -> str:
    """搜索网络信息。"""
    return f"已搜索：{query}"


@tool
def query_orders(order_id: str) -> str:
    """查询订单。"""
    return f"订单 {order_id} 状态：已发货。"


@dynamic_prompt
def customer_support_prompt(state: AgentState, runtime) -> str:
    """Dynamic prompt 示例。

    作用：
    1. 根据上下文动态生成 system prompt。
    2. 适合客服、教育、分角色系统。
    """
    del runtime
    if any("退款" in str(msg.content) for msg in state["messages"]):
        return "你是一个谨慎的退款客服，请先核对订单，再解释退款流程。"
    return "你是一个专业客服，请清晰、简洁地回答用户问题。"


class DynamicModelSelectionMiddleware(AgentMiddleware):
    """Dynamic model selection 示例。

    作用：
    1. 根据请求复杂度动态切模型。
    2. 简单请求走便宜模型，复杂请求走强模型。
    """

    def __init__(self, simple_model: ChatOpenAI, complex_model: ChatOpenAI):
        self.simple_model = simple_model
        self.complex_model = complex_model

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        if len(request.messages) > 10:
            return handler(request.override(model=self.complex_model))
        return handler(request.override(model=self.simple_model))


class DynamicToolSelectionMiddleware(AgentMiddleware):
    """Dynamically selecting tools 示例。

    作用：
    1. 根据用户问题动态缩小工具范围。
    2. 让主模型只看到当前最相关的工具。
    """

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        last_user_message = next(
            (
                msg
                for msg in reversed(request.messages)
                if isinstance(msg, HumanMessage)
            ),
            None,
        )

        selected_tools = request.tools
        if last_user_message:
            content = str(last_user_message.content)
            if "天气" in content:
                selected_tools = [tool_ for tool_ in request.tools if tool_.name == "weather"]
            elif "订单" in content:
                selected_tools = [tool_ for tool_ in request.tools if tool_.name == "query_orders"]
            elif "计算" in content:
                selected_tools = [tool_ for tool_ in request.tools if tool_.name == "calculator"]

        return handler(request.override(tools=selected_tools))


@wrap_tool_call
def track_tool_usage(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    """Tool call monitoring 示例。

    作用：
    1. 监控工具调用情况。
    2. 适合日志、审计、计费、性能分析。
    """
    print(f"[tool-monitor] 工具名: {request.tool_call['name']}")
    print(f"[tool-monitor] 参数: {request.tool_call['args']}")
    result = handler(request)
    print(f"[tool-monitor] 返回: {result.content}")
    return result


class AnthropicPromptCachingMiddleware(AgentMiddleware):
    """Prompt caching (Anthropic) 示例。

    作用：
    1. 给 Anthropic 请求增加 cache_control 标记。
    2. 让长系统提示或稳定上下文命中缓存。

    说明：
    1. 这里只是演示官方 custom middleware 思路。
    2. 真正运行时需要 Anthropic 模型与对应 provider 支持。
    """

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        patched_messages = []
        for message in request.messages:
            if isinstance(message, SystemMessage) and isinstance(message.content, str):
                patched_messages.append(
                    SystemMessage(
                        content=[
                            {
                                "type": "text",
                                "text": message.content,
                                "cache_control": {"type": "ephemeral"},
                            }
                        ]
                    )
                )
            else:
                patched_messages.append(message)
        return handler(request.override(messages=patched_messages))


def create_dynamic_prompt_agent():
    """案例 1: Dynamic prompt。"""
    return create_agent(
        model=model,
        tools=[query_orders],
        middleware=[customer_support_prompt],
    )


def create_dynamic_model_selection_agent():
    """案例 2: Dynamic model selection。"""
    return create_agent(
        model=model,
        tools=[weather, calculator],
        middleware=[DynamicModelSelectionMiddleware(mini_model, model)],
        system_prompt="你是一个专业助手。",
    )


def create_dynamic_tool_selection_agent():
    """案例 3: Dynamically selecting tools。"""
    return create_agent(
        model=model,
        tools=[weather, calculator, search_web, query_orders],
        middleware=[DynamicToolSelectionMiddleware()],
        system_prompt="你是一个专业助手，请根据问题选择合适工具。",
    )


def create_tool_monitoring_agent():
    """案例 4: Tool call monitoring。"""
    return create_agent(
        model=model,
        tools=[weather, search_web],
        middleware=[track_tool_usage],
        system_prompt="你是一个专业助手。",
    )


def create_prompt_caching_agent():
    """案例 5: Prompt caching (Anthropic 思路)。"""
    return create_agent(
        model=model,
        tools=[search_web],
        middleware=[AnthropicPromptCachingMiddleware()],
        system_prompt="你是一个专业助手，拥有一段很长且稳定的系统提示。",
    )


def show_available_examples():
    print("05_Middleware/06_官方自定义中间件_案例.py 包含这些案例：")
    print("1. Dynamic prompt")
    print("2. Dynamic model selection")
    print("3. Dynamically selecting tools")
    print("4. Tool call monitoring")
    print("5. Prompt caching (Anthropic 思路)")


def _pretty_print_last_message(result):
    last_message = result["messages"][-1]
    if hasattr(last_message, "pretty_print"):
        last_message.pretty_print()
    else:
        print(last_message)


def run_case(case_id: str):
    """根据编号运行指定案例。"""
    if case_id == "1":
        print("\n执行案例 1: Dynamic prompt")
        agent = create_dynamic_prompt_agent()
        result = agent.invoke({"messages": [{"role": "user", "content": "我的订单要退款，帮我看一下流程。"}]})
        _pretty_print_last_message(result)
        return

    if case_id == "2":
        print("\n执行案例 2: Dynamic model selection")
        agent = create_dynamic_model_selection_agent()
        result = agent.invoke({"messages": [{"role": "user", "content": "请计算 23 * 45。"}]})
        _pretty_print_last_message(result)
        return

    if case_id == "3":
        print("\n执行案例 3: Dynamically selecting tools")
        agent = create_dynamic_tool_selection_agent()
        result = agent.invoke({"messages": [{"role": "user", "content": "请查询订单 A10086 的状态。"}]})
        _pretty_print_last_message(result)
        return

    if case_id == "4":
        print("\n执行案例 4: Tool call monitoring")
        agent = create_tool_monitoring_agent()
        result = agent.invoke({"messages": [{"role": "user", "content": "请使用 weather 工具查询上海天气。"}]})
        _pretty_print_last_message(result)
        return

    if case_id == "5":
        print("\n执行案例 5: Prompt caching (Anthropic 思路)")
        agent = create_prompt_caching_agent()
        result = agent.invoke({"messages": [{"role": "user", "content": "请搜索 LangChain prompt caching。"}]})
        _pretty_print_last_message(result)
        return

    print("无效编号，请输入 1-5。")


if __name__ == "__main__":
    show_available_examples()
    user_input = input("\n请输入要执行的案例编号：").strip()
    run_case(user_input)
