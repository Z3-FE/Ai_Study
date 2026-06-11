"""
Chroma 进阶检索：使用 similarity_search_with_relevance_scores 余弦距离
与 similarity_search_with_score 的区别：
1. `with_score`: 返回原始距离（Distance），可能是 L2 或 Cosine Distance。
   - L2: 越小越好 [0, infinity]
   - Cosine Distance: 越小越好 [0, 2]
   
2. `with_relevance_scores`: 返回归一化的相关性分数（Relevance Score）。
   - 范围通常是 [0, 1]。
   - **分数越高越好**（1 表示完全匹配）。
   - LangChain 会尝试根据底层的距离公式自动将其转换为 0-1 的相似度。

注意：对于 Chroma，它默认使用 Cosine Distance，
LangChain 的 Chroma 实现会将 relevance_score 计算为 `1 - cosine_distance`。
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
persist_dir = os.path.join(current_dir, "asset/chroma-relevance-demo")

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

# 使用默认的 cosine 距离 (LangChain Chroma 默认就是 cosine)
# 这样 relevance_score = 1 - cosine_distance，正好符合 0~1 越高越好的直觉
print(">>> 正在构建向量库 (使用 Cosine 距离)...")
db = Chroma.from_documents(
    documents=chunks,
    embedding=embed,
    persist_directory=persist_dir,
    collection_metadata={"hnsw:space": "cosine"}
)

# 3. 带相关性分数的检索
# score_threshold: 可选参数，直接过滤掉分数低于阈值的结果
query = "什么是 RAG？"
print(f"\n>>> 正在检索问题: {query}")

# similarity_search_with_relevance_scores 返回 List[Tuple[Document, float]]
# 这里的 float 是相关性分数 (0~1, 越高越好)
results = db.similarity_search_with_relevance_scores(query, k=3, score_threshold=0.6)

if not results:
    print("没有找到符合阈值 (score > 0.6) 的结果。")
else:
    print(f"找到 {len(results)} 个结果 (按相关性分数排序，越大越相似)：\n")
    for i, (doc, score) in enumerate(results):
        print(f"--- Result {i + 1} (Relevance Score: {score:.4f}) ---")
        print(f"[Content]: {doc.page_content}")

        if score > 0.8:
            print(">>> 🌟 非常匹配")
        elif score > 0.7:
            print(">>> ✅ 比较匹配")
        else:
            print(">>> ⚠️ 勉强匹配")
        print("-" * 30)

# 4. 演示一个不相关的问题
query_bad = "如何做红烧肉？"
print(f"\n>>> 正在检索不相关问题: {query_bad}")
results_bad = db.similarity_search_with_relevance_scores(query_bad, k=3)

for i, (doc, score) in enumerate(results_bad):
    print(f"--- Bad Result {i + 1} (Score: {score:.4f}) ---")
    print(f"[Content]: {doc.page_content[:20]}...")
    # 你会发现这里的分数通常很低（例如 < 0.7 或 < 0.5）
