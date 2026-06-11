"""
Retriever 使用案例：基于分数阈值的检索 (Similarity Score Threshold)
场景：
有时候我们不希望返回任何结果，除非它们与查询足够相关。
设置 score_threshold 可以过滤掉低质量的匹配项，避免模型产生幻觉。
注意：score_threshold (0~1) 越高表示要求越严格。
"""
import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from langchain_study.env_utils import MODEL_NAME, EMBEDDING_MODEL_NAME, API_KEY, BASE_URL

# 1. 准备数据
docs = [
    Document(page_content="FAISS 是由 Facebook AI Research 开发的高效相似性搜索库。", metadata={"source": "wiki"}),
    Document(page_content="它能够快速搜索包含数十亿个向量的数据集。", metadata={"source": "wiki"}),
    Document(page_content="LangChain 提供了对 FAISS 的封装，使其易于集成。", metadata={"source": "docs"}),
    Document(page_content="与 Chroma 不同，FAISS 需要显式保存和加载索引。", metadata={"source": "note"}),
]

# 2. 初始化 Embedding
embed = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    check_embedding_ctx_length=False,
    chunk_size=10
)

# 3. 构建 FAISS 索引 (内存中)
print(">>> 正在构建 FAISS 索引...")
db = FAISS.from_documents(docs, embed)

# 4. 执行检索
# 推荐模式：将 VectorStore 转换为 Retriever
# search_type="similarity_score_threshold" 需要底层支持 relevance_score
# 对于 FAISS，通常需要使用 L2 距离转换为相似度
# 注意：score_threshold 的范围是 0~1，越高越严格
print(">>> 正在将 FAISS 转换为 Retriever (阈值 0.8)...")
retriever = db.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.8}
)

query = "FAISS 是什么？"
print(f"\n>>> 检索问题: {query}")

# --- 调试：查看原始分数 ---
print("--- Debug: 查看原始分数 ---")
# as_retriever 返回的是标准的 VectorStoreRetriever，它 invoke 的结果默认只包含 Document
# 如果想看分数，不能直接用 invoke，或者需要 Hack 一下。
# 
# 但作为替代，我们可以直接调用 vectorstore 的带分数的检索方法来“调试”看看分数是多少
# 这里的 search_type 对应的方法是 similarity_search_with_relevance_scores
raw_results = db.similarity_search_with_relevance_scores(query, k=4)
for doc, score in raw_results:
    print(f"[Score: {score:.4f}] {doc.page_content}")
print("-" * 30)
# ------------------------

# 使用 invoke 方法进行检索
try:
    results = retriever.invoke(query)
    print(f"\n>>> Retriever.invoke 最终返回 {len(results)} 个结果：")
    for i, doc in enumerate(results):
        print(f"Result {i + 1}: {doc.page_content}")
except Exception as e:
    print(f"检索出错: {e}")

# --- 验证测试 ---
print("\n>>> 验证测试: 使用一个完全不相关的问题")
query_bad = "如何做西红柿炒鸡蛋？"
print(f"检索问题: {query_bad}")
results_bad = retriever.invoke(query_bad)

if not results_bad:
    print("✅ 验证成功：没有返回结果，说明阈值生效了（低分结果被过滤）。")
else:
    print(f"❌ 验证失败：返回了 {len(results_bad)} 个结果（说明没过滤掉）：")
    for doc in results_bad:
        print(f"- {doc.page_content}")
