"""
FAISS (Facebook AI Similarity Search) 检索器使用案例
FAISS 是目前最快的向量检索库之一，特别适合大规模数据。
注意：FAISS 默认是内存数据库，如果需要持久化，需要手动 save_local 和 load_local。
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
# 这样可以使用标准的 invoke 接口，并方便集成到 Chain 中
# 默认是相似性检索similarity
print(">>> 正在将 FAISS 转换为 Retriever...")
retriever = db.as_retriever(search_kwargs={"k": 2})  # 返回前两条

query = "FAISS 是什么？"
print(f"\n>>> 检索问题: {query}")

# 使用 invoke 方法进行检索
results = retriever.invoke(query)

for i, doc in enumerate(results):
    print(f"Result {i + 1}: {doc.page_content}")

# 5. 持久化保存 (Save)
save_path = os.path.join(os.path.dirname(__file__), "faiss_index")
print(f"\n>>> 保存索引到: {save_path}")
db.save_local(save_path)

# 6. 加载索引 (Load)
print(">>> 重新加载索引...")
# allow_dangerous_deserialization=True 是为了防止反序列化漏洞，
# 对于自己保存的索引是安全的。
new_db = FAISS.load_local(
    save_path,
    embed,
    allow_dangerous_deserialization=True
)

# 7. 再次检索验证
print("\n>>> 验证加载后的检索 (使用 invoke):")
# 同样转换为 Retriever
new_retriever = new_db.as_retriever(search_kwargs={"k": 1})
results_new = new_retriever.invoke("LangChain 和 FAISS 的关系")
print(f"Result: {results_new[0].page_content}")
