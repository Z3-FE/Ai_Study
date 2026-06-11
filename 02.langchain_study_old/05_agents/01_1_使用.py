import os
import sys

from langchain_core.tools import StructuredTool

# 将项目根目录添加到 sys.path，以便导入 env_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from langchain_study.env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE

# --- 1. 配置环境变量 ---
# 设置 Tavily API Key (用户提供)
os.environ["TAVILY_API_KEY"] = "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"

# 设置 LLM 相关的环境变量
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL

print("--- 初始化 Agent ---")

# --- 2. 初始化 LLM ---
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    verbose=True
)

# --- 3. 初始化工具 ---
# TavilySearchResults 是一个强大的搜索工具，适合 Agent 使用

# 3.1自定义说明，也可以不写，直接使用
# search_tool = Tool(
#     func=TavilySearchResults(max_results=1).run,
#     name="search_tianqi",
#     description="调用浏览器查询天气",
# )
# tools = [search_tool]


# 3.2
tools = [TavilySearchResults(max_results=1)]

# --- 4. 创建 Agent ---
# 定义 Prompt，包含 agent_scratchpad 用于存放中间步骤
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个乐于助人的助手。如果需要查询实时信息（如天气），请使用搜索工具。"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),  # 必须要声明的！！！
])

# 创建 Tool Calling Agent
agent = create_tool_calling_agent(llm, tools, prompt)

# 创建 AgentExecutor (Agent 的运行时)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --- 5. 运行 Agent ---
print("\n>>> 用户提问：今天北京的天气怎么样？")
response = agent_executor.invoke({"input": "今天北京的天气怎么样？"})

print("-" * 50)
print('数据：', response)
print("-" * 50)

print("最终回复:", response["output"])
