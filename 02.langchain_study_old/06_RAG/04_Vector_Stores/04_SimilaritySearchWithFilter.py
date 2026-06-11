"""
Chroma 进阶检索：相似性检索 + 元数据过滤 (filter)
场景：当你只想在特定范围的文档中进行检索时（例如：只搜 '研发部' 的文档，或者只搜 'author=admin' 的文档）。
"""
import os
import sys
import shutil

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_community.document_loaders import CSVLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from langchain_study.env_utils import MODEL_NAME, EMBEDDING_MODEL_NAME, API_KEY, BASE_URL

# 1. 准备数据
# 为了演示过滤，我们需要给 Document 添加一些特定的 metadata
# 这里我们直接手动构造一些带有丰富 metadata 的 Document，比加载文件更直观
docs = [
    Document(
        page_content="张三是研发部的后端工程师，擅长 Python。",
        metadata={"department": "研发部", "role": "engineer", "year": 2023}
    ),
    Document(
        page_content="李四是研发部的前端工程师，擅长 React。",
        metadata={"department": "研发部", "role": "engineer", "year": 2022}
    ),
    Document(
        page_content="王五是市场部的销售经理，负责华东区。",
        metadata={"department": "市场部", "role": "manager", "year": 2023}
    ),
    Document(
        page_content="赵六是研发部的项目经理，负责进度管理。",
        metadata={"department": "研发部", "role": "manager", "year": 2021}
    ),
]

# 2. 初始化环境
persist_dir = os.path.join(os.path.dirname(__file__), "asset/chroma-filter-demo")
if os.path.exists(persist_dir):
    shutil.rmtree(persist_dir)

embed = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    check_embedding_ctx_length=False,
    chunk_size=10
)

# 3. 建库
print(">>> 正在构建带有元数据的向量库...")
db = Chroma.from_documents(
    documents=docs,
    embedding=embed,
    persist_directory=persist_dir
)

# 4. 场景演示

query = "谁懂技术？"

# --- 场景 A: 无过滤检索 ---
print(f"\n>>> 场景 A: 无过滤检索 '{query}'")
results_a = db.similarity_search(query, k=2)
for doc in results_a:
    print(f"- {doc.page_content} (Dept: {doc.metadata['department']})")

# --- 场景 B: 简单过滤 (只看研发部) ---
# filter 语法取决于底层向量库，Chroma 使用 MongoDB 风格的查询语法
print(f"\n>>> 场景 B: 过滤检索 '{query}' (仅限 研发部)")
results_b = db.similarity_search(
    query, 
    k=2,
    filter={"department": "研发部"} # 精确匹配
)
for doc in results_b:
    print(f"- {doc.page_content} (Dept: {doc.metadata['department']})")

# --- 场景 C: 组合过滤 (研发部 AND manager) ---
# Chroma 的 $and 操作符
print(f"\n>>> 场景 C: 组合过滤 '{query}' (研发部 且 是经理)")
results_c = db.similarity_search(
    query, 
    k=2,
    filter={
        "$and": [
            {"department": "研发部"},
            {"role": "manager"}
        ]
    }
)
for doc in results_c:
    print(f"- {doc.page_content} (Dept: {doc.metadata['department']}, Role: {doc.metadata['role']})")

# --- 场景 D: 范围过滤 (入职年份 >= 2022) ---
# Chroma 的 $gte (greater than or equal) 操作符
print(f"\n>>> 场景 D: 范围过滤 '{query}' (2022年及以后入职)")
results_d = db.similarity_search(
    query,
    k=2,
    filter={"year": {"$gte": 2022}}
)
for doc in results_d:
    print(f"- {doc.page_content} (Year: {doc.metadata['year']})")
