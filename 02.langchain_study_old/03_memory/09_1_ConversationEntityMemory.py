"""
键值对的存储方式
{name: "张三"}
"""
import os
import sys

from langchain_community.memory.kg import ConversationKGMemory

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_classic.chains.conversation.base import ConversationChain
from langchain_classic.memory import ConversationEntityMemory
from langchain_classic.memory.prompt import ENTITY_MEMORY_CONVERSATION_TEMPLATE
from langchain_openai import ChatOpenAI

from langchain_study.env_utils import MODEL_NAME, API_KEY, BASE_URL, TEMPERATURE

# --- 配置 LLM ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

# LLM 实例
# ConversationEntityMemory 需要 LLM 来从对话中提取实体并生成摘要
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    verbose=True
)

print(f"✅ 模型 '{llm.model_name}' 初始化成功。")
print("-" * 50)

# --- 1. 初始化 ConversationEntityMemory ---
# 这个 Memory 会自动提取对话中的实体（如人名、地名、特定名词），并维护关于这些实体的知识库。
memory = ConversationEntityMemory(llm=llm)

# --- 2. 创建 ConversationChain ---
# 注意：使用专门为实体记忆设计的 Prompt 模板 ENTITY_MEMORY_CONVERSATION_TEMPLATE
# 这个模板包含了 {entities} 变量，用于将相关实体的上下文注入 Prompt
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=ENTITY_MEMORY_CONVERSATION_TEMPLATE,
    verbose=True
)

print("--- 启动会话：观察实体提取与记忆 ---")

# --- 3. 运行对话 ---

# 轮次 1：介绍两个实体
print("\n>>> 轮次 1：介绍实体 'Sam' 和 'Google'")
response_1 = conversation.predict(input="Sam 在 Google 工作，他是一名资深工程师。")
print(f"[AI 助手]: {response_1}")
print(f"\n[状态 1] 实体存储 (Entity Store):\n{memory.entity_store.store}")
print("-" * 50)

# 轮次 2：介绍另一个实体，并提及之前的实体
print("\n>>> 轮次 2：介绍实体 'Lucy' 并关联 'Sam'")
response_2 = conversation.predict(input="Lucy 是 Sam 的同事，她非常喜欢用 Python 编程。")
print(f"[AI 助手]: {response_2}")
print(f"\n[状态 2] 实体存储 (Entity Store):\n{memory.entity_store.store}")
print("-" * 50)

# 轮次 3：询问关于实体的信息
print("\n>>> 轮次 3：询问实体信息")
# Memory 会检索 'Sam' 和 'Lucy' 的相关信息注入 Prompt
response_3 = conversation.predict(input="Sam 和 Lucy 是什么关系？他们各自擅长什么？")
print(f"[AI 助手]: {response_3}")
print("-" * 50)

# 打印最终的 Memory 状态
print(f"\n[最终状态] 实体缓存 (Buffer):\n{memory.buffer}")
print(f"\n[最终状态] 完整实体库:\n{memory.entity_store.store}")
