"""LangChain 官方内置中间件案例

资料来源：
1. https://docs.langchain.com/oss/javascript/langchain/middleware/built-in
2. https://docs.langchain.com/oss/python/langchain/middleware/built-in

说明：
1. 这个文件整理“通用内置 middleware”，优先对应 Python 项目的 create_agent 写法。
2. 每个函数都返回一个已经配置好的 agent，方便单独学习与复制。
3. 这里主要演示“怎么配 middleware”，不强制在 __main__ 里全部运行。
"""

from __future__ import annotations

import re

from langchain.agents import create_agent
from langchain.agents.middleware import (
    ClearToolUsesEdit,
    ContextEditingMiddleware,
    HumanInTheLoopMiddleware,
    LLMToolEmulator,
    LLMToolSelectorMiddleware,
    ModelCallLimitMiddleware,
    ModelFallbackMiddleware,
    ModelRetryMiddleware,
    PIIMiddleware,
    ShellToolMiddleware,
    SummarizationMiddleware,
    TodoListMiddleware,
    ToolCallLimitMiddleware,
    ToolRetryMiddleware,
    FilesystemFileSearchMiddleware,
    HostExecutionPolicy,
    RedactionRule,
)
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

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
    """获取城市天气。"""
    return f"{city} 今天天气晴朗，温度 26 度。"


@tool
def add_numbers(a: int, b: int) -> int:
    """两个整数相加。"""
    return a + b


@tool
def read_email(email_id: str) -> str:
    """读取邮件。"""
    return f"邮件 {email_id} 的内容：会议改到下午 3 点。"


@tool
def send_email(recipient: str, subject: str, body: str) -> str:
    """发送邮件。"""
    return f"已向 {recipient} 发送主题为 {subject} 的邮件。"


@tool
def search_tool(query: str) -> str:
    """搜索信息。"""
    return f"搜索关键词：{query}，共返回 3 条候选结果。"


@tool
def query_database(sql: str) -> str:
    """执行数据库查询。"""
    return f"执行 SQL：{sql}，返回 2 行数据。"


@tool
def scrape_webpage(url: str) -> str:
    """抓取网页内容。"""
    return f"已抓取网页：{url}"


@tool
def run_tests() -> str:
    """运行测试。"""
    return "测试通过：12 passed"


def create_summarization_agent():
    """1. SummarizationMiddleware: 长对话自动摘要。

    作用：
    1. 当历史消息太多时，自动把旧消息压缩成摘要。
    2. 保留最近上下文，减少 token 消耗。

    参数：
    1. model: 用哪个模型来生成摘要。
    2. trigger=("messages", 6): 当消息数达到 6 条时触发摘要。
    3. keep=("messages", 4): 摘要后保留最近 4 条消息。
    """
    return create_agent(
        model=model,
        tools=[get_weather, add_numbers],
        middleware=[
            SummarizationMiddleware(
                model=mini_model,
                trigger=("messages", 6),
                keep=("messages", 4),
            ),
        ],
        system_prompt="你是一个专业助手，回答问题前请结合对话历史。",
    )


def create_human_in_the_loop_agent():
    """2. HumanInTheLoopMiddleware: 高风险工具需要人工批准。

    作用：
    1. 在工具真正执行前先暂停。
    2. 适合邮件发送、数据库写入、转账等高风险操作。

    参数：
    1. interrupt_on: 配置哪些工具需要人工确认。
    2. allowed_decisions: 人类可做的决定，例如 approve / edit / reject。
    3. checkpointer: 必填，用来在中断后恢复执行状态。
    """
    return create_agent(
        model=model,
        tools=[read_email, send_email],
        checkpointer=InMemorySaver(),
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "send_email": {"allowed_decisions": ["approve", "edit", "reject"]},
                    "read_email": False,
                }
            )
        ],
        system_prompt="你是邮件助手，发送邮件前需要人工批准。",
    )


