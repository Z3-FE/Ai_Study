from langchain_core.prompts import PromptTemplate

# import os
# from langchain_openai import ChatOpenAI
# from env_utils import (
#     API_KEY,
#     BASE_URL,
#     MODEL_NAME,
#     TEMPERATURE  # 导入 float 类型的温度值
# )
#
# # 也可以赋值给环境变量使用
# os.environ["OPENAI_API_KEY"] = API_KEY
# os.environ["OPENAI_BASE_URL"] = BASE_URL
# # 任何大语言模型都匹配 openai
# llm = ChatOpenAI(
#     model_name=MODEL_NAME,
#     temperature=TEMPERATURE,
#     # api_key=API_KEY,
#     # base_url=BASE_URL
# )

# 创建PromptTemplate
# 方法一：
# input_variables 、template 是必传参数
Prompt_Tem = PromptTemplate(
    input_variables=['name', 'role'],
    template='一个{role}的身份，名字叫做{name}'
)

# 方法二： 推荐！！！ template可以纯字符串，format则不需要进行参数传递
Prompt_Tem2 = PromptTemplate.from_template(template='一个{role}的身份，名字叫做{name}')

# 方式三： 部分变量直接初始化赋值
Prompt_Tem3 = PromptTemplate.from_template(
    template='一个{role}的身份，名字叫做{name}',
    partial_variables={'role': '演员3'}
)
# 方法四： PromptTemplate函数设置
Prompt_Tem4 = PromptTemplate.from_template(
    template='一个{role}的身份，名字叫做{name}',
).partial(role='演员4')

# 方法五： 组合提示词模板, 字符串链接
Prompt_Tem5 = (
        PromptTemplate.from_template(template='一个{role}的身份,')
        + '\n名字叫做{name}'
)
print(Prompt_Tem)
print(Prompt_Tem2)

# 2.调用
# 方法1： format调用
prompt = Prompt_Tem.format(name='迪丽热巴', role='演员')
prompt2 = Prompt_Tem2.format(name='迪丽热巴2', role='演员2')
prompt3 = Prompt_Tem3.format(name='迪丽热巴3')
prompt4 = Prompt_Tem4.format(name='迪丽热巴4')
prompt5 = Prompt_Tem5.format(name='迪丽热巴5', role='演员5')
# 方法2： invoke调用
prompt6 = Prompt_Tem5.invoke(input={'name': '地理日吧', 'role': '演员6'})

print(prompt)
print(prompt2)
print(prompt3)
print(prompt4)
print(prompt5)
print(prompt6)

# print(llm.invoke(prompt5))
