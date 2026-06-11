"""LangChain 官方自定义中间件案例：基础篇

资料来源：
1. https://docs.langchain.com/oss/javascript/langchain/middleware/custom
2. https://docs.langchain.com/oss/python/langchain/middleware/custom

这个文件重点覆盖：
1. decorator-based middleware
2. class-based middleware
3. node-style hooks
4. wrap-style hooks
5. 自定义 state schema
6. agent jumps
7. execution order 的代码理解方式
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from typing_extensions import NotRequired

from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import (
    AgentMiddleware,
    ExtendedModelResponse,
    ModelRequest,
    ModelResponse,
    after_agent,
    after_model,
    before_agent,
    before_model,
    dynamic_prompt,
    hook_config,
    wrap_model_call,
    wrap_tool_call,
)
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool
from langchain.tools.tool_node import ToolCallRequest
from langgraph.runtime import Runtime
from langgraph.types import Command
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
def get_weather(city: str) -> str:
    """获取天气。"""
    return f"{city} 今天天气晴朗，温度 26 度。"


@tool
def multiply(a: int, b: int) -> int:
    """两个整数相乘。"""
    return a * b


@tool
def search_docs(query: str) -> str:
    """搜索资料。"""
    return f"搜索完成：{query}"


class CustomState(AgentState):
    """自定义状态。

    作用：
    1. 给 middleware 增加额外状态字段。
    2. 可以让多个 hook 之间共享数据。

    字段：
    1. model_call_count: 记录模型调用次数。
    2. user_id: 记录当前用户。
    3. _internal_trace: 私有字段，不会出现在最终结果里。
    """

    model_call_count: NotRequired[int]
    user_id: NotRequired[str]
    _internal_trace: NotRequired[str]


@before_agent
def log_before_agent(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """before_agent: agent 整次执行开始前运行一次。

    作用：
    1. 适合做日志、参数校验、初始化。
    2. 每次 invoke 只运行一次。
    """
    del runtime
    print(f"[before_agent] 本次执行开始，当前消息数: {len(state['messages'])}")
    return None


@before_model
def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """before_model: 每次模型调用前运行。

    作用：
    1. 适合修剪消息、校验输入、写日志。
    2. 返回 dict 时，会把结果合并进 state。
    """
    del runtime
    print(f"[before_model] 即将调用模型，消息数: {len(state['messages'])}")
    return None


@after_model
def log_after_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """after_model: 每次模型返回后运行。

    作用：
    1. 适合检查输出、统计信息、更新状态。
    """
    del runtime
    last_message = state["messages"][-1]
    print(f"[after_model] 模型返回: {last_message.content}")
    return None


@after_agent
def log_after_agent(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """after_agent: agent 整次执行完成后运行一次。

    作用：
    1. 适合收尾日志、结果汇总。
    """
    del runtime
    print(f"[after_agent] 本次执行结束，最终消息数: {len(state['messages'])}")
    return None


@wrap_model_call
def retry_model_call(
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """wrap_model_call: 包裹模型调用。

    作用：
    1. 适合做重试、fallback、缓存、动态换模型。
    2. 可以决定调用 handler 0 次、1 次或多次。

    参数：
    1. request: 当前模型请求。
    2. handler: 真正执行模型调用的函数。
    """
    for attempt in range(3):
        try:
            return handler(request)
        except Exception as exc:
            if attempt == 2:
                raise
            print(f"[wrap_model_call] 第 {attempt + 1} 次失败，准备重试: {exc}")
    raise RuntimeError("理论上不会走到这里")


@wrap_tool_call
def monitor_tool_call(
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    """wrap_tool_call: 包裹工具调用。

    作用：
    1. 适合监控工具、重试工具、限制工具、统一错误处理。
    2. 能看到工具名和工具参数。
    """
    print(f"[wrap_tool_call] 正在执行工具: {request.tool_call['name']}")
    print(f"[wrap_tool_call] 工具参数: {request.tool_call['args']}")
    result = handler(request)
    print("[wrap_tool_call] 工具执行成功")
    return result


@dynamic_prompt
def build_dynamic_prompt(state: AgentState, runtime: Runtime) -> str:
    """dynamic_prompt: 动态生成 system prompt。

    作用：
    1. 根据当前 state / runtime 动态插入系统提示。
    2. 适合注入用户身份、租户信息、业务上下文。
    """
    del runtime
    user_id = state.get("user_id", "anonymous")
    return f"你是一个专业助手。当前用户ID是 {user_id}。"


@before_model(state_schema=CustomState, can_jump_to=["end"])
def check_call_limit(state: CustomState, runtime: Runtime) -> dict[str, Any] | None:
    """自定义状态 + jump 示例。

    作用：
    1. 读取自定义状态里的计数器。
    2. 超过阈值后直接 jump_to='end' 提前结束。

    参数：
    1. state_schema=CustomState: 指定这个 hook 使用扩展状态。
    2. can_jump_to=['end']: 允许该 hook 直接跳到 end 节点。
    """
    del runtime
    count = state.get("model_call_count", 0)
    if count > 10:
        return {"jump_to": "end"}
    return None


@after_model(state_schema=CustomState)
def increment_counter(state: CustomState, runtime: Runtime) -> dict[str, Any] | None:
    """after_model 更新自定义状态。"""
    del runtime
    return {"model_call_count": state.get("model_call_count", 0) + 1}


@wrap_model_call(state_schema=CustomState)
def track_usage(
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
) -> ExtendedModelResponse:
    """wrap_model_call 返回 ExtendedModelResponse + Command。

    作用：
    1. 在模型调用层更新自定义状态。
    2. 比如记录 token、trace、usage 等。
    """
    response = handler(request)
    return ExtendedModelResponse(
        model_response=response,
        command=Command(update={"_internal_trace": "track_usage_ran"}),
    )


@after_model
@hook_config(can_jump_to=["end"])
def block_specific_output(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """hook_config + jump 示例。

    作用：
    1. 如果模型输出中出现某些关键字，直接提前结束。
    2. 可以在结束前替换掉最终回复。
    """
    del runtime
    last_message = state["messages"][-1]
    if "BLOCKED" in str(last_message.content):
        return {
            "messages": [AIMessage(content="我不能继续响应这个请求。")],
            "jump_to": "end",
        }
    return None


class LoggingMiddleware(AgentMiddleware):
    """class-based middleware 示例。

    作用：
    1. 当你需要把多个 hook 组合在一个类里时更合适。
    2. 也适合需要同步 + 异步双版本的场景。
    """

    def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        del runtime
        print(f"[class.before_model] 当前消息数: {len(state['messages'])}")
        return None

    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        del runtime
        print(f"[class.after_model] 最后一条消息: {state['messages'][-1].content}")
        return None

    async def abefore_model(
            self,
            state: AgentState,
            runtime: Runtime,
    ) -> dict[str, Any] | None:
        del state, runtime
        return None

    async def aafter_model(
            self,
            state: AgentState,
            runtime: Runtime,
    ) -> dict[str, Any] | None:
        del state, runtime
        return None


class DynamicModelMiddleware(AgentMiddleware):
    """class-based wrap_model_call 示例：动态选模型。"""

    def __init__(self, simple_model: ChatOpenAI, complex_model: ChatOpenAI):
        self.simple_model = simple_model
        self.complex_model = complex_model

    def wrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        model_to_use = self.complex_model if len(request.messages) > 10 else self.simple_model
        return handler(request.override(model=model_to_use))


def create_decorator_based_agent():
    """装饰器风格 middleware。

    作用：
    1. 快速、轻量。
    2. 适合单 hook 或少量 hook。
    """
    return create_agent(
        model=model,
        tools=[get_weather, multiply],
        middleware=[
            log_before_agent,
            log_before_model,
            retry_model_call,
            monitor_tool_call,
            log_after_model,
            log_after_agent,
        ],
        system_prompt="你是一个专业助手。",
    )


agent = create_decorator_based_agent()
agent.invoke({"messages": "Hi, my name is Bob."})


def create_class_based_agent():
    """类风格 middleware。"""
    return create_agent(
        model=model,
        tools=[get_weather],
        middleware=[LoggingMiddleware()],
        system_prompt="你是一个专业助手。",
    )


def create_custom_state_agent():
    """自定义状态案例。

    调用时可以传：
    1. model_call_count
    2. user_id
    """
    return create_agent(
        model=model,
        tools=[],
        middleware=[check_call_limit, increment_counter, track_usage],
        system_prompt="你是一个专业助手。",
        state_schema=CustomState,
    )


def create_dynamic_prompt_agent():
    """dynamic_prompt 案例。"""
    return create_agent(
        model=model,
        tools=[get_weather],
        middleware=[build_dynamic_prompt],
    )


def create_execution_order_agent():
    """执行顺序观察案例。

    说明：
    1. before_*: 从前到后执行
    2. wrap_*: 像洋葱一样嵌套
    3. after_*: 从后到前执行
    """
    return create_agent(
        model=model,
        tools=[search_docs],
        middleware=[
            log_before_agent,
            log_before_model,
            monitor_tool_call,
            log_after_model,
            log_after_agent,
        ],
        system_prompt="你是一个专业助手。",
    )


def show_available_examples():
    print("05_Middleware/05_官方自定义中间件_基础.py 包含这些案例：")
    print("1. before_agent / before_model / after_model / after_agent")
    print("2. wrap_model_call / wrap_tool_call")
    print("3. dynamic_prompt")
    print("4. decorator-based middleware")
    print("5. class-based middleware")
    print("6. custom state schema")
    print("7. hook_config + jump_to")
    print("8. execution order 观察案例")


def run_case(case_id: str):
    """根据编号运行指定案例。"""
    if case_id == "1":
        print("\n执行案例 1: before_agent / before_model / after_model / after_agent")
        agent = create_agent(
            model=model,
            tools=[],
            middleware=[log_before_agent, log_before_model, log_after_model, log_after_agent],
            system_prompt="你是一个专业助手，请简单介绍一下人工智能。",
        )
        result = agent.invoke({"messages": [{"role": "user", "content": "请简单介绍一下人工智能。"}]})
        result["messages"][-1].pretty_print()
        return

    if case_id == "2":
        print("\n执行案例 2: wrap_model_call / wrap_tool_call")
        agent = create_agent(
            model=model,
            tools=[get_weather],
            middleware=[retry_model_call, monitor_tool_call],
            system_prompt="你是一个专业助手，优先使用工具。",
        )
        result = agent.invoke({"messages": [{"role": "user", "content": "请使用 get_weather 查询上海天气。"}]})
        result["messages"][-1].pretty_print()
        return

    if case_id == "3":
        print("\n执行案例 3: dynamic_prompt")
        agent = create_dynamic_prompt_agent()
        result = agent.invoke(
            {
                "messages": [{"role": "user", "content": "请查询北京天气。"}],
                "user_id": "user_001",
            }
        )
        result["messages"][-1].pretty_print()
        return

    if case_id == "4":
        print("\n执行案例 4: decorator-based middleware")
        agent = create_decorator_based_agent()
        result = agent.invoke({"messages": [{"role": "user", "content": "请使用 get_weather 查询杭州天气。"}]})
        result["messages"][-1].pretty_print()
        return

    if case_id == "5":
        print("\n执行案例 5: class-based middleware")
        agent = create_class_based_agent()
        result = agent.invoke({"messages": [{"role": "user", "content": "请介绍一下大模型。"}]})
        result["messages"][-1].pretty_print()
        return

    if case_id == "6":
        print("\n执行案例 6: custom state schema")
        agent = create_custom_state_agent()
        result = agent.invoke(
            {
                "messages": [{"role": "user", "content": "请简单解释一下什么是中间件。"}],
                "model_call_count": 0,
                "user_id": "custom_user_1",
            }
        )
        result["messages"][-1].pretty_print()
        return

    if case_id == "7":
        print("\n执行案例 7: hook_config + jump_to")
        agent = create_agent(
            model=model,
            tools=[],
            middleware=[block_specific_output],
            system_prompt="请直接输出 BLOCKED 这个单词。",
        )
        result = agent.invoke({"messages": [{"role": "user", "content": "请按要求输出。"}]})
        result["messages"][-1].pretty_print()
        return

    if case_id == "8":
        print("\n执行案例 8: execution order 观察案例")
        agent = create_execution_order_agent()
        result = agent.invoke({"messages": [{"role": "user", "content": "请使用 search_docs 搜索 LangChain middleware。"}]})
        result["messages"][-1].pretty_print()
        return

    print("无效编号，请输入 1-8。")


if __name__ == "__main__":
    show_available_examples()
    user_input = input("\n请输入要执行的案例编号：").strip()
    run_case(user_input)