def create_model_call_limit_agent():
    """3. ModelCallLimitMiddleware: 限制模型调用次数。

    作用：
    1. 防止 agent 死循环反复调用模型。
    2. 控制成本。

    参数：
    1. thread_limit=10: 同一 thread 最多调用 10 次模型。
    2. run_limit=5: 单次运行最多调用 5 次模型。
    3. exit_behavior="end": 超限后直接结束，而不是报错。
    """
    return create_agent(
        model=model,
        tools=[],
        checkpointer=InMemorySaver(),
        middleware=[
            ModelCallLimitMiddleware(
                thread_limit=10,
                run_limit=5,
                exit_behavior="end",
            )
        ],
    )


def create_tool_call_limit_agent():
    """4. ToolCallLimitMiddleware: 全局和单工具限流。

    作用：
    1. 控制工具被调用的频率。
    2. 既可以全局限流，也可以只限制某个工具。

    参数：
    1. tool_name: 指定限制哪个工具；不写就是全局。
    2. thread_limit: 同线程累计可调用多少次。
    3. run_limit: 单次运行可调用多少次。
    4. exit_behavior="error": 超限后直接报错。
    """
    global_limiter = ToolCallLimitMiddleware(thread_limit=20, run_limit=10)
    search_limiter = ToolCallLimitMiddleware(
        tool_name="search_tool",
        thread_limit=5,
        run_limit=3,
    )
    scraper_limiter = ToolCallLimitMiddleware(
        tool_name="scrape_webpage",
        run_limit=2,
        exit_behavior="error",
    )

    return create_agent(
        model=model,
        tools=[search_tool, query_database, scrape_webpage],
        checkpointer=InMemorySaver(),
        middleware=[global_limiter, search_limiter, scraper_limiter],
    )


def create_model_fallback_agent():
    """5. ModelFallbackMiddleware: 主模型失败时回退到备用模型。

    作用：
    1. 主模型调用失败时自动切换到备用模型。
    2. 提高健壮性。

    参数：
    1. mini_model: 备用模型，主模型失败时自动接管。
    """
    return create_agent(
        model=model,
        tools=[],
        middleware=[
            ModelFallbackMiddleware(
                mini_model,
            )
        ],
    )


def create_basic_pii_agent():
    """6. PIIMiddleware: 内置 PII 检测。

    作用：
    1. 自动识别敏感信息。
    2. 对敏感内容做遮盖、删除或阻止。

    参数：
    1. "email": 检测邮箱。
    2. strategy="redact": 直接替换敏感内容。
    3. "credit_card": 检测信用卡号。
    4. strategy="mask": 部分打码。
    5. apply_to_input=True: 对用户输入生效。
    """
    return create_agent(
        model=model,
        tools=[],
        middleware=[
            PIIMiddleware("email", strategy="redact", apply_to_input=True),
            PIIMiddleware("credit_card", strategy="mask", apply_to_input=True),
        ],
    )


def create_custom_pii_agent():
    """7. PIIMiddleware: 自定义 PII 类型。

    作用：
    1. 在官方内置类型之外，自定义自己的敏感信息规则。
    2. 可以用正则，也可以用函数。

    参数：
    1. detector=r"...": 用正则检测 API Key。
    2. detector=re.compile(...): 用编译后的正则检测手机号。
    3. detector=detect_ssn: 用函数检测更复杂的模式。
    4. strategy="block"/"mask"/"hash": 决定如何处理敏感数据。
    """

    def detect_ssn(content: str) -> list[dict[str, str | int]]:
        matches: list[dict[str, str | int]] = []
        pattern = r"\d{3}-\d{2}-\d{4}"
        for match in re.finditer(pattern, content):
            ssn = match.group(0)
            first_three = int(ssn[:3])
            if first_three not in [0, 666] and not (900 <= first_three <= 999):
                matches.append(
                    {
                        "text": ssn,
                        "start": match.start(),
                        "end": match.end(),
                    }
                )
        return matches

    return create_agent(
        model=model,
        tools=[],
        middleware=[
            PIIMiddleware("api_key", detector=r"sk-[a-zA-Z0-9]{32}", strategy="block"),
            PIIMiddleware(
                "phone_number",
                detector=re.compile(r"\+?\d{1,3}[\s.-]?\d{3,4}[\s.-]?\d{4}"),
                strategy="mask",
            ),
            PIIMiddleware("ssn", detector=detect_ssn, strategy="hash"),
        ],
    )


