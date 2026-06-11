import os

from langchain_classic.chains.sql_database.query import create_sql_query_chain
from langchain_core.prompts import ChatPromptTemplate

# 导入 DeepSeek 配置
# 假设 env_utils 模块已配置且能正确导入 DeepSeek API 信息
from langchain_study.env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE

# 导入 LangChain LCEL 组件
from langchain_openai import ChatOpenAI

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# --- 0. 配置 LLM ---
# 将 DeepSeek 配置设置为 OpenAI 兼容环境变量
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

# 1. 初始化 LLM 和 Parser
llm = ChatOpenAI(
    model=MODEL_NAME,  # 使用 model 而非 model_name
    temperature=TEMPERATURE,
)
parser = StrOutputParser()
print(f"✅ LLM ({llm.model_name}) 和 Parser 初始化成功。")
print("-" * 50)

# --- 定义每一步的 Chain ---

# A. 步骤 1: 广告语生成 Chain (product_name -> tagline)
prompt_a = ChatPromptTemplate.from_messages([
    ("system", "你是一位顶尖的文案专家，以简洁和创意见长。"),
    ("user", "请为产品 '{product_name}' 编写一个极具吸引力的广告语。"),
])
chain_a = prompt_a | llm | parser

# B. 步骤 2: 社交媒体帖子生成 Chain (tagline -> social_post)
prompt_b = ChatPromptTemplate.from_messages([
    ("system", "你是一位社交媒体运营专家，擅长编写简短、引人注目的帖子。"),
    ("user", "根据广告语 '{tagline}'，编写一个适合发布在微博上的、字数不超过140字的宣传帖子。"),
])
chain_b = prompt_b | llm | parser

# C. 步骤 3: 费用估算 Chain (social_post -> budget)
prompt_c = ChatPromptTemplate.from_messages([
    ("system", "你是一位市场分析师，专注于预算估算。"),
    ("user", "根据这个宣传帖子的复杂程度：'{social_post}'，估算其推广预算。只需输出金额数字，单位：RMB。"),
])
chain_c = prompt_c | llm | parser

# --- 2. 构建最终的 LCEL 链 (RunnablePassthrough().assign()) ---
#

# 2.1 步骤 1: 生成 tagline 并保留原始输入
full_chain = RunnablePassthrough() | {
    # 这一步接收初始输入 {"product_name": "..."}
    # "tagline" 的值由 chain_a 产生，输入给 chain_a 的是 product_name
    "tagline": chain_a,
    # RunnablePassthrough() 将原始输入键值对 {"product_name": ...} 原样传递到下一步
    "product_name": RunnablePassthrough(),
}

# 2.2 步骤 2: 生成 social_post (依赖上一步的 "tagline")
# .assign() 用于在现有字典结果中添加新的键值对
full_chain = full_chain.assign(
    # social_post 的值来自 chain_b 的执行结果
    # lambda x: x 是当前 Chain 运行到此处的字典结果，包含 {"tagline": ..., "product_name": ...}
    # 我们用字典中的 "tagline" 作为 chain_b 的输入
    social_post=lambda x: chain_b.invoke({"tagline": x["tagline"]})
)

# 2.3 步骤 3: 估算 budget (依赖上一步的 "social_post")
full_chain = full_chain.assign(
    # budget 的值来自 chain_c 的执行结果
    # 用字典中的 "social_post" 作为 chain_c 的输入
    budget=lambda x: chain_c.invoke({"social_post": x["social_post"]})
)

# 3. 运行 Chain
product = "智能语音咖啡机"
print(f"🚀 正在调用 DeepSeek LLM 运行 LCEL 链，产品：{product}...")

# 运行 Chain，输入字典的键名必须匹配 prompt_a 的输入变量名 ('product_name')
response_lcel = full_chain.invoke({"product_name": product})

# 4. 打印结果
print("\n" + "=" * 60)
print("              ✨ LCEL 顺序链最终输出 ✨")
print("=" * 60)
print(f"产品名称: {response_lcel['product_name']}")
print(f"广告语 (tagline): {response_lcel['tagline'].strip()}")
print(f"社交帖子 (social_post): {response_lcel['social_post'].strip()}")
print(f"推广预算 (budget): RMB {response_lcel['budget'].strip()}")
print("=" * 60)

create_sql_query_chain()
