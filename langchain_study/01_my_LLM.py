from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from env_utils import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL_NAME_RE,
    DEEPSEEK_TEMPERATURE  # 导入 float 类型的温度值
)

# 任何大语言模型都匹配 openai
llm = ChatOpenAI(
    model_name=DEEPSEEK_MODEL_NAME_RE,
    temperature=DEEPSEEK_TEMPERATURE,
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

# langchain-deepseek deepseek自己的专用
# llm = ChatDeepSeek(
#     model_name=DEEPSEEK_MODEL_NAME_RE,
#     temperature=DEEPSEEK_TEMPERATURE,
#     api_key=DEEPSEEK_API_KEY,
#     api_base=DEEPSEEK_BASE_URL
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

