"""
工具调用示例
"""

import os

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.tools import tool
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


# 4. tool 调用
@tool
def get_weather(location: str) -> str:
    """Get the weather at a location."""
    return f"在 {location} 天气晴朗。"


model_with_tools = model.bind_tools([get_weather])

# 4.1 工具调用 注：直接调用工具，模型不会直接返回调用工具的结果
# response = model_with_tools.invoke('北京天气？')
# for tool_call in response.tool_calls:
#     # View tool calls made by the model
#     print(f"Tool: {tool_call['name']}")
#     print(f"Args: {tool_call['args']}")


# 4.2 工具调用流程 -> 融合返回结果
# Step 1: 模型生成工具调用
# messages = [{"role": "user", "content": "北京天气？"}]
# ai_msg = model_with_tools.invoke(messages)
# messages.append(ai_msg)

## Step 2: 执行工具调用，获取工具结果
# for tool_call in ai_msg.tool_calls:
#     tool_result = get_weather.invoke(tool_call)
#     messages.append(tool_result)
#
# # Step 3: 模型生成最终响应
# final_response = model_with_tools.invoke(messages)
# print(final_response.text)

# 4.3 强制调用工具

# model_with_tools = model.bind_tools([get_weather], tool_choice="any")  # 强制调任何工具
# model_with_tools = model.bind_tools([get_weather], tool_choice="get_weather")  # 强制调用指定工具

# 4.4 并行调用工具

# messages = [{"role": "user", "content": "波士顿和东京的天气如何？"}]
# response = model_with_tools.invoke(messages)
# messages.append(response)
# for tool_call in response.tool_calls:
#     if tool_call['name'] == 'get_weather':
#         result = get_weather.invoke(tool_call)
#     messages.append(result)
#
# print(f'messages: {messages}')
# final_response = model_with_tools.invoke(messages)
# print(f'final_response: {final_response.content}')


# 4.5 工具调用流式输出

# for chunk in model_with_tools.stream(
#         "波士顿和东京的天气如何？"
# ):
#     # Tool call chunks arrive progressively
#     for tool_chunk in chunk.tool_call_chunks:
#         if name := tool_chunk.get("name"):
#             print(f"Tool: {name}")
#         if id_ := tool_chunk.get("id"):
#             print(f"ID: {id_}")
#         if args := tool_chunk.get("args"):
#             print(f"Args: {args}", end='', flush=True)

# 1. 对话历史列表（初始化包含用户问题）

history = [{"role": "user", "content": "波士顿和东京的天气如何？"}]
# 2. 初始化一个空的聚合变量
gathered = None

# 3. 开始流式迭代
for chunk in model_with_tools.stream(history):
    # 将碎片累加。如果是第一个碎片，直接赋值；后续碎片则执行 + 运算
    gathered = chunk if gathered is None else gathered + chunk

    # 实时查看内容流出（可选）
    if chunk.content:
        print(chunk.content, end="|", flush=True)

# 此时，gathered 已经是一个完整的 AIMessage 了，包含了完整的 tool_calls
print("\n--- 聚合后的完整消息 ---")
print(gathered)

# 4. 检查是否有工具调用
if gathered.tool_calls:
    # 将模型生成的完整工具请求加入历史
    history.append(gathered)

    # 依次执行工具调用
    for tool_call in gathered.tool_calls:
        observation = get_weather.invoke(tool_call["args"])

        # 将工具返回的结果（ToolMessage）加入历史
        history.append(observation)

# 5. 最后，将包含工具结果的历史再次传给模型，获取最终自然语言回答
final_response = ""
for chunk in model_with_tools.stream(history):
    final_response += chunk.content
    print(chunk.content, end="", flush=True)
