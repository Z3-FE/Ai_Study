"""基础用途"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from env_utils import (
    API_KEY,
    BASE_URL,
    MODEL_NAME,
)

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
    max_retries=6,

)
# 1.文本提示
# response = model.invoke("Write a haiku about spring")
# print(response)

# 2. 消息提示
# sys_megs = SystemMessage("你是一个乐于助人的助手，负责将汉语翻译成英语")
# human_megs = HumanMessage("翻译：我喜欢编程。")
# ai_megs = AIMessage("I love programming.")
# message = [sys_megs, human_megs, ai_megs, ai_megs]
# print(model.invoke(message))

# 3. 词典格式
message = [
    {"role": "system", "content": "你是一个乐于助人的助手，负责将汉语翻译成英语"},
    {"role": "human", "content": "翻译：我喜欢编程。"},
    {"role": "assistant", "content": "I love programming."},
]
print(model.invoke(message))
