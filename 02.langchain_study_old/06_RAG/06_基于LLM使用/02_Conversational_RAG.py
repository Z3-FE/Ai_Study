"""
RAG + History (Conversational RAG)
这是一个带有“记忆”的 RAG 系统。
难点：当用户问后续问题（如“那它怎么连？”）时，这是一个指代模糊的问题。
如果直接拿去检索，搜不到任何东西。
所以需要两步：
1. 历史感知链 (History Aware Retriever): 把“历史对话 + 最新问题”改写成一个独立的、完整的搜索语句。
2. 文档问答链 (Document Chain): 拿着检索到的文档和原始问题回答。
"""
import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# 兼容性导入：尝试从不同位置导入 chain
try:
    from langchain.chains import create_history_aware_retriever, create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
except ImportError:
    # 如果是旧版本或结构变动，尝试直接自己实现简单的逻辑
    print("Warning: Standard chain imports failed. Using manual chain construction.")
    pass

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

llm = ChatOpenAI(model=MODEL_NAME, base_url=BASE_URL, api_key=API_KEY, temperature=0)

# --- 2. 关键步骤 A: 创建“历史感知检索器” ---
# 它的任务是：如果问题里有“它”、“这个”这种代词，根据历史把它改写成独立问题
contextualize_q_system_prompt = """给定一个聊天历史和最新的用户问题（可能引用了聊天历史中的上下文），
请构造一个独立的问题，这就无需聊天历史也能理解。
不要回答问题，只需根据需要重写它，如果不需要重写就原样返回。"""

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"), # 占位符，用于放入历史记录
    ("human", "{input}"),
])

# 如果标准库导入失败，我们手动构建这个简单的链
# history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
history_aware_retriever = (
    contextualize_q_prompt
    | llm
    | StrOutputParser()
    | retriever
)

# --- 3. 关键步骤 B: 创建“文档问答链” ---
# 它的任务是：拿到文档后，回答用户的问题
qa_system_prompt = """你是一个助手。请根据以下上下文回答问题。
如果你不知道，就说不知道。

{context}"""

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),
    MessagesPlaceholder("chat_history"), # 这里也要放历史，因为回答时可能也需要参考之前的语气或内容
    ("human", "{input}"),
])

# create_stuff_documents_chain: 最基础的合并文档链，把所有文档塞进 prompt
# question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 手动构建问答链
question_answer_chain = (
    {
        "context": lambda x: format_docs(x["context"]),
        "chat_history": lambda x: x["chat_history"],
        "input": lambda x: x["input"]
    }
    | qa_prompt
    | llm
    | StrOutputParser()
)

# --- 4. 组合成最终的 RAG 链 ---
# rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

# 手动组合：
# 1. 拿到 input 和 chat_history
# 2. 传给 history_aware_retriever 得到 context (docs)
# 3. 把 context, chat_history, input 传给 question_answer_chain
rag_chain = (
    RunnablePassthrough.assign(
        context=history_aware_retriever
    )
    | question_answer_chain
)

# --- 5. 管理状态 (Session History) ---
# 前面的 rag_chain 本身是无状态的，我们需要用 RunnableWithMessageHistory 把它包起来
# 在内存中存储每个 session_id 对应的历史
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer", # 如果是 StrOutputParser，输出就是字符串，不需要指定 key，或者需要调整
)

# 修正：因为我们的手动链直接返回字符串，而不是字典，所以 output_messages_key 不需要指定或者会有所不同
# RunnableWithMessageHistory 期望链返回一个字典（如果指定了 output_messages_key），或者它把整个输出当成回复
conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# --- 6. 执行多轮对话测试 ---
session_id = "user_123"

# Round 1
query1 = "Wifi 密码是多少？"
print(f"\n>>> [Round 1] 用户: {query1}")
response1 = conversational_rag_chain.invoke(
    {"input": query1},
    config={"configurable": {"session_id": session_id}}
)
# 手动链直接返回字符串
print(f">>> AI: {response1}")

# Round 2: 这是一个带有代词的问题，如果不看历史，根本不知道“之后”指什么，“做什么”指什么
query2 = "连上之后需要做什么？"
print(f"\n>>> [Round 2] 用户: {query2}")
print("(系统内部会自动将这个问题改写为类似 '连上 Wifi 后需要做什么？' 去检索)")
response2 = conversational_rag_chain.invoke(
    {"input": query2},
    config={"configurable": {"session_id": session_id}}
)
print(f">>> AI: {response2}")

# Round 3
query3 = "认证密码呢？"
print(f"\n>>> [Round 3] 用户: {query3}")
response3 = conversational_rag_chain.invoke(
    {"input": query3},
    config={"configurable": {"session_id": session_id}}
)
print(f">>> AI: {response3}")
