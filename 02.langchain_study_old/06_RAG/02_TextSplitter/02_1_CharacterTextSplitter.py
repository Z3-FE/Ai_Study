from langchain_text_splitters import CharacterTextSplitter

# 1. 准备长文本
# 这是一个包含多个段落的长字符串，用于演示分割
text = (
    "LangChain 是一个用于开发由语言模型驱动的应用程序的框架。\n\n"
    "核心功能：\n"
    "1. 数据感知：能够将语言模型连接到其他数据源。\n"
    "2. 代理能力：允许语言模型与其环境进行交互。\n\n"
    "02_TextSplitter 的作用是将长文本切分成更小的块（Chunks），"
    "以便能够放入 LLM 的上下文窗口中。"
)

print(f"原始文本长度: {len(text)}")
print("-" * 30)

# 2. 初始化 CharacterTextSplitter
# separator: 分割符。默认是 "\n\n"。它会尝试先用这个符号切分。
# chunk_size: 每个块的最大字符数。
# chunk_overlap: 块之间的重叠字符数，用于保持上下文连贯性。
splitter = CharacterTextSplitter(
    separator="\n",  # 指定换行符作为分割点 (分割标识优先原则，可能导致chunk_size超出长度)
    chunk_size=50,  # 每个块尽量不超过 50 个字符
    chunk_overlap=5,  # 相邻块之间重叠 5 个字符
    length_function=len,  # 计算长度的函数，默认是 len
    keep_separator=True,  # 是否保留分隔符
    is_separator_regex=False  # separator 是否为正则表达式
)

# 3.1 执行分割
docs = splitter.split_text(text)
print(docs)

for doc in enumerate(docs):
    print(doc)
print("-" * 30)

# 3.2 执行分割
# (推荐
# 标准化流程 : 在 RAG（检索增强生成）流程中，向量数据库（VectorStore）通常期望接收 Document 对象，而不是纯字符串。
# 使用 create_documents 可以一步到位。)


# create_documents 会返回 Document 对象列表
docs = splitter.create_documents([text])

print(docs)
# 4. 打印结果
print(f"分割后得到 {len(docs)} 个文档块：\n")

for i, doc in enumerate(docs):
    print(f"--- Chunk {i + 1} (Length: {len(doc.page_content)}) ---")
    print(f"'{doc.page_content}'")
    print("-" * 20)
