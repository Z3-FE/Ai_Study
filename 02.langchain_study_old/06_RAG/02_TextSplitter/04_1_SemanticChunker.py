import os
import sys

# 将项目根目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_study.env_utils import API_KEY, BASE_URL, EMBEDDING_MODEL_NAME

# 1. 准备一段长文本（包含多个不同的话题）
# 这段文本前半部分讲 LangChain，后半部分突然跳到了“如何做红烧肉”。
# 传统的固定字符切分可能会把这两个完全不同的话题切在同一个块里，或者把一个话题切断。
text = """
LangChain 是一个强大的框架，旨在帮助开发人员构建端到端的语言模型应用。它提供了一套工具、组件和接口，
可以简化创建由大型语言模型 (LLM) 和聊天模型提供支持的应用程序的过程。LangChain 可以轻松管理与语言模型的交互，
将多个组件链接在一起，并集成额外的资源，例如 API 和数据库。

红烧肉是一道著名的中国菜，以其肥而不腻、入口即化而闻名。
制作红烧肉的主要原料是五花肉。首先将五花肉切成方块，冷水下锅焯水去腥。
然后炒糖色，加入葱姜蒜八角桂皮等香料煸炒，最后加入生抽老抽和水，小火慢炖一个小时以上。
收汁后即可出锅，色泽红亮，香气扑鼻。
"""

# 2. 初始化 Embeddings
# SemanticChunker 需要理解文本的含义，所以必须依赖 Embeddings 模型
embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    api_key=API_KEY,
    # api_base=BASE_URL,
    check_embedding_ctx_length=False
)

print(f"Model Name: {EMBEDDING_MODEL_NAME}")

# 3. 初始化 SemanticChunker (语义分割器)
# breakpoint_threshold_type: 决定如何判断语义突变
#   - "percentile": 根据所有句子相似度的百分位数（如 95%）来切分
#   - "standard_deviation": 根据标准差切分
#   - "interquartile": 根据四分位距切分
semantic_splitter = SemanticChunker(
    embeddings,
    breakpoint_threshold_type="percentile",  # 默认模式，适合大多数情况
    # breakpoint_threshold_amount=25.0 , 越小拆的越多
)

# 4. 执行分割
print(">>> 开始进行语义分割...")
docs = semantic_splitter.create_documents([text])

# 5. 打印结果
print(f"分割后得到 {len(docs)} 个文档块：\n")

for i, doc in enumerate(docs):
    print(f"--- Chunk {i + 1} ---")
    print(doc.page_content)
    print("-" * 30)

print("\n【总结】")
print("SemanticChunker 会自动检测到 'LangChain介绍' 和 '红烧肉做法' 是两个语义完全不同的话题，")
print("并在它们之间进行切分，而不是机械地按照 50 或 100 个字符切分。")
print("这对于 RAG 检索非常重要，因为我们不希望检索 '编程框架' 时召回 '红烧肉' 的内容。")
