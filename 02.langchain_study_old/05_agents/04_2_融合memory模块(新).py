import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from langchain_study.env_utils import MODEL_NAME, TEMPERATURE, API_KEY, BASE_URL

# --- 1. 配置环境变量 ---
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL
os.environ["TAVILY_API_KEY"] = "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"

# --- 2. 初始化 LLM ---
llm = ChatOpenAI(
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    # verbose=True
)

# --- 3. 初始化 Memory (LangGraph Checkpointer) ---
# 在 LangChain 1.0+ / LangGraph 中，我们使用 Checkpointer 来保存状态（记忆）
memory = MemorySaver()

# --- 4. 创建 Agent ---
# create_agent (基于 LangGraph) 直接支持 checkpointer 参数
agent = create_agent(
    model=llm,
    tools=[TavilySearch(max_results=1)],
    system_prompt="你是一个智能助手，擅长查询实时信息。",
    checkpointer=memory,  # 关键点：传入记忆保存器
    # debug=True
)

# --- 5. 验证配置是否成功 ---
# 使用 config 中的 thread_id 来区分不同的会话
config = {"configurable": {"thread_id": "session_1"}}

print("\n>>> [轮次 1] 用户提问：今天上海天气如何？")
response1 = agent.invoke(
    {"messages": [HumanMessage(content="今天上海天气如何？")]},
    config=config
)
print("Agent 回复:", response1["messages"][-1].content)

# --- 验证方法 1：查看状态快照 ---
# 我们可以直接获取当前 thread_id 的状态，看看里面是否保存了历史消息
print("\n>>> [验证 1] 查看当前 Session 的状态快照 (Snapshot):")
state_snapshot = agent.get_state(config)
print("state_snapshot", state_snapshot)  # 打印详细消息列表state_snapshot)

print(f"当前保存的消息数量: {len(state_snapshot.values['messages'])}")

# 获取并打印当前的 thread_id
current_thread_id = state_snapshot.config['configurable']['thread_id']
print(f"当前运行的 thread_id: {current_thread_id}")

print("response1", response1)  # 打印详细消息列表

print("\n" + "-" * 50 + "\n")

print(">>> [轮次 2] 用户提问：适合穿什么衣服？ (测试记忆能力)")
# 注意：这里不需要手动传入 chat_history，LangGraph 会根据 thread_id 自动加载历史
response2 = agent.invoke(
    {"messages": [HumanMessage(content="那适合穿什么衣服？")]},
    config=config
)
print("Agent 回复:", response2["messages"][-1].content)

print("\n" + "-" * 50 + "\n")

# --- 验证方法 2：Session 隔离测试 ---
# 使用一个新的 thread_id，验证它是否会有之前的记忆（预期：没有）
print(">>> [验证 2] 测试 Session 隔离 (使用新的 thread_id):")
config_new = {"configurable": {"thread_id": "session_2"}}
response3 = agent.invoke(
    {"messages": [HumanMessage(content="那适合穿什么衣服？")]},  # 直接问这个问题，如果没有记忆，它会不知道“那”指代什么
    config=config_new
)
print("Session_2 Agent 回复 (预期不知道上下文):", response3["messages"][-1].content)
