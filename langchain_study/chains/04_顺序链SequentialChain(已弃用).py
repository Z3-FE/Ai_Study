"""
SequentialChain 是 LangChain 中一个更高级、更灵活的链式结构，用于将多个 Chain（如 LLMChain 或其他自定义 Chain）按顺序连接起来，实现复杂的多步骤任务。

与 SimpleSequentialChain 最大的区别在于：

多输入/多输出： 它可以处理多个初始输入，并且可以指定哪些中间步骤的输出应该被保留并作为最终输出的一部分。

更强的控制力： 你可以精确地定义每个步骤的输入键 (input key) 和输出键 (output key)。

⚠️ 注意： 和 LangChain 中许多传统的 Chain 类一样，SequentialChain 在 LangChain 1.0+ 版本中也已经被弃用 (Deprecated)。官方推荐使用 LCEL (LangChain Expression Language) 来实现其功能。
"""
import os

from langchain_classic.chains.llm import LLMChain
from langchain_classic.chains.sequential import SequentialChain
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI

from langchain_study.env_utils import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL_NAME_RE, DEEPSEEK_TEMPERATURE

os.environ["OPENAI_API_KEY"] = DEEPSEEK_API_KEY
os.environ["OPENAI_BASE_URL"] = DEEPSEEK_BASE_URL

# 1. 初始化组件 (与上例相同)
# 任何大语言模型都匹配 openai
llm = ChatOpenAI(
    model_name=DEEPSEEK_MODEL_NAME_RE,
    temperature=DEEPSEEK_TEMPERATURE,
    # api_key=DEEPSEEK_API_KEY,
    # base_url=DEEPSEEK_BASE_URL
)
# --- A. 步骤 1: 广告语生成 ---
prompt_a = PromptTemplate(
    input_variables=["product_name"],
    template="你是一位顶尖的文案专家。请为产品 '{product_name}' 编写一个极具吸引力的广告语。",
)
chain_a = LLMChain(
    llm=llm,
    prompt=prompt_a,
    output_key="tagline", # 🌟 指定输出键名为 'tagline'
    verbose=True
)

# --- B. 步骤 2: 社交媒体帖子生成 ---
prompt_b = PromptTemplate(
    input_variables=["tagline"], # 接收上一步的输出 'tagline'
    template="根据广告语 '{tagline}'，编写一个适合发布在微博上的、字数不超过140字的宣传帖子。",
)
chain_b = LLMChain(
    llm=llm,
    prompt=prompt_b,
    verbose=True,
    output_key="social_post", # 🌟 指定输出键名为 'social_post'
)

# --- C. 步骤 3: 费用估算 ---
# 这是一个简化的步骤，我们假设模型能根据帖子内容估算费用
prompt_c = PromptTemplate(
    input_variables=["social_post"], # 接收上一步的输出 'social_post'
    template="根据这个宣传帖子的复杂程度：'{social_post}'，估算其推广预算（只需输出金额数字，单位：RMB）。",
)
chain_c = LLMChain(
    llm=llm,
    prompt=prompt_c,
verbose=True,
    output_key="budget" # 🌟 指定输出键名为 'budget'
)

# 2. 实例化 SequentialChain
full_chain = SequentialChain(
    chains=[chain_a, chain_b, chain_c],
    input_variables=["product_name"], # 初始输入只有一个 'product_name'
    # 🌟 指定最终需要输出的键（包括中间步骤的输出）
    output_variables=["tagline", "social_post", "budget"],
    verbose=True
)

print("✅ SequentialChain 实例创建成功。")
print("-" * 50)

# 3. 运行 Chain
product = "智能语音咖啡机"
print(f"🚀 正在运行 Chain，初始输入产品：{product}...")

# 运行 Chain，输入字典
response = full_chain.invoke({"product_name": product})

# 4. 打印结果
print("\n--- 最终输出 (SequentialChain) ---")
print(f"产品名称: {product}")
print(f"广告语 (tagline): {response['tagline'].strip()}")
print(f"社交帖子 (social_post): {response['social_post'].strip()}")
print(f"推广预算 (budget): RMB {response['budget'].strip()}")
print("-" * 50)
print(f'整合体结果：{response}')