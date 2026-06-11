from langchain_core.prompts import ChatPromptTemplate
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
# 1.创建实例
# 方法一:
chat_prompt_template = ChatPromptTemplate([
    ('system', '你是一个AI助手，你的名字是{name}'),
    ('human', '我的问题是{question}')
],
    # input_variables=['name', 'question'], 可以不写
)

# 方法二：
chat_prompt_template2 = ChatPromptTemplate.from_messages([
    ('system', '你是一个AI助手，你的名字是{name}'),
    ('human', '我的问题是{question}')
])

print(chat_prompt_template)

# 2.调用
# 方法一： invoke 等价于 format_prompt 就是传入的参数形式不一样
chat_prompt = chat_prompt_template.invoke({"name": "迪丽热巴", "question": '1+1 = ?'})
chat_prompt2 = chat_prompt_template2.format_prompt(name='迪丽热巴2', question='1+1 = ?')
# 方法二： format
chat_prompt3 = chat_prompt_template.format(name='迪丽热巴3', question='1+1 = ?')

# 方法三：
chat_prompt4 = chat_prompt_template.format_messages(name='迪丽热巴4', question='1+1 = ?')

# 返回结果类型
print(type(chat_prompt))  # <class 'langchain_core.prompt_values.ChatPromptValue'>
print(type(chat_prompt3))  # <class 'str'>
print(type(chat_prompt4))  # <class 'list'>

# 类型转换
print("to_string", chat_prompt.to_string(), type(chat_prompt.to_string()))
print("to_messages", chat_prompt.to_messages(), type(chat_prompt.to_messages()))

print(chat_prompt)
print(chat_prompt2)
print(chat_prompt3)
print(chat_prompt4)

# 调用大模型
response = chat_model.invoke(chat_prompt)

print('response', response)
