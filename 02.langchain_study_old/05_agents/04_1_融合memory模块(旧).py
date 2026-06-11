import os
import sys

from langchain_classic import hub
from langchain_classic.memory import ConversationBufferMemory
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
# 创建一个会话缓冲记忆实例
memory = ConversationBufferMemory(
    memory_key="chat_history",  # 变量名必须匹配 Prompt 中的 MessagesPlaceholder 的 name
    return_messages=True  # 记忆以 Message 列表形式返回
)
tools = [TavilySearchResults(max_results=1)]

"""
模板信息内容：

System: You are a helpful assistant
Human: {input}
Placeholder: {chat_history}
Placeholder: {agent_scratchpad}
"""
prompt = hub.pull("hwchase17/openai-tools-agent")

# --- 4. 创建 Agent 和 AgentExecutor ---

# 使用 create_tool_calling_agent 创建 Agent
# 这种方法更健壮，因为它依赖模型内置的函数调用能力。
agent = create_tool_calling_agent(llm, tools, prompt)

# 创建 Agent 执行器 (AgentExecutor)
# 核心机制：通过 'memory' 参数，AgentExecutor 在每次运行前，
# 会将 memory 中的历史记录注入到 prompt 中的 'chat_history' 变量。
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,  # 关键：将 memory 模块传递给执行器
    verbose=True,
    # 必须明确传入输入键，以匹配 Prompt 期望的键名
    # "input" 和 "chat_history"
    # handle_parsing_errors=True # 如果匹配不到关键字，不是直接崩溃 （生产环境中使用）
)

# --- 5. 运行多轮对话（演示记忆功能） ---

print("--- 第一轮：Agent 学习并记忆 ---")
first_query = "请记住我的狗叫'旺财'。"
agent_executor.invoke({"input": first_query})

print("\n" + "=" * 50 + "\n")

print("--- 第二轮：Agent 使用记忆 + 搜索工具 ---")
second_query = "旺财最近需要打疫苗吗？请帮我搜索一下一般狗狗疫苗的最新建议。"
agent_executor.invoke({"input": second_query})
