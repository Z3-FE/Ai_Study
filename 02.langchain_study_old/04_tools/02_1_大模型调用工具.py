import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_community.tools import MoveFileTool
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from langchain_study.env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE

os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL
# 任何大语言模型都匹配 openai
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    # api_key=API_KEY,
    # base_url=BASE_URL
)

message = [
    HumanMessage('把当前目录文件a.py移动到/Users/z523/Desktop')
]

# 工具列表
tools = [MoveFileTool()]

# 绑定工具
llm_with_tools = llm.bind_tools(tools)

# 调用大模型
response = llm_with_tools.invoke(message)

print("Response Content:", response.content)
print("Tool Calls:", response.tool_calls)
print("-" * 50)

# --- 2. 解析并执行工具调用 ---
if response.tool_calls:
    # 获取第一个工具调用请求
    tool_call = response.tool_calls[0]
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    tool_id = tool_call["id"]

    print(f"执行工具: {tool_name}")
    print(f"参数: {tool_args}")

    # 查找对应的工具实例 next() 类似 find
    tool_instance = next((t for t in tools if t.name == tool_name), None)

    if tool_instance:
        # 执行工具
        tool_output = tool_instance.invoke(tool_args)
        print(f"工具执行结果: {tool_output}")
    else:
        print(f"未找到工具: {tool_name}")

print("-" * 50)
