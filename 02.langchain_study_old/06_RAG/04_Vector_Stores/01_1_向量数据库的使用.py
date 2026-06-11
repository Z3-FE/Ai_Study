"""
chorma 向量数据库
"""
import os
import sys
import shutil

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import TextSplitter, CharacterTextSplitter, RecursiveCharacterTextSplitter
from posthog import api_key

from langchain_study.env_utils import MODEL_NAME, EMBEDDING_MODEL_NAME, API_KEY, BASE_URL

# 1. 构建绝对路径（建议）
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "asset/01_langchain_utf-8.txt")
persist_dir = os.path.join(current_dir, "asset/chroma-1")

# --- 关键逻辑：初始化前检查 ---
# 如果您是想“演示”或“重新构建”数据库，那么应该先清理旧数据。
# 如果您是想“增量更新”，则不需要删除。
if os.path.exists(persist_dir):
    print(f"检测到旧的向量数据库: {persist_dir}，正在清理以避免重复...")
    shutil.rmtree(persist_dir)  # 递归删除文件夹
    print("清理完成。\n")

loader = TextLoader(
    file_path=file_path
)

doc = loader.load()

text_split = RecursiveCharacterTextSplitter(
    chunk_size=50, chunk_overlap=5,
)

chunks = text_split.split_documents(doc)

"""
check_embedding_ctx_length:
 DashScope（阿里）的兼容接口，而不是原生的 OpenAI，
 且之前遇到过本地 Tokenizer 的问题，所以设置为 False 是为了 
 跳过本地校验，直接由服务端处理 ，这是一个兼容性更好的做法。
"""
# DashScope (阿里) 的 Embedding API 限制每批次最多 25 条 (有些模型是 10 条)
# 所以我们需要设置 chunk_size (批处理大小) 小一点，OpenAIEmbeddings 默认是 1000。
embed = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    check_embedding_ctx_length=False,
    chunk_size=10  # 关键修正：将批处理大小限制为 10
)

"""在向量数据库中不仅存储了转换后的向量数据，也存储了文档"""
# 此时因为 persist_directory 被清空了（或者不存在），Chroma 会创建一个新的
db = Chroma.from_documents(
    documents=chunks,
    embedding=embed,
    persist_directory=persist_dir,  # 恢复持久化路径
)

# 可选：显式调用 persist() 确保保存（虽然新版 Chroma 会自动保存，但加上更保险）
# db.persist() 

dataMessage = db.similarity_search(query="“LangChain 有哪些组件？”")

print(dataMessage)
print("-" * 100)
print(len(dataMessage))

for (i, chunk) in enumerate(dataMessage):
    print('记录切片', i)
    print(chunk.page_content)
    print("-" * 100)
