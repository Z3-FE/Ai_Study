import os

from langchain_classic.chains.conversation.base import ConversationChain
from langchain_classic.chains.llm import LLMChain
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_study.env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE

# 导入 DeepSeek 配置 (假设这些变量已在环境中定义)

# --- 配置 LLM (使用占位符，请替换为你的实际配置) ---
# ⚠️ 请确保在实际运行环境中设置这些环境变量
# --- 配置 LLM ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
)
print(f"✅ 模型 '{llm.model_name}' 初始化成功。")
print("-" * 50)

# 2. 初始化 Memory (设置窗口 K=3)
WINDOW_SIZE = 2
# K=3 意味着最多保留 2 轮（2条 Human + 2条 AI）消息
window_memory = ConversationBufferWindowMemory(
    memory_key="history",
    return_messages=True,  # 确保返回消息列表，兼容 ChatModel
    k=WINDOW_SIZE
)
print(f"✅ ConversationBufferWindowMemory 初始化完成，K={WINDOW_SIZE}")

# 3. 定义 Prompt
template = """你是一个测试记忆的助手，请基于你收到的历史记录进行回复。
{history}
Human: {input}
AI Assistant:"""

prompt = PromptTemplate(
    input_variables=["history", "input"],
    template=template
)

# 4. 构造 Chain
memory_test_chain = LLMChain(
    llm=llm,
    memory=window_memory,
    prompt=prompt,
    verbose=True,
)
print("✅ Chain 构造完成。")
print("-" * 50)

# 5. 运行对话 (演示记忆滑动)
print("🚀 启动记忆滑动测试...")

# -------------------- 轮次 1：初始对话 (会被丢弃) --------------------
query_1 = "我的秘密数字是 42."
print(f"[用户 1]: {query_1}")
memory_test_chain.invoke({"input": query_1})

# -------------------- 轮次 2：正常记忆 --------------------
query_2 = "今天天气如何？"
print(f"[用户 2]: {query_2}")
memory_test_chain.invoke({"input": query_2})

# -------------------- 轮次 3：正常记忆 --------------------
query_3 = "好的，请问我最喜欢的颜色是什么？ (我没说过)"
print(f"[用户 3]: {query_3}")
memory_test_chain.invoke({"input": query_3})

# -------------------- 轮次 4：触发丢弃 --------------------
# 此时，第 1 轮消息 (秘密数字 42) 将被丢弃
query_4 = "请问我的秘密数字是多少？"
print(f"[用户 4]: {query_4}")
response_4 = memory_test_chain.invoke({"input": query_4})
print(f"[AI 助理 4]: {response_4}")

# 验证：检查第一条消息是否是 H2
history_data = window_memory.load_memory_variables({})
print(history_data)
print("历史信息总数：", len(history_data['history']))
