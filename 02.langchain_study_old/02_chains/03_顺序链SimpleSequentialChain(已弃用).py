"""
SimpleSequentialChain 是 LangChain 中一个相对基础的链结构，
用于将多个 LLMChain 按顺序串联起来，实现一个步骤的输出作为下一个步骤的输入。
"""
import os

from langchain_classic.chains.llm import LLMChain
from langchain_classic.chains.sequential import SimpleSequentialChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from langchain_study.env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE

os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

# 1. 初始化组件 (与上例相同)
# 任何大语言模型都匹配 openai
llm = ChatOpenAI(
    model_name=MODEL_NAME,
    temperature=TEMPERATURE,
    # api_key=API_KEY,
    # base_url=BASE_URL
)
# --- 第一步：文章生成 Chain ---
# 定义第一步的 Prompt
prompt_1 = PromptTemplate(
    input_variables=["topic"],
    template="请围绕主题'{topic}'，写一篇 300 字左右的文章，要求内容积极向上。",
)
# 创建第一个 LLMChain
chain_1 = LLMChain(llm=llm, prompt=prompt_1, verbose=True)

# --- 第二步：翻译 Chain ---
# 定义第二步的 Prompt。注意：输入变量名称不重要，因为 SimpleSequentialChain 自动传递上一步的完整输出
prompt_2 = PromptTemplate(
    input_variables=["input"],  # 习惯性地使用 'input' 或 'text'
    template="请将以下中文文本翻译成地道的英文，只输出翻译结果。\n\n中文文本：\n{input}",
)
# 创建第二个 LLMChain
chain_2 = LLMChain(llm=llm, prompt=prompt_2)

# 2. 实例化 SimpleSequentialChain
# 将链条列表传入 02_chains 参数中
overall_chain = SimpleSequentialChain(
    chains=[chain_1, chain_2],
    verbose=True  # 设置为 True 可以看到每一步的输入和输出
)

print("✅ SimpleSequentialChain 实例创建成功。")
print("-" * 50)

# 3. 运行 Chain
input_topic = "人工智能的乐观未来"
print(f"🚀 正在运行 Chain，初始输入主题：{input_topic}...")

# SimpleSequentialChain 只需要一个输入
response = overall_chain.invoke(input_topic)

print("\n--- 最终输出 (英文翻译) ---")
print(response['output'].strip())
print("-" * 50)
