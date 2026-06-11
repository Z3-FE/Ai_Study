from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 准备一段复杂的文本
# 这段文本包含了双换行（段落）、单换行（行）、句子和单词结构
text = (
    "LangChain RAG 系统教程\n\n"
    "第一章：简介\n"
    "RAG (Retrieval-Augmented Generation) 是一种技术，它结合了检索和生成的能力。"
    "它允许模型访问外部知识库，从而减少幻觉并提供最新信息。\n\n"
    "第二章：文本分割 (Text Splitting)\n"
    "为什么需要分割？\n"
    "1. LLM 有上下文窗口限制。\n"
    "2. 较小的块通常意味着更精准的语义检索。\n\n"
    "RecursiveCharacterTextSplitter 是最常用的分割器。它按顺序尝试分割符，"
    "默认列表是 [\"\\n\\n\", \"\\n\", \" \", \"\"]。这意味着它会优先保持段落完整，"
    "如果段落太长，再尝试按行切分，依此类推。"
)

print(f"原始文本长度: {len(text)}")
print("-" * 30)

# 2. 初始化 RecursiveCharacterTextSplitter
# 这是 LangChain 默认推荐的分割器
splitter = RecursiveCharacterTextSplitter(
    chunk_size=50,  # 设定较小的块大小以观察递归效果 (chunk_size的优先级更高一些)
    chunk_overlap=10,  # 重叠部分
    # separators=["\n\n", "\n", " ", ""], # 这是默认值，您可以自定义
    length_function=len,
    is_separator_regex=False
)

# 3. 执行分割
docs = splitter.create_documents([text])

# 4. 打印结果
print(f"分割后得到 {len(docs)} 个文档块：\n")

for i, doc in enumerate(docs):
    print(f"--- Chunk {i + 1} (Length: {len(doc.page_content)}) ---")
    print(f"'{doc.page_content}'")
    print("-" * 20)

print("\n【总结】")
print("观察上面的结果，你会发现它优先在 '段落' (\\n\\n) 处切分。")
print("当遇到 '第二章...' 这样较长的段落时，它会自动降级使用 '\\n' 或空格进行切分，")
print("以确保每个块不超过 chunk_size (50)。")
