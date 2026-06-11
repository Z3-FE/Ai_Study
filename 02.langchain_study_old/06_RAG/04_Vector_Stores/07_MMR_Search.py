"""
Chroma 进阶检索：Max Marginal Relevance (MMR) 多样性检索
场景：
普通的相似度检索（Similarity Search）倾向于返回内容非常接近的文档（可能都是同一句话的重复或微小变体）。
MMR 算法试图在“与查询的相关性”和“结果之间的多样性”之间找到平衡。
它会先检索出 k*fetch_k 个文档，然后从中选出 k 个既相关又彼此不雷同的结果。
"""
import os
import sys
import shutil

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from langchain_study.env_utils import MODEL_NAME, EMBEDDING_MODEL_NAME, API_KEY, BASE_URL

# 1. 构造一个容易出现“重复结果”的数据集
# 假设我们有关于“苹果”的几句话，其中两句非常相似，一句不同
docs = [
    Document(page_content="苹果富含维生素C，是一种非常健康的水果。", metadata={"id": 1}),
    Document(page_content="苹果含有大量的维他命C，对身体健康很有好处。", metadata={"id": 2}),  # 与 id:1 语义极度相似
    Document(page_content="苹果公司发布了最新的 iPhone 15。", metadata={"id": 3}),  # 语义不同
    Document(page_content="每天吃一个苹果，医生远离我。", metadata={"id": 4}),  # 语义略有不同
    Document(page_content="香蕉也是一种富含钾元素的水果。", metadata={"id": 5}),  # 完全不同的水果
]

# 2. 初始化环境
persist_dir = os.path.join(os.path.dirname(__file__), "asset/chroma-mmr-demo")
if os.path.exists(persist_dir):
    shutil.rmtree(persist_dir)

embed = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    check_embedding_ctx_length=False,
    chunk_size=10
)

print(">>> 正在构建向量库...")
db = Chroma.from_documents(
    documents=docs,
    embedding=embed,
    persist_directory=persist_dir
)

query = "苹果有什么好处？"
print(f"\n>>> 查询问题: {query}")

# --- 对比 A: 普通相似度检索 ---
print("\n--- A. 普通 Similarity Search (k=2) ---")
# 可能会返回 id:1 和 id:2，因为它们最相似，但内容几乎一样
results_sim = db.similarity_search(query, k=2)
for doc in results_sim:
    print(f"[ID:{doc.metadata['id']}] {doc.page_content}")

# --- 对比 B: MMR 多样性检索 ---
print("\n--- B. MMR Search (k=2, lambda=0.5) ---")
# lambda_mult: 多样性因子 (0~1)
#   - 1.0 = 完全等同于普通相似度检索（只看相关性）
#   - 0.0 = 最大化多样性（甚至可能选出不相关的，只要它跟已选的不一样）
#   - 0.5 = 平衡（默认值）
results_mmr = db.max_marginal_relevance_search(
    query,
    k=2,
    fetch_k=4,  # 初始候选池大小（从这4个里选2个）
    lambda_mult=0.3  # 调低 lambda 以鼓励更多样性
)
for doc in results_mmr:
    print(f"[ID:{doc.metadata['id']}] {doc.page_content}")

print("\n【结论】")
print("普通检索容易返回 [ID:1] 和 [ID:2]，因为它们都讲'维生素C'，语义极近。")
print("MMR 检索更有可能返回 [ID:1] 和 [ID:4] 或 [ID:3]，因为它发现 ID:2 和 ID:1 太像了，会惩罚它的分数。")
