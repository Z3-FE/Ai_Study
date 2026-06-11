import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from typing import Dict, Any, List
import tiktoken
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langchain_classic.chains.conversation.base import ConversationChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_classic.memory import ConversationSummaryBufferMemory

from langchain_study.env_utils import MODEL_NAME, API_KEY, BASE_URL, TEMPERATURE

# --- 配置 LLM ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

MAX_TOKEN_LIMIT = 100  # 设置一个较小的限制，方便观察截断和总结

# --- 手动定义 Token 计数函数 ---
TOKEN_ENCODER = tiktoken.encoding_for_model("gpt-4")


def count_tokens_manually(messages: List[BaseMessage]) -> int:
    """
    一个自定义的 Token 计数函数，用于兼容非 OpenAI 模型。
    """
    total_tokens = 0
    for message in messages:
        if isinstance(message, HumanMessage):
            role_prefix = "user"
        elif isinstance(message, AIMessage):
            role_prefix = "assistant"
        else:
            role_prefix = "system"

        tokens_content = TOKEN_ENCODER.encode(message.content)
        tokens_role = TOKEN_ENCODER.encode(role_prefix)
        total_tokens += len(tokens_content) + len(tokens_role) + 4
    return total_tokens


class ChatOpenAIManualCount(ChatOpenAI):
    def get_num_tokens_from_messages(self, messages: List[BaseMessage]) -> int:
        return count_tokens_manually(messages)


# LLM 实例，用于 Chat 和生成摘要
llm = ChatOpenAIManualCount(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    verbose=True  # 开启 Verbose 观察 LLM 调用，包括摘要生成
)

print(f"✅ 模型 '{llm.model_name}' 初始化成功。")
print(f"✅ 最大 Token 限制 MAX_TOKEN_LIMIT={MAX_TOKEN_LIMIT}")
print("-" * 50)

# --- 1. 初始化 ConversationSummaryBufferMemory ---

# SummaryBuffer Memory 必须传入一个 LLM 实例用于生成摘要，并设定 Token 限制
memory = ConversationSummaryBufferMemory(
    llm=llm,
    max_token_limit=MAX_TOKEN_LIMIT,
    memory_key="history",  # 默认键名
    return_messages=False  # 返回字符串格式，适合 PromptTemplate
)
print(f"✅ ConversationSummaryBufferMemory 初始化成功，Token 限制: {MAX_TOKEN_LIMIT}")
print("-" * 50)

# --- 2. 定义 Prompt 模板 ---
# PromptTemplate 接收 {history} 字符串，该字符串可能包含摘要和原始消息。

template = """你是我的摘要助手。你的回复应该简洁、友好。
以下是对话历史 (包含摘要和最新对话)：
{history}

新的输入：{input}
AI 回复："""

PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)

# --- 3. 创建 ConversationChain ---
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=PROMPT,
    verbose=True  # 开启 Verbose 观察 Chain 的执行步骤
)

# --- 4. 运行多轮对话，观察摘要生成和缓冲区状态 ---

print("--- 启动会话：观察缓冲区管理和摘要生成 ---")

# --- 轮次 1 & 2：建立记忆 (未超限，全部保留) ---
print("\n>>> 轮次 1：建立基础信息 (Token 远低于 100)")
response_1 = conversation.predict(input="我的名字叫艾利克斯，我喜欢研究物理学中的黑洞。")
print(f"[AI 助手]: {response_1}")
print(f"[状态 1] 当前 Token: {llm.get_num_tokens_from_messages(memory.chat_memory.messages)}")
print("-" * 50)

print("\n>>> 轮次 2：积累信息 (仍未超限)")
response_2 = conversation.predict(input="我今天做了一个关于虫洞的报告，感觉不错。")
print(f"[AI 助手]: {response_2}")
print(f"[状态 2] 当前 Token: {llm.get_num_tokens_from_messages(memory.chat_memory.messages)}")
print("-" * 50)

# --- 轮次 3：触发摘要生成和缓冲区截断 ---
print(f"\n>>> 轮次 3：**触发截断和总结** (MAX_TOKEN_LIMIT={MAX_TOKEN_LIMIT})")
# 这条消息足够长，会使总 Token 数超过 100，从而触发 LLM 总结旧消息。
long_input = "请用一个很长的句子来描述黑洞如何形成，以及它们如何扭曲周围的时空。"
response_3 = conversation.predict(input=long_input)
print(f"[AI 助手]: {response_3}")

# 此时，观察 verbose 输出，应该可以看到 LLM 被调用了两次：
# 1. 调用 LLM 生成回复
# 2. 调用 LLM 生成摘要 (将最早的消息压缩)
print(f"\n[状态 3] **截断后** Token: {llm.get_num_tokens_from_messages(memory.chat_memory.messages)}")
print(f"\n[状态 3] 缓冲区内容 (包含摘要):\n{memory.buffer}")
print("-" * 50)

# --- 轮次 4：验证记忆 (基于摘要和剩余消息) ---
print("\n>>> 轮次 4：验证记忆 (基于摘要)")
# 尽管第一轮消息可能被压缩进摘要，但模型应该能记住关键词 "黑洞"
response_4 = conversation.predict(input="我上次提到的研究方向是什么？")
print(f"[AI 助手]: {response_4}")
print(f"\n[状态 4] 最终缓冲区:\n{memory.buffer}")
