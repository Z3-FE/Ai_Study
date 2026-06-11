"""
CSV 加载 -> Token 切分 -> Chroma 存储与检索
"""
import os
import sys
import shutil

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_community.document_loaders import CSVLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import TokenTextSplitter

from langchain_study.env_utils import MODEL_NAME, EMBEDDING_MODEL_NAME, API_KEY, BASE_URL

# 1. 构建路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 假设 employees.csv 在 asset 目录下
file_path = os.path.join(current_dir, "asset/employees.csv")
persist_dir = os.path.join(current_dir, "asset/chroma-csv")

# 2. 清理旧数据库 (避免重复数据)
if os.path.exists(persist_dir):
    print(f"检测到旧的向量数据库: {persist_dir}，正在清理...")
    shutil.rmtree(persist_dir)
    print("清理完成。\n")

# 3. 加载 CSV 并初步切分 (使用 loader 默认的切分逻辑)
print(f"正在加载 CSV 文件: {file_path}")
loader = CSVLoader(
    file_path=file_path,
    source_column="name",
    encoding="utf-8"
)

# load_and_split() 默认使用 RecursiveCharacterTextSplitter 进行切分
# 这里我们可以传入一个自定义的 splitter，但为了演示“两步切分”，我们先让它用默认的切一下
print(">>> 第一步：使用 loader.load_and_split() 进行初步切分")
initial_docs = loader.load_and_split()
print(f"第一步切分后得到 Document 数量: {len(initial_docs)}")

# 4. 使用 TokenTextSplitter 进行二次切分
print("\n>>> 第二步：使用 TokenTextSplitter 进行二次切分")
token_splitter = TokenTextSplitter(
    chunk_size=50,  # 每个块最多 50 个 Token
    chunk_overlap=0,  # 不重叠
    encoding_name="cl100k_base"
)

final_docs = token_splitter.split_documents(initial_docs)
print(f"第二步切分后得到 Document 数量: {len(final_docs)}")

# 5. 初始化 Embedding
embed = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    check_embedding_ctx_length=False,
    chunk_size=10
)

# 6. 存入 Chroma 数据库
print("\n正在存入 Chroma 向量数据库...")
db = Chroma.from_documents(
    documents=final_docs,
    embedding=embed,
    persist_directory=persist_dir
)
print("存储完成。\n")

# 7. 执行检索测试
query = "谁在研发部工作？"
print(f"正在检索问题: {query}")
results = db.similarity_search(query, k=2) # k 表示返回前 k 个结果

print("-" * 50)
for i, doc in enumerate(results):
    print(f"结果 {i + 1}:")
    print(f"[Content]: {doc.page_content}")
    print(f"[Source]: {doc.metadata.get('source')}")
    print("-" * 50)
