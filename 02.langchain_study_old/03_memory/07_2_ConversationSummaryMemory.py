import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from typing import Dict, Any

from langchain_classic.chains.conversation.base import ConversationChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_classic.memory import ConversationSummaryMemory

from langchain_study.env_utils import MODEL_NAME, API_KEY, BASE_URL, TEMPERATURE

# --- 配置 LLM ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

# LLM 实例，用于 Chat 和生成摘要
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    verbose=True  # 开启 Verbose 观察 LLM 调用，包括摘要生成
)

print(f"✅ 模型 '{llm.model_name}' 初始化成功。")
print("-" * 50)

# --- 1. 初始化 ConversationSummaryMemory ---

# Summary Memory 必须传入一个 LLM 实例用于生成摘要
memory = ConversationSummaryMemory(
    llm=llm,
    memory_key="history",  # 默认键名
    return_messages=False  # 默认返回字符串格式的摘要，适合 PromptTemplate
)
print(f"✅ ConversationSummaryMemory 初始化成功，记忆键名: {memory.memory_key}")
print("-" * 50)

# --- 2. 定义 Prompt 模板 ---
# 注意 PromptTemplate 使用的是 {history} 字符串格式

template = """你是我的总结助手。你的回复应该简洁、友好。
以下是对话历史的摘要：
{history}

新的输入：{input}
AI 回复："""

PROMPT = PromptTemplate(input_variables=["history", "input"], template=template)

# --- 3. 创建 ConversationChain ---
# ConversationChain 内部会自动调用 03_memory 的 load_memory_variables 和 save_context
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=PROMPT,
    verbose=True  # 开启 Verbose 观察 Chain 的执行步骤
)

# --- 4. 运行多轮对话，观察摘要生成 ---

print("--- 启动会话：观察 LLM 生成摘要 ---")

# 轮次 1：建立基础信息
print("\n>>> 轮次 1：建立基础信息")
response_1 = conversation.predict(input="我喜欢蓝色和绿色，我的宠物是一只叫'旺财'的猫。")
print(f"[AI 助手]: {response_1}")

# 此时，03_memory 内部存储了 1 轮对话。
print(f"\n[状态 1] 当前摘要内容:\n{memory.buffer}")
print("-" * 50)

# 轮次 2：积累更多信息，触发摘要更新
print("\n>>> 轮次 2：积累信息 (会触发 LLM 总结旧对话)")
# 总结 Memory 通常在每轮对话后都会尝试更新摘要
response_2 = conversation.predict(input="我想去一个有很多雪山和湖泊的地方旅行。")
print(f"[AI 助手]: {response_2}")

# 此时，观察 verbose 输出，应该可以看到 LLM 被调用了两次：一次是生成回复，一次是生成摘要。
print(f"\n[状态 2] 更新后的摘要内容 (Summary):\n{memory.buffer}")
print("-" * 50)

# 轮次 3：基于摘要进行回复
print("\n>>> 轮次 3：基于摘要进行回复")
# 此时 Prompt 中注入的是 Summary_new，而不是原始消息
response_3 = conversation.predict(input="我上次提到我有什么宠物？")
print(f"[AI 助手]: {response_3}")

# 验证 LLM 是否从摘要中提取了 "旺财" 的信息
print(f"\n[状态 3] 最终摘要内容:\n{memory.buffer}")
print("-" * 50)
