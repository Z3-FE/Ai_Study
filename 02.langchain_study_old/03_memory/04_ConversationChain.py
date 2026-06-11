"""
ConversationChain: 是 ConversationBufferMemory 与LLmChain的结合体
"""

import os

from langchain_classic.chains.conversation.base import ConversationChain
from langchain_classic.memory import ConversationBufferMemory, ConversationBufferWindowMemory, ConversationEntityMemory
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# 导入所需的经典 Chain 和 Memory 组件


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

# 1. 定义 Prompt 模板
# ConversationChain 默认需要一个包含 {history} 和 {input} 变量的 Prompt
# {history} 变量会被 Memory 自动填充，{input} 变量会被当前用户输入填充。
template = """你是我的私人心理咨询师。请用同理心和温暖的语气来回复我，并记住我告诉你的信息。

当前对话历史:
{history}
Human: {input}
AI Assistant:"""

prompt = PromptTemplate(
    input_variables=["history", "input"],
    template=template
)
print("✅ PromptTemplate 定义完成。")

# 2. 初始化 Memory 模块
# 使用 ConversationBufferMemory，它将存储所有对话历史
memory = ConversationBufferMemory(
    # 设置 memory_key 必须与 Prompt 模板中的历史变量名 {history} 匹配
    memory_key="history",
    # 设置 return_messages=True 确保返回的是消息对象列表，以更好地兼容 ChatModel
    return_messages=True
)
print("✅ ConversationBufferMemory 初始化完成。")

# 3. 构造 ConversationChain，
# 可以不使用 Memory 和 Prompt 
conversation_chain = ConversationChain(
    llm=llm,
    # 03_memory=03_memory,
    # prompt=prompt,
    verbose=True  # 调试时可以打开，查看完整的 Prompt 注入过程
)
print("✅ ConversationChain 构造完成。")
print("-" * 50)

# 4. 运行对话会话
print("🚀 启动心理咨询对话...")

# 第一次调用 (引入记忆)
query_1 = "我最近工作压力很大，感到焦虑，但我的名字叫小王。"
print(f"[用户]: {query_1}")
# 在 ConversationChain 中，invoke 的输入键名必须是 'input'
response_1 = conversation_chain.invoke({"input": query_1})
print(f"[咨询师]: {response_1['response']}\n")

# 第二次调用 (测试记忆：无需重复提名字和问题)
query_2 = "我感觉我的压力源于上司给我的不合理要求。"
print(f"[用户]: {query_2}")
response_2 = conversation_chain.invoke({"input": query_2})
print(f"[咨询师]: {response_2['response']}\n")

# 第三次调用 (验证名字记忆)
query_3 = "你还记得我的名字吗？"
print(f"[用户]: {query_3}")
response_3 = conversation_chain.invoke({"input": query_3})
print(f"[咨询师]: {response_3['response']}\n")

print("-" * 50)
# 5. 验证内部存储 (可选)
# 打印 03_memory 中存储的完整历史记录
print("--- 内部 Memory 存储的完整历史记录 ---")
# load_memory_variables({}) 返回一个字典，键是 memory_key ('history')
history_data = memory.load_memory_variables({})
for msg in history_data['history']:
    print(f"[{msg.type.upper()}]: {msg.content}")
print("---------------------------------------")
