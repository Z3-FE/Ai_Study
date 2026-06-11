"""
Chroma 进阶检索：基于 L2 (欧氏距离) 的分数检索
Chroma 默认使用 L2 距离（Euclidean Distance）或 Cosine Similarity（余弦相似度）。
注意：对于归一化的向量，L2 距离和余弦相似度是单调相关的。

similarity_search_with_score 会返回 (Document, score) 的元组。
- 如果使用 L2 距离：分数越低越好（0 表示完全一样）。
- 如果使用 Cosine 距离：分数越低越好（通常 Chroma 返回的是 1 - cosine_similarity）。
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

# 1. 准备数据
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "asset/01_langchain_utf-8.txt")
persist_dir = os.path.join(current_dir, "asset/chroma-score-demo")

if os.path.exists(persist_dir):
    shutil.rmtree(persist_dir)

# 2. 建库
loader = TextLoader(file_path)
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
chunks = splitter.split_documents(docs)

embed = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    check_embedding_ctx_length=False,
    chunk_size=10
)

# collection_metadata={"hnsw:space": "l2"} 显式指定使用 L2 距离
# 可选值: "l2" (欧氏距离), "cosine" (余弦距离), "ip" (内积)
print(">>> 正在构建向量库 (使用 L2 距离)...")
db = Chroma.from_documents(
    documents=chunks,
    embedding=embed,
    persist_directory=persist_dir,
    collection_metadata={"hnsw:space": "l2"}
)

# 3. 带分数的检索
query = "什么是 RAG？"
print(f"\n>>> 正在检索问题: {query}")

# similarity_search_with_score 返回 List[Tuple[Document, float]]
results_with_score = db.similarity_search_with_score(query, k=3)

print(f"找到 {len(results_with_score)} 个结果 (按 L2 距离排序，越小越相似)：\n")

for i, (doc, score) in enumerate(results_with_score):
    print(f"--- Result {i + 1} (Score: {score:.4f}) ---")
    print(f"[Content]: {doc.page_content}")

    # 简单的阈值判断演示
    if score < 0.4:
        print(">>> 匹配度很高")
    elif score < 0.8:
        print(">>> 匹配度一般")
    else:
        print(">>> 匹配度较低")
    print("-" * 30)