def create_todo_list_agent():
    """8. TodoListMiddleware: 自动给 agent 增加 write_todos 工具。

    作用：
    1. 让 agent 能把复杂任务拆成待办列表。
    2. 适合多步骤任务规划。

    参数：
    1. 这里使用默认配置，直接启用待办能力。
    """
    return create_agent(
        model=model,
        tools=[search_tool, query_database, run_tests],
        middleware=[TodoListMiddleware()],
        system_prompt="你是项目助手，遇到多步骤任务时请合理规划待办。",
    )


def create_llm_tool_selector_agent():
    """9. LLMToolSelectorMiddleware: 先让小模型挑选相关工具。

    作用：
    1. 工具很多时，先筛选最相关的工具给主模型看。
    2. 减少主模型的上下文负担。

    参数：
    1. model=mini_model: 用小模型做工具筛选。
    2. max_tools=3: 最多保留 3 个工具。
    3. always_include=["search_tool"]: 无论如何都保留该工具。
    """
    return create_agent(
        model=model,
        tools=[get_weather, add_numbers, search_tool, query_database, scrape_webpage],
        middleware=[
            LLMToolSelectorMiddleware(
                model=mini_model,
                max_tools=3,
                always_include=["search_tool"],
            )
        ],
    )


def create_tool_retry_agent():
    """10. ToolRetryMiddleware: 工具失败自动重试。

    作用：
    1. 工具偶发失败时自动重试。
    2. 适合网络波动、临时服务异常。

    参数：
    1. max_retries=3: 最多重试 3 次。
    2. backoff_factor=2.0: 指数退避倍数。
    3. initial_delay=1.0: 第一次重试前等待 1 秒。
    """
    return create_agent(
        model=model,
        tools=[search_tool, query_database],
        middleware=[
            ToolRetryMiddleware(
                max_retries=3,
                backoff_factor=2.0,
                initial_delay=1.0,
            )
        ],
    )


def create_model_retry_agent():
    """11. ModelRetryMiddleware: 模型调用失败自动重试。

    作用：
    1. 模型调用失败时自动重试。
    2. 适合短暂的 API 超时或网络异常。

    参数：
    1. max_retries=3: 最多重试 3 次。
    2. backoff_factor=2.0: 指数退避倍数。
    3. initial_delay=1.0: 第一次重试前等待时间。
    """
    return create_agent(
        model=model,
        tools=[search_tool],
        middleware=[
            ModelRetryMiddleware(
                max_retries=3,
                backoff_factor=2.0,
                initial_delay=1.0,
            )
        ],
    )


def create_llm_tool_emulator_agent():
    """12. LLMToolEmulator: 用模型模拟工具执行，适合测试。

    作用：
    1. 不真正调用工具，而是让模型模拟工具结果。
    2. 适合测试流程或演示。

    参数：
    1. 这里使用默认行为，不额外传配置。
    """
    return create_agent(
        model=model,
        tools=[get_weather, send_email, query_database],
        middleware=[
            LLMToolEmulator(),
        ],
    )


def create_context_editing_agent():
    """13. ContextEditingMiddleware: 清理旧工具输出，控制上下文大小。

    作用：
    1. 清理旧工具返回内容，避免上下文无限膨胀。
    2. 适合工具输出很长的场景。

    参数：
    1. edits: 要执行的上下文编辑策略列表。
    2. ClearToolUsesEdit: 清理旧工具使用记录。
    3. trigger=100000: 达到阈值时触发清理。
    4. keep=3: 清理后保留最近 3 条工具使用记录。
    """
    return create_agent(
        model=model,
        tools=[search_tool, query_database],
        middleware=[
            ContextEditingMiddleware(
                edits=[
                    ClearToolUsesEdit(
                        trigger=100000,
                        keep=3,
                    )
                ]
            )
        ],
    )


