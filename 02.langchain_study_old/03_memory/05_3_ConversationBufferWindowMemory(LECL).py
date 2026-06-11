import os
from typing import Dict, List
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig, RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.callbacks.stdout import StdOutCallbackHandler
from langchain_core.globals import set_debug

from langchain_study.env_utils import MODEL_NAME, TEMPERATURE

# ⚠️ 替换为你实际的配置变量或直接设置
# 假设 API_KEY, BASE_URL 等已定义
# 示例配置：
API_KEY = os.environ.get("API_KEY", "YOUR_API_KEY")
BASE_URL = os.environ.get("BASE_URL", "https://api.deepseek.com/v1")
MODEL_NAME = "deepseek-chat"

# --- 配置 LLM ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
)
print(f"✅ 模型 '{llm.model_name}' 初始化成功。")
print("-" * 50)

# --- 窗口大小 K ---
WINDOW_SIZE = 3
print(f"✅ 窗口大小 K={WINDOW_SIZE} (只保留最近 {WINDOW_SIZE} 轮对话)")

# 1. 历史记录存储后端 (InMemoryChatMessageHistory)
session_store: Dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """返回或创建一个 InMemoryChatMessageHistory 实例。"""
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()
    return session_store[session_id]


# 2. 核心：历史格式化和截断函数
def format_history_for_prompt(history: List[BaseMessage]) -> str:
    """
    接收完整的消息列表，并只返回最近 K 轮的消息给 Prompt。
    """
    # 截断逻辑：只取列表末尾的 2 * K 条消息
    trimmed_messages = history[-(WINDOW_SIZE * 2):]

    # 将截断后的消息列表格式化为字符串（供 Prompt 模板使用）
    formatted_history = ""
    for msg in trimmed_messages:
        # 格式化消息类型和内容
        if isinstance(msg, HumanMessage):
            formatted_history += f"Human: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            formatted_history += f"AI: {msg.content}\n"

    return formatted_history


print("✅ 历史截断函数 (format_history_for_prompt) 定义完成。")
print("-" * 50)

# 3. 定义 LCEL Prompt
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", f"你是一个善于交谈的助手，但只能记住最近 {WINDOW_SIZE} 轮对话。请基于提供的历史和当前问题回复。"),
        # 使用 history 键接收截断后的 K 轮历史字符串,
        ("human", "{03_embeddings}"),
    ]
)

# 4. 构造核心 LCEL 管道 (Base Chain)
# Base Chain 负责处理数据流和调用 LLM
base_chain = (
    # 步骤 1: 使用 RunnablePassthrough.assign 注入截断后的历史
        RunnablePassthrough.assign(
            # 从 "history" 键读取完整历史 (由 RWMH 注入)，并写入 "history" 键
            history=lambda x: format_history_for_prompt(x["history"])
        )
        # 步骤 2: Prompt -> LLM -> Parser
        | prompt
        | llm
        | StrOutputParser()
)

# 5. 封装为带历史记录的 Runnable
# RunnableWithMessageHistory 负责加载完整的历史到 "messages" 键，并在调用后保存
chain_with_history = RunnableWithMessageHistory(
    runnable=base_chain,
    get_session_history=get_session_history,
    input_messages_key="03_embeddings",  # 用户输入键名
    history_messages_key="history",  # 完整的历史消息将被注入到 "messages" 键下
)

# --- 开启 Verbose 模式进行调试 ---
# 使用 set_debug(True) 可以打印出详细的 Chain 执行过程，包括 Prompt 格式化结果
set_debug(True)

print("✅ RunnableWithMessageHistory 封装完成，已开启 Verbose 模式。")
print("-" * 50)


# --- 运行测试会话 ---

def run_window_test(session_id: str):
    """运行一个 K=3 的窗口记忆测试，以验证忘记机制"""
    print(f"\n--- 正在启动会话: {session_id} (K={WINDOW_SIZE}) ---")

    config: RunnableConfig = {"configurable": {"session_id": session_id}}

    # 轮次 1：引入记忆 (H1, A1) - 目标是忘记这个信息
    query_1 = "我的秘密数字是 99。记住它。"
    print(f"[用户 1]: {query_1}")
    response = chain_with_history.invoke({"03_embeddings": query_1}, config=config)
    print("历史记录:", get_session_history(session_id))

    # 轮次 2：正常记忆 (H2, A2)
    query_2 = "我来自哪里？ (我还没说)"
    print(f"[用户 2]: {query_2}")
    chain_with_history.invoke({"03_embeddings": query_2}, config=config)
    print("历史记录:", get_session_history(session_id))

    # 轮次 3：正常记忆 (H3, A3)
    query_3 = "我最喜欢的颜色是蓝色。"
    print(f"[用户 3]: {query_3}")
    chain_with_history.invoke({"03_embeddings": query_3}, config=config)
    print("历史记录:", get_session_history(session_id))

    # 检查点 A：当前 03_memory 存储了 H1,A1,H2,A2,H3,A3 (6条)
    print(f"\n[检查点 A] 存储消息总数 (完整): {len(get_session_history(session_id).messages)}")
    print("-" * 50)

    # 轮次 4：触发窗口滑动 (H4, A4)
    # H1/A1 应该被挤出 Prompt，AI 应该无法回答秘密数字
    query_4 = "请问我在第一轮说的秘密数字是多少？"
    print(f"[用户 4]: {query_4}")
    response_4 = chain_with_history.invoke({"03_embeddings": query_4}, config=config)
    print(f"[AI 助手 4]: {response_4}\n")
    print("历史记录:", get_session_history(session_id))

    # 轮次 5：确认彻底忘记 (H5, A5)
    # H2/A2 也被挤出 Prompt
    query_5 = "我们上次提到最喜欢的颜色是什么？"
    response_5 = chain_with_history.invoke({"03_embeddings": query_5}, config=config)
    print(f"[AI 助手 5]: {response_5}\n")
    print("历史记录:", get_session_history(session_id))

    # 轮次 6：最终验证 H1 (99) 是否被忘记
    print("\n--- 轮次 6：验证 H1 彻底忘记 (99) ---")
    query_6 = "请问我最开始说的那个秘密数字是多少？"
    print(f"[用户 6]: {query_6}")
    response_6 = chain_with_history.invoke({"03_embeddings": query_6}, config=config)
    print(f"[AI 助手 6]: {response_6}\n")
    # 预期结果：AI 应该回答不知道/找不到记录。


# 运行测试
run_window_test("lc_window_test_001")
