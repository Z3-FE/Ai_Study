"""
使用 LLM 将对话历史转化为知识图谱（Knowledge Graph）。
"""

import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_classic.chains.conversation.base import ConversationChain
from langchain_classic.memory import ConversationKGMemory
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from langchain_study.env_utils import MODEL_NAME, API_KEY, BASE_URL, TEMPERATURE

# --- 配置 LLM ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

# LLM 实例
# KG Memory 需要 LLM 来从对话中提取实体和关系三元组 (Subject, Predicate, Object)
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    verbose=True
)

print(f"✅ 模型 '{llm.model_name}' 初始化成功。")
print("-" * 50)

# --- 1. 初始化 ConversationKGMemory ---
# Knowledge Graph Memory 使用知识图谱来存储信息。
# 它会将非结构化的文本转换为结构化的三元组。
memory = ConversationKGMemory(llm=llm)

# --- 2. 创建 ConversationChain ---
# 默认的 PROMPT 可能不包含对 context/entities 的显式引用，
# 但 ConversationChain 会自动处理 03_memory.load_memory_variables 返回的内容。
# KGMemory 默认将检索到的相关知识放入 "history" 键中（取决于 memory_key 配置）。

# 为了更清晰地展示 KG 的效果，我们可以自定义 Prompt，或者直接使用默认的。
# 这里使用默认 Prompt，LangChain 会自动将检索到的 KG 知识填充进 Prompt。
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

print("--- 启动会话：观察知识图谱构建与检索 ---")

# --- 3. 运行对话 ---

# 轮次 1：提供事实信息
print("\n>>> 轮次 1：告诉 AI 关于 Sam 的喜好")
response_1 = conversation.predict(input="Sam 非常喜欢吃 Pepperoni Pizza。")
print(f"[AI 助手]: {response_1}")

# 此时 Memory 应该提取了 (Sam, likes, Pepperoni Pizza) 这样的三元组
# 我们可以手动检查一下当前的知识三元组
# 注意：get_current_entities 需要输入文本来寻找相关实体
print(f"\n[调试] 针对 'Sam' 的相关知识: {memory.get_knowledge_triplets('Sam')}")
print("-" * 50)

# 轮次 2：提供更多属性
print("\n>>> 轮次 2：告诉 AI 关于 Sam 的职业")
response_2 = conversation.predict(input="Sam 是一名 Python 开发者。")
print(f"[AI 助手]: {response_2}")
print(f"\n[调试] 针对 'Sam' 的相关知识: {memory.get_knowledge_triplets('Sam')}")
print("-" * 50)

# 轮次 3：复杂查询
print("\n>>> 轮次 3：询问 Sam 的信息")
# Memory 会根据输入中的 "Sam" 检索图谱中的相关三元组，并作为 Context 提供给 LLM
response_3 = conversation.predict(input="Sam 喜欢吃什么？他是做什么工作的？")
print(f"[AI 助手]: {response_3}")
print("-" * 50)

# --- 4. 检查内部图谱结构 (如果有 NetworkX 支持) ---
try:
    # 03_memory.kg 存储了图结构
    # get_all_triplets() 是一个假设的方法，实际 NetworkX 图存储在 03_memory.kg._graph
    # 我们可以尝试打印所有节点和边
    print("\n[最终状态] 知识图谱概览:")
    if hasattr(memory.kg, "_graph"):
        print(f"节点 (Nodes): {memory.kg._graph.nodes}")
        print(f"边 (Edges): {memory.kg._graph.edges}")
    else:
        # 如果底层实现不同，尝试直接获取
        pass
except Exception as e:
    print(f"无法直接打印图结构: {e}")
