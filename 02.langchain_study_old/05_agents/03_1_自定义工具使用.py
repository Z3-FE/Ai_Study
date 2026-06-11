"""
自定义工具运行 x的平方 例如用户输入 3的平方
"""
import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from langchain_study.env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE

# --- 1. 配置环境变量 ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL


# --- 2. 定义自定义工具 ---
# 使用 @tool 装饰器定义工具，docstring 会作为工具描述提供给 LLM
@tool
def square(x: int) -> int:
    """计算一个数字的平方。"""
    print(f"DEBUG: 正在计算 {x} 的平方...")
    return x * x


# --- 3. 初始化 LLM ---
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    verbose=True
)

# --- 4. 创建 Agent ---
# 将自定义工具添加到工具列表
tools = [square]

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="你是一个精通数学计算的助手。如果用户需要计算平方",
    debug=True
)

# --- 5. 运行 Agent ---
print("\n>>> 用户提问：3的平方是多少？")

# 调用 Agent
response = agent.invoke({"messages": [HumanMessage(content="3的平方是多少？")]})

print("-" * 50)
last_message = response["messages"][-1]
print("最终回复:", last_message.content)
