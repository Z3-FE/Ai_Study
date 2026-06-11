import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_study.env_utils import MODEL_NAME, TEMPERATURE, API_KEY, BASE_URL

# --- 1. 初始化 LLM ---
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    api_key=API_KEY,
    base_url=BASE_URL
)

# --- 2. 创建 Prompt Template ---
# 这是一个简单的聊天提示模板
prompt = ChatPromptTemplate.from_template("请用一句话解释什么是：{topic}")

# --- 3. 创建 Output Parser ---
# StrOutputParser 将 LLM 的输出消息直接转换为字符串
parser = StrOutputParser()

# --- 4. 构建 Chain (LCEL 语法) ---
# 使用管道符 | 将组件连接起来：Prompt -> LLM -> Parser
chain = prompt | llm | parser

# --- 5. 运行 Chain ---
print(">>> 开始运行 Chain...")
result = chain.invoke({"topic": "LangChain"})
print(f"结果: {result}")
