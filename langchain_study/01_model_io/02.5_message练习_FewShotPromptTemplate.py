"""
FewShotChatMessagePromptTemplate  与FewShotPromptTemplate
理解： 惯性，推断，喂数据

"""
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate, FewShotChatMessagePromptTemplate

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from env_utils import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL_NAME_RE,
    DEEPSEEK_TEMPERATURE  # 导入 float 类型的温度值
)

# 也可以赋值给环境变量使用
os.environ["OPENAI_API_KEY"] = DEEPSEEK_API_KEY
os.environ["OPENAI_BASE_URL"] = DEEPSEEK_BASE_URL
# 任何大语言模型都匹配 openai
chat_model = ChatOpenAI(
    model_name=DEEPSEEK_MODEL_NAME_RE,
    temperature=DEEPSEEK_TEMPERATURE,
    # api_key=DEEPSEEK_API_KEY,
    # base_url=DEEPSEEK_BASE_URL
)

prompt_template = PromptTemplate.from_template(
    template="Q: {input} \n A:{output}"
)
examples = [
    {
        "input": "北京很热",
        "output": "北京市",
    },
    {
        "input": "天津很冷",
        "output": "天津市",
    },
    {
        "input": "上海很冷",
        "output": "上海市",
    },

]
fewShow = FewShotPromptTemplate(
    # 实例模板
    example_prompt=prompt_template,
    # 前缀
    # prefix='帮我分析一下：\n',

    # 实例数据
    examples=examples,

    # 后缀 : 这里需要传入 'input' 变量
    suffix='Q: {input}\n A:',

)

few_show_chat = FewShotChatMessagePromptTemplate(
    example_prompt=ChatPromptTemplate([
        ("human", "{input}"),
        ("ai", "{output}"),
    ]),
    examples=[
        {"input": "2 ❤️ 2", "output": "4"},
        {"input": "2 ❤️ 3", "output": "5"},
        {"input": "2 ❤️ 4", "output": "6"},
    ],
)

chat_prompt_tem = ChatPromptTemplate([
    ('system', '你是一个数学天才'),
    few_show_chat,
    ('human', '{input}'),
])

response = chat_model.invoke(fewShow.invoke({"input": '重庆市很热'}))

response2 = chat_model.invoke(chat_prompt_tem.invoke({'input': '2 ❤️ 6'}))
print("response", response)  # 重庆市
print("#" * 30)
print("response2", response2)  # 8