def create_shell_tool_agent():
    """14. ShellToolMiddleware: 给 agent 一个持久 shell。

    作用：
    1. 让 agent 可以执行 shell 命令。
    2. 适合代码代理、运维代理、调试代理。

    参数：
    1. workspace_root=".": shell 工作目录。
    2. execution_policy=HostExecutionPolicy(): 在宿主机执行命令。
    3. redaction_rules: 对命令输出中的敏感信息做脱敏。
    4. RedactionRule(...): 定义具体脱敏规则。
    """
    return create_agent(
        model=model,
        tools=[],
        middleware=[
            ShellToolMiddleware(
                workspace_root=".",
                execution_policy=HostExecutionPolicy(),
                redaction_rules=[
                    RedactionRule(pii_type="api_key", detector=r"sk-[a-zA-Z0-9]{32}")
                ],
            )
        ],
    )


def create_filesystem_file_search_agent():
    """15. FilesystemFileSearchMiddleware: 增加 glob_search / grep_search。

    作用：
    1. 给 agent 文件搜索能力。
    2. 适合代码库检索、日志检索、本地文档检索。

    参数：
    1. root_path=".": 搜索根目录。
    2. use_ripgrep=True: 优先使用 rg 加速搜索。
    3. max_file_size_mb=10: 超过 10MB 的文件不搜索。
    """
    return create_agent(
        model=model,
        tools=[],
        middleware=[
            FilesystemFileSearchMiddleware(
                root_path=".",
                use_ripgrep=True,
                max_file_size_mb=10,
            )
        ],
    )


def show_available_examples():
    """打印本文件包含的案例。"""
    print("05_Middleware/02_官方内置中间件_通用.py 包含这些案例：")
    print("1. SummarizationMiddleware")
    print("2. HumanInTheLoopMiddleware")
    print("3. ModelCallLimitMiddleware")
    print("4. ToolCallLimitMiddleware")
    print("5. ModelFallbackMiddleware")
    print("6. PIIMiddleware")
    print("7. 自定义 PIIMiddleware")
    print("8. TodoListMiddleware")
    print("9. LLMToolSelectorMiddleware")
    print("10. ToolRetryMiddleware")
    print("11. ModelRetryMiddleware")
    print("12. LLMToolEmulator")
    print("13. ContextEditingMiddleware")
    print("14. ShellToolMiddleware")
    print("15. FilesystemFileSearchMiddleware")


def _pretty_print_last_message(result):
    last_message = result["messages"][-1]
    if hasattr(last_message, "pretty_print"):
        last_message.pretty_print()
    else:
        print(last_message)


def _run_safely(case_name: str, fn):
    print(f"\n执行案例: {case_name}")
    try:
        fn()
    except Exception as exc:
        print(f"[运行失败] {type(exc).__name__}: {exc}")


