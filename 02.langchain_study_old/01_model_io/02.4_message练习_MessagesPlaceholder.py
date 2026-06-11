"""
MessagesPlaceholder
理解： 历史数据插入

"""
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_openai import ChatOpenAI
import os
from env_utils import (
    API_KEY,
    BASE_URL,
    MODEL_NAME,
    TEMPERATURE  # 导入 float 类型的温度值
)

# 也可以赋值给环境变量使用
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL
# 任何大语言模型都匹配 openai
chat_model = ChatOpenAI(
    model_name=MODEL_NAME,
    temperature=TEMPERATURE,
    # api_key=API_KEY,
    # base_url=BASE_URL
)

chat_prompt_template = ChatPromptTemplate([
    ("system", "你是一个记忆力超群的{name}。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "我的名字是什么？,还有一个问题{question}"),
])

chat_format = chat_prompt_template.format_messages(
    name="聊天机器人",
    history=[
        HumanMessage(content="我的名字是小明。"),
        SystemMessage(content="好的，小明，记住了。")
    ],
    question="1+1 = ?"
)
print(chat_format)

response = chat_model.invoke(chat_format)
print('response', response)
