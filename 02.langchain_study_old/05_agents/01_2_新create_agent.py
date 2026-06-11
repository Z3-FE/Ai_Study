import os
import sys
import warnings

# 忽略 Tavily 库中的 Pydantic 字段覆盖警告
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_tavily")

# 将项目根目录添加到 sys.path，以便导入 env_utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_tavily import TavilySearch
from langchain_openai import ChatOpenAI
# 使用新的 create_agent API (基于 LangGraph)
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
tools = [TavilySearch(max_results=1)]

# --- 4. 创建 Agent (CompiledStateGraph) ---
# create_agent 直接返回一个可执行的图，不需要 AgentExecutor

# 方式 1：直接传入字符串作为 system_prompt (最简单)
# agent = create_agent(
#     model=llm,
#     tools=tools,
#     system_prompt="你是一个智能助手，擅长查询实时信息。"
# )

# 方式 2：使用 SystemMessage 对象 (稍微正式点)
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SystemMessage(content="你是一个智能助手，擅长查询实时信息。")
)

# # 方式 3 (推荐)：如果你想使用 ChatPromptTemplate 的强大功能（如变量替换）
# # 你需要先将 Prompt "烘焙" (Invoke) 成具体的 SystemMessage，然后再传给 create_agent
# from langchain_core.prompts import ChatPromptTemplate
#
# # 定义模板
# prompt_template = ChatPromptTemplate.from_messages([
#     ("system", "你是一个智能助手。你的名字是 {name}，你擅长 {skill}。"),
#     # 注意：create_agent 会自动处理 user input 和 tool calls，
#     # 所以这里只需要定义 System Prompt 部分即可，不需要 "human" 或 "placeholder"
# ])
#
# # 渲染 Prompt (填入变量)
# system_message = prompt_template.invoke({"name": "小爱", "skill": "查询实时天气"}).to_messages()[0]
#
# agent = create_agent(
#     model=llm,
#     tools=tools,
#     system_prompt=system_message
# )

# --- 5. 运行 Agent ---
print("\n>>> 用户提问：今天上海的天气如何？")

# LangGraph agent 的输入通常是 {"messages": [...]}
response = agent.invoke({"messages": [HumanMessage(content="今天上海的天气如何？")]})

print("-" * 50)
print("数据:", response)
print("-" * 50)
# response 是一个包含 messages 列表的字典
# 获取最后一条消息（AI 的最终回复）

last_message = response["messages"][-1]
print("最终回复:", last_message.content)
