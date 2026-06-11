"""
  管道调用
  不推荐使用， 1.0版本不需要使用这个
  """

import os

from langchain_classic.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI

from langchain_study.env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE

# --- 配置 ---
# 1. 实例化 LLM
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL
# 任何大语言模型都匹配 openai
llm = ChatOpenAI(
    model_name=MODEL_NAME,
    temperature=TEMPERATURE,
    # api_key=API_KEY,
    # base_url=BASE_URL
)
print(f"✅ 模型 '{llm.model_name}' 实例创建成功。")

# 2. 定义 Prompt 模板
template = """
请以一个历史学家的身份，用中文解释 '{event}' 发生的深层原因，回答不超过三句话。
事件：{event}
解释：
"""
prompt = PromptTemplate(
    input_variables=["event"],
    template=template,
)
print("✅ 提示模板创建成功。")

# 3. 实例化 LLMChain
# 将 llm 和 prompt 传入 LLMChain
#  verbose=True 显示调用过程
llm_chain = LLMChain(llm=llm, prompt=prompt, verbose=True)

print("✅ LLMChain 实例创建成功。")
print("-" * 50)

# 4. 运行 Chain
event_input = "工业革命为什么发生在英国"
print(f"🚀 正在调用模型，事件：{event_input}...")

# 使用 .invoke() 方法执行 Chain
response_dict = llm_chain.invoke({"event": event_input})

# LLMChain.invoke() 返回一个字典，键通常为 'text'
result_text = response_dict['text']

# 5. 打印结果
print("\n--- 完整模型响应 (LLMChain) ---")
print(result_text.strip())
print("-" * 50)
