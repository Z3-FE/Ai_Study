"""
Chroma 向量检索基础演示
演示最基本的 similarity_search_by_vector (向量数值查询)
"""
import os
import sys
import shutil

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_study.env_utils import MODEL_NAME, EMBEDDING_MODEL_NAME, API_KEY, BASE_URL

# 1. 准备数据和路径
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "asset/01_langchain_utf-8.txt")
persist_dir = os.path.join(current_dir, "asset/chroma-search-demo")

# 为了演示清晰，每次清理重建
if os.path.exists(persist_dir):
    shutil.rmtree(persist_dir)

# 2. 加载和切分
loader = TextLoader(file_path)
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
chunks = splitter.split_documents(docs)

# 3. 初始化 Embedding
embed = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    check_embedding_ctx_length=False,
    chunk_size=10
)

# 4. 创建向量库
print(">>> 正在构建向量数据库...")
db = Chroma.from_documents(
    documents=chunks,
    embedding=embed,
    persist_directory=persist_dir
)

# 5. 执行检索
query = "什么是 RAG？"
print(f"\n>>> 正在检索问题: {query}")

query_embedding = embed.embed_query(query)
# similarity_search 默认使用余弦相似度（对于归一化向量）或欧氏距离
# k=2 表示返回最相似的前 2 个结果
results = db.similarity_search_by_vector(query_embedding, k=2)

print(f"找到 {len(results)} 个相关文档：\n")
for i, doc in enumerate(results):
    print(f"--- Result {i+1} ---")
    print(f"[Content]: {doc.page_content}")
    print(f"[Metadata]: {doc.metadata}")
    print("-" * 30)