def run_case(case_id: str):
    """根据编号运行指定案例。"""

    if case_id == "1":
        def _case():
            agent = create_summarization_agent()
            agent.invoke({"messages": [{"role": "user", "content": "我叫 Bob。"}]})
            agent.invoke({"messages": [{"role": "user", "content": "请记住我的名字。"}]})
            agent.invoke({"messages": [{"role": "user", "content": "写一首关于猫的小诗。"}]})
            result = agent.invoke({"messages": [{"role": "user", "content": "我叫什么？"}]})
            _pretty_print_last_message(result)
        return _run_safely("SummarizationMiddleware", _case)

    if case_id == "2":
        def _case():
            agent = create_human_in_the_loop_agent()
            result = agent.invoke(
                {"messages": [{"role": "user", "content": "请发送一封邮件给 test@example.com，主题是会议通知，正文是下午三点开会。"}]},
                config={"configurable": {"thread_id": "hitl_demo_1"}},
            )
            print(result)
        return _run_safely("HumanInTheLoopMiddleware", _case)

    if case_id == "3":
        def _case():
            agent = create_model_call_limit_agent()
            result = agent.invoke(
                {"messages": [{"role": "user", "content": "请简单解释一下什么是 AI。"}]},
                config={"configurable": {"thread_id": "model_limit_demo_1"}},
            )
            _pretty_print_last_message(result)
        return _run_safely("ModelCallLimitMiddleware", _case)

    if case_id == "4":
        def _case():
            agent = create_tool_call_limit_agent()
            result = agent.invoke(
                {"messages": [{"role": "user", "content": "请使用 search_tool 搜索 LangChain。"}]},
                config={"configurable": {"thread_id": "tool_limit_demo_1"}},
            )
            _pretty_print_last_message(result)
        return _run_safely("ToolCallLimitMiddleware", _case)

    if case_id == "5":
        def _case():
            agent = create_model_fallback_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": "请介绍一下 middleware。"}]})
            _pretty_print_last_message(result)
        return _run_safely("ModelFallbackMiddleware", _case)

    if case_id == "6":
        def _case():
            agent = create_basic_pii_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": "我的邮箱是 bob@example.com，信用卡是 4242 4242 4242 4242。"}]})
            _pretty_print_last_message(result)
        return _run_safely("PIIMiddleware(内置)", _case)

    if case_id == "7":
        def _case():
            agent = create_custom_pii_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": "我的 API key 是 sk-1234567890abcdefghijklmnopqrstuvwxyz，手机号是 +86 13800138000。"}]})
            _pretty_print_last_message(result)
        return _run_safely("PIIMiddleware(自定义)", _case)

    if case_id == "8":
        def _case():
            agent = create_todo_list_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": "请帮我规划一个调研、编码、测试三步任务。"}]})
            _pretty_print_last_message(result)
        return _run_safely("TodoListMiddleware", _case)

    if case_id == "9":
        def _case():
            agent = create_llm_tool_selector_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": "请搜索 LangChain middleware 的资料。"}]})
            _pretty_print_last_message(result)
        return _run_safely("LLMToolSelectorMiddleware", _case)

    if case_id == "10":
        def _case():
            agent = create_tool_retry_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": "请搜索 Python retry middleware。"}]})
            _pretty_print_last_message(result)
        return _run_safely("ToolRetryMiddleware", _case)

    if case_id == "11":
        def _case():
            agent = create_model_retry_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": "请简单解释一下模型重试。"}]})
            _pretty_print_last_message(result)
        return _run_safely("ModelRetryMiddleware", _case)

    if case_id == "12":
        def _case():
            agent = create_llm_tool_emulator_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": "请查询北京天气。"}]})
            _pretty_print_last_message(result)
        return _run_safely("LLMToolEmulator", _case)

    if case_id == "13":
        def _case():
            agent = create_context_editing_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": "请搜索并总结 LangChain middleware。"}]})
            _pretty_print_last_message(result)
        return _run_safely("ContextEditingMiddleware", _case)

    if case_id == "14":
        def _case():
            agent = create_shell_tool_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": "请使用 shell 查看当前目录下有哪些 Python 文件。"}]})
            _pretty_print_last_message(result)
        return _run_safely("ShellToolMiddleware", _case)

    if case_id == "15":
        def _case():
            agent = create_filesystem_file_search_agent()
            result = agent.invoke({"messages": [{"role": "user", "content": "请搜索项目里所有包含 middleware 的 Python 文件。"}]})
            _pretty_print_last_message(result)
        return _run_safely("FilesystemFileSearchMiddleware", _case)

    print("无效编号，请输入 1-15。")


if __name__ == "__main__":
    show_available_examples()
    user_input = input("\n请输入要执行的案例编号：").strip()
    run_case(user_input)
