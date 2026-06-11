"""
Retriever 使用案例：MMR (Max Marginal Relevance) 多样性检索
场景：
当你的知识库中有很多相似内容（如重复的新闻、不同版本的文档）时，
普通的相似度检索可能会返回 Top-K 个几乎一样的结果。
MMR 检索器可以在“相关性”和“多样性”之间找到平衡，返回既相关又彼此不同的结果。
"""
import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from langchain_study.env_utils import MODEL_NAME, EMBEDDING_MODEL_NAME, API_KEY, BASE_URL

# 1. 准备数据：构造一组有大量重复/相似内容的文档
docs = [
    Document(page_content="Python 是一种流行的编程语言，适合数据分析。", metadata={"id": 1}),
    Document(page_content="Python 广泛应用于数据科学领域，非常流行。", metadata={"id": 2}), # 与 id:1 语义极度相似
    Document(page_content="Python 的语法简洁，易于学习。", metadata={"id": 3}),            # 语义不同
    Document(page_content="Java 是一种静态类型的编程语言。", metadata={"id": 4}),          # 不同的主题
    Document(page_content="Python 在人工智能领域有统治地位。", metadata={"id": 5}),          # 语义不同
]

# 2. 初始化 Embedding
embed = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    check_embedding_ctx_length=False,
    chunk_size=10
)

# 3. 构建索引
print(">>> 正在构建向量索引...")
db = FAISS.from_documents(docs, embed)

# 4. 创建 MMR 检索器
# search_type="mmr"
# lambda_mult: 0~1，越小越多祥，越大越相关 (0.5 是默认平衡点)
# fetch_k: 初始召回数量，比如先找 20 个，再从中选 k 个最多样化的
print(">>> 正在创建 MMR 检索器 (lambda=0.25, 偏向多样性)...")
retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 2,              # 最终返回 2 个结果
        "fetch_k": 4,        # 从 4 个候选中挑选
        "lambda_mult": 0.25  # 这是一个较低的值，表示强烈倾向于多样性
    }
)

query = "Python 有什么特点？"
print(f"\n>>> 检索问题: {query}")

# 5. 执行检索
results = retriever.invoke(query)

print(f"找到 {len(results)} 个结果：\n")
for i, doc in enumerate(results):
    print(f"Result {i+1} [ID:{doc.metadata['id']}]: {doc.page_content}")

print("\n【结果分析】")
print("如果使用普通检索，可能会返回 ID:1 和 ID:2，因为它们最相似。")
print("使用 MMR 后，检索器会发现 ID:2 和 ID:1 太像了，所以会跳过 ID:2，")
print("转而选择 ID:3 或 ID:5 这样既相关又不一样的内容。")
