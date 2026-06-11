"""
父子文档检索 (Parent-Child Retrieval) 示例
核心理念：
1. 检索时：使用小块（Child Chunks）进行向量匹配，因为小块语义更集中，匹配更准。
2. 生成时：返回大块（Parent Chunks）给 LLM，提供更完整的上下文信息。
"""
import os
import sys
import shutil
import uuid

from langchain_chroma import Chroma

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_core.stores import InMemoryStore
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_study.env_utils import MODEL_NAME, EMBEDDING_MODEL_NAME, API_KEY, BASE_URL

# 1. 配置路径与清理
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "asset/01_langchain_utf-8.txt")
persist_dir = os.path.join(current_dir, "asset/chroma-parent-child")

if os.path.exists(persist_dir):
    shutil.rmtree(persist_dir)

# 2. 初始化 Embedding 和 VectorStore
# VectorStore 只负责存 Child Chunks（小块）的向量
embed = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    check_embedding_ctx_length=False,
    chunk_size=10
)

vectorstore = Chroma(
    collection_name="split_parents",
    embedding_function=embed,
    persist_directory=persist_dir
)

# 3. 初始化 DocStore (文档存储)
# DocStore 负责存 Parent Chunks（大块）的原始内容
# 在生产环境中，这里通常使用 Redis 或 MongoDB，这里演示用内存存储
store = InMemoryStore()

# 4. 定义两个 Splitter
# Parent Splitter: 切分大块（比如 2000 字符），这是最终给 LLM 看的
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)

# Child Splitter: 切分小块（比如 200 字符），这是用来做向量检索的
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200)

# 5. 初始化 ParentDocumentRetriever
print(">>> 初始化 ParentDocumentRetriever...")
retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)

# 6. 加载并添加文档
print(f"正在加载文件: {file_path}")
loader = TextLoader(file_path)
docs = loader.load()

# add_documents 会自动做以下事情：
# 1. 用 parent_splitter 切分原始文档 -> 得到 Parents
# 2. 把 Parents 存入 docstore (InMemoryStore)
# 3. 用 child_splitter 把每个 Parent 切分成多个 Children
# 4. 把 Children 向量化并存入 vectorstore (Chroma)
# 5. 建立 Child -> Parent 的 ID 映射关系
print("正在处理并存入文档（这会自动生成父子切片）...")
retriever.add_documents(docs, ids=None)

# 7. 检索演示
query = "LangChain 有哪些组件？"
print(f"\n>>> 用户提问: {query}")

# 执行检索
# 注意：这里返回的将是 Parent Documents（大块），而不是匹配到的小块
retrieved_docs = retriever.invoke(query)

print(f"检索到了 {len(retrieved_docs)} 个父文档块：\n")
for i, doc in enumerate(retrieved_docs):
    print(f"--- Parent Document {i + 1} (Length: {len(doc.page_content)}) ---")
    print(doc.page_content)
    print("-" * 50)

print("\n【原理验证】")
print("虽然我们检索的是小块（准确度高），但返回的是大块（上下文全）。")
print("你可以看到返回的内容包含了完整上下文，而不仅仅是匹配到的那几句话。")
