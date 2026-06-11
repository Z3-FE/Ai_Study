# """
# 单条信息调用和对话调用示例
# """
#
# import os
#
# from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
# from langchain_openai import ChatOpenAI
#
# from env_utils import (
#     API_KEY,
#     BASE_URL,
#     MODEL_NAME,
# )
#
# model = ChatOpenAI(
#     model=MODEL_NAME,
#     api_key=API_KEY,
#     base_url=BASE_URL,
#     temperature=0.7,
#     timeout=30,
#     max_tokens=1000,
#     max_retries=6,
#
# )
#
# # 1.单条信息调用
# print(model.invoke("你好"))
#
# print('*' * 40)
#
# # 1.1. 字典列表
# conversation = [
#     {"role": "system", "content": "你是一个乐于助人的助手，负责将汉语翻译成英语"},
#     {"role": "user", "content": "翻译：我喜欢编程。"},
#     {"role": "assistant", "content": "I love programming."},
#     {"role": "user", "content": "翻译：我喜欢构建应用程序。"}
# ]
# print(model.invoke(conversation))
#
# print('*' * 40)
# # 1.2. 消息对象列表
# conversation = [
#     SystemMessage("You are a helpful assistant that translates English to French."),  # 英语转换为法语
#     HumanMessage("Translate: I love programming."),
#     AIMessage("J'adore la programmation."),
#     HumanMessage("Translate: I love building applications.")
# ]
#
# print(model.invoke(conversation))
# print('*' * 40)


# from langchain.agents import create_agent
#
#
# def get_weather(city: str) -> str:
#     """Get weather for a given city."""
#     return f"It's always sunny in {city}!"
#
#
# agent = create_agent(
#     model="openai:gpt-5-mini",
#     tools=[get_weather],
#     system_prompt="You are a helpful assistant",
# )
#
# # Run the agent
# agent.invoke(
#     {"messages": [{"role": "user", "content": "What is the weather in San Francisco?"}]}
# )
