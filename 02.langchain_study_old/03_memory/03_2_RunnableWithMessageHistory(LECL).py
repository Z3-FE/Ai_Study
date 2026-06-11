import os
from typing import Dict

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser

# 导入 DeepSeek 配置
from langchain_study.env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE

# --- 配置 LLM ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
)
print(f"✅ 模型 '{llm.model_name}' 初始化成功。")
print("-" * 50)

# 1. 历史记录存储后端 (模拟数据库/缓存)
# 使用一个字典来存储不同 session_id 对应的 InMemoryChatMessageHistory 实例
session_store: Dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """
    一个工厂函数，根据 session_id 返回或创建一个 InMemoryChatMessageHistory 实例。
    这是 RunnableWithMessageHistory 要求的接口。
    """
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()
    return session_store[session_id]


print("✅ 历史记录存储函数 (get_session_history) 定义完成。")

# 2. 定义基本 Chain
# 这是不带记忆的核心逻辑：Prompt -> LLM -> Parser
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个善于交谈的助手，请基于提供的上下文和历史记录进行回复。"),
        # 占位符 {history} 会被 RunnableWithMessageHistory 自动注入历史消息
        ("placeholder", "{history}"),
        ("human", "{03_embeddings}"),
    ]
)

# 使用 LCEL 管道构建核心 Chain
base_chain = prompt | llm | StrOutputParser()

# 3. 封装为带历史记录的 Runnable
# RunnableWithMessageHistory:
with_history_chain = RunnableWithMessageHistory(
    base_chain,  # 核心 Chain
    get_session_history=get_session_history,  # 历史记录后端工厂函数
    # 告诉 Chain 用户的当前问题在输入字典中的键名
    input_messages_key="03_embeddings",
    # 告诉 Chain 历史消息在 Prompt 模板中的占位符名
    history_messages_key="history",
)

print("✅ RunnableWithMessageHistory 封装完成。")
print("-" * 50)


def run_chat_session(session_id: str):
    """运行一个带记忆的聊天会话"""
    print(f"\n--- 正在启动会话: {session_id} ---")

    # config 字典必须包含 'configurable' 键，其中包含 'session_id'
    config: RunnableConfig = {"configurable": {"session_id": session_id}}

    # 第一轮：引入记忆
    query_1 = "我的名字叫张三，我来自深圳，我最喜欢的运动是篮球。"
    print(f"[用户]: {query_1}")
    response_1 = with_history_chain.invoke({"03_embeddings": query_1}, config=config)
    print(f"[AI 助手]: {response_1}\n")

    # 第二轮：测试记忆 (无需重复城市和运动)
    query_2 = "我最喜欢的运动是什么？我来自哪个城市？"
    print(f"[用户]: {query_2}")
    response_2 = with_history_chain.invoke({"03_embeddings": query_2}, config=config)
    print(f"[AI 助手]: {response_2}\n")

    # 第三轮：确认记忆
    query_3 = "好的，请问我的名字是？"
    print(f"[用户]: {query_3}")
    response_3 = with_history_chain.invoke({"03_embeddings": query_3}, config=config)
    print(f"[AI 助手]: {response_3}\n")

    # 验证：检查内部存储是否已保存
    history_list = get_session_history(session_id).messages
    print(f"--- 会话 {session_id} 历史消息总数: {len(history_list)} ---")

    # 打印前两轮的完整历史记录
    # for msg in history_list:
    #     print(f"[{msg.type.upper()}]: {msg.content}")
    print("---------------------------------------")


# 运行两个不同的会话，验证 session_id 隔离
run_chat_session("zhang-san-session-001")
run_chat_session("li-si-session-002")
