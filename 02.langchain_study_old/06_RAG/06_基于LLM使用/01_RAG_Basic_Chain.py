"""
RAG (Retrieval-Augmented Generation) 基础全流程演示
本案例展示了构建一个 RAG 应用的最简闭环：
1. 加载数据 (Document Loader)
2. 向量化 (Embedding)
3. 存储与检索 (FAISS + Retriever)
4. 提示词模板 (PromptTemplate)
5. LLM 生成 (ChatOpenAI)
6. 链式调用 (LCEL Chain)
"""
import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from langchain_study.env_utils import MODEL_NAME, EMBEDDING_MODEL_NAME, API_KEY, BASE_URL

# --- 1. 准备知识库数据 ---
# 假设这是我们公司的内部文档，LLM 训练时没见过
docs = [
    Document(page_content="公司的午餐补贴标准是每天 50 元。", metadata={"source": "policy"}),
    Document(page_content="加班超过晚上 9 点可以报销打车费。", metadata={"source": "policy"}),
    Document(page_content="年假是每年 10 天，满一年增加 1 天。", metadata={"source": "policy"}),
    Document(page_content="IT 部门的 Wifi 密码是 'Hello@2024'。", metadata={"source": "it_guide"}),
]

# --- 2. 初始化 Embedding 和 向量数据库 ---
print(">>> 正在构建向量索引...")
embed = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    check_embedding_ctx_length=False,
    chunk_size=10
)

# 使用 FAISS 构建内存索引
vectorstore = FAISS.from_documents(docs, embed)

# 转换为 Retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# --- 3. 初始化 LLM ---
llm = ChatOpenAI(
    model=MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    temperature=0 # RAG 任务通常希望回答准确，所以设为 0
)

# --- 4. 定义提示词模板 (Prompt Template) ---
# {context}: 检索到的相关文档内容
# {question}: 用户的提问
template = """你是一个乐于助人的公司行政助手。
请根据下面的上下文信息回答用户的问题。如果你不知道答案，就说不知道，不要编造。

上下文信息：
{context}

用户问题：
{question}
"""

prompt = ChatPromptTemplate.from_template(template)

# --- 5. 构建 LCEL 链 (LangChain Expression Language) ---
# RunnablePassthrough() 允许我们将用户的输入直接传给 prompt 的 question 字段
# 同时，我们将用户的输入传给 retriever，检索结果传给 prompt 的 context 字段

def format_docs(docs):
    """将检索到的 Document 列表转换为拼接的字符串"""
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# --- 6. 执行问答 ---

# 测试 1: 问一个知识库里有的问题
query1 = "Wifi 密码是多少？"
print(f"\n>>> 用户提问: {query1}")
print(">>> AI 回答:")
response1 = rag_chain.invoke(query1)
print(response1)

# 测试 2: 问一个关于福利的问题
query2 = "如果我加班到很晚，能报销车费吗？"
print(f"\n>>> 用户提问: {query2}")
print(">>> AI 回答:")
response2 = rag_chain.invoke(query2)
print(response2)

# 测试 3: 问一个知识库里没有的问题 (测试幻觉)
query3 = "公司老板叫什么名字？"
print(f"\n>>> 用户提问: {query3}")
print(">>> AI 回答:")
response3 = rag_chain.invoke(query3)
print(response3)
