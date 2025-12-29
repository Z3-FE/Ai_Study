"""
读取文件 yaml或者json
"""
import os
import yaml
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate, FewShotChatMessagePromptTemplate, load_prompt
import langchain_community
import langchain_core
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from env_utils import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL_NAME_RE,
    DEEPSEEK_TEMPERATURE  # 导入 float 类型的温度值
)

chat_model = ChatOpenAI(
    model_name=DEEPSEEK_MODEL_NAME_RE,
    temperature=DEEPSEEK_TEMPERATURE,
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

# 假设您的 JSON 文件名为 'my_prompt.json' 且位于当前目录下

# 1. 加载 Prompt 模板
try:
    prompt = load_prompt("test.json")
    print("✅ Prompt 模板加载成功！")
    print(f"输入变量: {prompt.input_variables}")

    # 2. 格式化和使用 Prompt
    output_prompt = prompt.format(
        topic="宇宙飞船",
        style="幽默风趣"
    )

    print("\n--- 格式化后的 Prompt  (JSON)---")
    print(output_prompt)

    response = chat_model.invoke(output_prompt)
    print(response)

except FileNotFoundError:
    print("❌ 错误：未找到 'test.json' 文件，请确保文件路径正确。")
except Exception as e:
    print(f"❌ 加载 Prompt 时发生错误: {e}")

# 2. 加载 Prompt 模板 (YAML)
try:
    prompt = load_prompt("test.yaml")
    print("✅ Prompt 模板（YAML）加载成功！")
    print(f"输入变量: {prompt.input_variables}")

    # 2. 格式化和使用 Prompt
    output_prompt = prompt.format(
        product="智能降噪耳机",
        feature="长达50小时的续航"
    )

    print("\n--- 格式化后的 Prompt  (YAML) ---")
    print(output_prompt)

    response = chat_model.invoke(output_prompt)
    print(response)

except FileNotFoundError:
    print("❌ 错误：未找到 'my_prompt.yaml' 文件，请确保文件路径正确。")
except Exception as e:
    print(f"❌ 加载 Prompt 时发生错误: {e}")
