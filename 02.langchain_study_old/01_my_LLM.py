from langchain_openai import ChatOpenAI
from env_utils import (
    API_KEY,
    BASE_URL,
    MODEL_NAME,
    TEMPERATURE  # 导入 float 类型的温度值
)

# 任何大语言模型都匹配 openai
llm = ChatOpenAI(
    model_name=MODEL_NAME,
    temperature=TEMPERATURE,
    api_key=API_KEY,
    base_url=BASE_URL
)

# langchain-deepseek deepseek自己的专用
# llm = ChatDeepSeek(
#     model_name=MODEL_NAME,
#     temperature=TEMPERATURE,
#     api_key=API_KEY,
#     api_base=BASE_URL
# )

# 普通调用
# result = llm.invoke('今天天气怎么样')
# print(type(result)) # langchain_core.messages.ai.AIMessage
# print(result)

# 流式调用
result = []
for chunk in llm.stream('今天天气怎么样'):
    print(type(chunk))  # <class 'langchain_core.messages.ai.AIMessageChunk'>
    if chunk.content:
        result.append(chunk.content)
    print(chunk)

print(''.join(result))  # 输出中文

if __name__ == "__main__":
    print('主文件')
