import os
import sys
import warnings

from langchain_community.tools import TavilySearchResults
from langchain_experimental.tools import PythonREPLTool

# 忽略 Tavily 库中的 Pydantic 字段覆盖警告
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_tavily")

# 将项目根目录添加到 sys.path，以便导入 env_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage

from langchain_study.env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE

# --- 1. 配置环境变量 ---
# 设置 Tavily API Key
os.environ["TAVILY_API_KEY"] = "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"

# 设置 LLM 相关的环境变量
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

print("--- 初始化 Agent (使用 langchain.agents.create_agent) ---")

# --- 2. 初始化 LLM ---
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    verbose=True
)

# --- 3. 初始化工具 ---
tools = [TavilySearchResults(max_results=1), PythonREPLTool()]

# --- 4. 创建 Agent (CompiledStateGraph) ---
# create_agent 直接返回一个可执行的图，不需要 AgentExecutor

# 方式 1：直接传入字符串作为 system_prompt (最简单)
# agent = create_agent(
#     model=llm,
#     tools=tools,
#     system_prompt="你是一个智能助手，擅长查询实时信息和执行数学计算。"
# )

# 方式 2：使用 SystemMessage 对象 (稍微正式点)
# 注意：create_agent (LangGraph版) 没有 verbose 参数，debug 信息通过 debug=True 开启
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SystemMessage(content="你是一个智能助手，擅长查询实时信息和执行 Python 代码进行计算。"),
    debug=True
)

# --- 5. 运行 Agent ---
print("\n>>> 用户提问：计算 100 的 3.5 次方是多少？")

# LangGraph agent 的输入通常是 {"messages": [...]}
response = agent.invoke({"messages": [HumanMessage(content="计算 100 的 3.5 次方是多少？")]})

print("-" * 50)
print("数据:", response)
print("-" * 50)
# response 是一个包含 messages 列表的字典
# 获取最后一条消息（AI 的最终回复）

last_message = response["messages"][-1]
print("最终回复:", last_message.content)
