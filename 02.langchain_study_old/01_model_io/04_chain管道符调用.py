import os

from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

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
llm = ChatOpenAI(
    model_name=MODEL_NAME,
    temperature=TEMPERATURE,
)

output_json = JsonOutputParser()

chat_prompt = ChatPromptTemplate(
    messages=[
        ("system", '你是一个{name}'),
        ("human", '我有一个{question},{type}')
    ],
    partial_variables={
        'type': output_json.get_format_instructions()
    }
)

# 全部使用了 invoke方法调用
# output_json.invoke(
#     llm.invoke(
#     chat_prompt.invoke({"name": '人工智能', "question": "人工智能用英语怎么说的问题。"})
#     )
# )

# 简化：
chain = chat_prompt | llm | output_json

response = chain.invoke({"name": '人工智能', "question": "人工智能用英语怎么说的问题。"})

print(response)
