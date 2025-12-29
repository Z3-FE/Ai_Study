"""
在 LangChain 1.0+ 中，实现顺序链的最佳方法是使用 LCEL 的管道操作符 (|) 来构建一个 RunnableSequence
LCEL 不仅能实现 SimpleSequentialChain 的功能，还能处理多输入和多输出，甚至并行执行，远超传统链的限制。
"""
import os

from langchain_core.prompts import PromptTemplate

from langchain_core.output_parsers import StrOutputParser
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
print(f"✅ 模型 '{llm.model_name}' 实例创建成功。")

parser = StrOutputParser() # 用于将模型输出转换为字符串

# --- 步骤 1: 文章生成 Chain (Prompt 1 + LLM + Parser) ---
prompt_1 = PromptTemplate.from_template(
    "请围绕主题'{topic}'，写一篇 300 字左右的文章，要求内容积极向上。"
)
chain_1 = prompt_1 | llm | parser

# --- 步骤 2: 翻译 Chain (Prompt 2 + LLM + Parser) ---
prompt_2 = PromptTemplate.from_template(
    "请将以下中文文本翻译成地道的英文，只输出翻译结果。\n\n中文文本：\n{text_to_translate}"
)
# 这里的 Prompt 接收一个名为 'text_to_translate' 的变量

# 2. 构建最终的 LCEL Chain

# 关键步骤：使用 LCEL 的 .invoke() 或 .stream() 方法，前一个链的输出会自动作为下一个链的输入。
# Chain 1 的输出 (文章文本) 会作为 Chain 2 的输入变量 'text_to_translate' 的值。
# 这是通过 LangChain 内部的 Runnable 接口自动处理的。

overall_lcel_chain = {
    # 步骤 1：处理初始输入 (topic)，并生成文章
    "text_to_translate": chain_1,
    # 这里的键名 'text_to_translate' 必须匹配 prompt_2 中的输入变量名
} | prompt_2 | llm | parser


print("✅ LCEL 管道构建成功 (实现 SimpleSequentialChain 功能)。")
print("-" * 50)

# 3. 运行 Chain
input_topic = "人工智能的乐观未来"
print(f"🚀 正在运行 LCEL Chain，初始输入主题：{input_topic}...")

# 运行 LCEL Chain，输入字典的键名必须匹配 chain_1 中 prompt_1 的输入变量名 ('topic')
response_lcel = overall_lcel_chain.invoke({"topic": input_topic})

print("\n--- 最终输出 (LCEL 英文翻译) ---")
print(response_lcel.strip())
print("-" * 50)