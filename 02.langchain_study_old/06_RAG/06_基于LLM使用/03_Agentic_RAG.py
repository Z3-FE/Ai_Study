"""
RAG + Agent + Memory (LangGraph 版)
这是最高级的形态：
1. Agent: 拥有工具使用能力（这里我们把 Retriever 封装成一个 Tool）。
2. Memory: 使用 LangGraph 的 Checkpointer 自动管理历史。
3. RAG: 作为 Agent 的一个工具，只有当用户问相关问题时才调用。

优势：
- Agent 可以自主决定是聊天、搜索还是查文档。
- 自动管理记忆，不需要手动改写问题（Agent 内部会自动处理上下文）。
"""
import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
try:
    from langchain.tools.retriever import create_retriever_tool
except ImportError:
    # 兼容性处理：如果无法从 langchain.tools.retriever 导入
    # 则手动创建一个 Tool
    from langchain_core.tools import Tool

    def create_retriever_tool(retriever, name, description):
        def _get_relevant_docs(query: str):
            docs = retriever.invoke(query)
            return "\n\n".join([d.page_content for d in docs])
        
        return Tool(
            name=name,
            func=_get_relevant_docs,
            description=description
        )
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from langchain_study.env_utils import MODEL_NAME, EMBEDDING_MODEL_NAME, API_KEY, BASE_URL

# --- 1. 准备知识库 ---
docs = [
    Document(page_content="IT 部门的 Wifi 密码是 'Hello@2024'。", metadata={"source": "it_guide"}),
    Document(page_content="连接 Wifi 后，需要访问 login.corp.com 进行认证。", metadata={"source": "it_guide"}),
    Document(page_content="认证用户名为工号，初始密码是身份证后六位。", metadata={"source": "it_guide"}),
]

print(">>> 正在构建向量索引...")
embed = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    check_embedding_ctx_length=False,
    chunk_size=10
)
vectorstore = FAISS.from_documents(docs, embed)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# --- 2. 将 Retriever 转换为 Tool ---
# 这步很关键：我们把检索能力封装成一个 Agent 可以调用的工具
retriever_tool = create_retriever_tool(
    retriever,
    name="it_help_search",
    description="用于查询公司 IT 相关的问题，如 Wifi 密码、网络认证、账号问题等。"
)

tools = [retriever_tool]

# --- 3. 初始化 LLM ---
llm = ChatOpenAI(
    model=MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    temperature=0
)

# --- 4. 初始化 Memory (LangGraph Checkpointer) ---
memory = MemorySaver()

# --- 5. 创建 Agent (使用 langgraph 的 create_react_agent) ---
# 注意：state_modifier 在不同版本中参数名可能不同，有时是 system_message
print(">>> 正在初始化 Agent...")
# 兼容性处理：LangGraph 1.0 之前的版本
agent = create_react_agent(
    model=llm,
    tools=tools,
    # state_modifier 或 messages_modifier 都不可用，说明版本可能较旧
    # 在旧版中，通常通过 SystemMessage 传入 messages 列表的第一个元素
    checkpointer=memory,
)

# 我们可以通过手动添加 SystemMessage 到输入来实现 modifier 的效果
system_message = "你是一个乐于助人的公司 IT 助手。如果问题需要查文档，请使用 it_help_search 工具。如果不知道，就说不知道。"

# --- 6. 执行多轮对话测试 ---
config = {"configurable": {"thread_id": "session_rag_1"}}

# Round 1
query1 = "Wifi 密码是多少？"
print(f"\n>>> [Round 1] 用户: {query1}")
# 手动将 SystemMessage 插入到消息列表的最前面
response1 = agent.invoke(
    {"messages": [("system", system_message), HumanMessage(content=query1)]},
    config=config
)
print(f">>> AI: {response1['messages'][-1].content}")

# Round 2: 带有代词的追问
query2 = "连上之后需要做什么？"
print(f"\n>>> [Round 2] 用户: {query2}")
# Agent 会自动看到之前的历史，发现"连上"指的 Wifi，然后决定是否需要再次调用工具
response2 = agent.invoke(
    {"messages": [HumanMessage(content=query2)]},
    config=config
)
print(f">>> AI: {response2['messages'][-1].content}")

# Round 3: 闲聊 (测试是否会乱调工具)
query3 = "你是谁？"
print(f"\n>>> [Round 3] 用户: {query3}")
response3 = agent.invoke(
    {"messages": [HumanMessage(content=query3)]},
    config=config
)
print(f">>> AI: {response3['messages'][-1].content}")
