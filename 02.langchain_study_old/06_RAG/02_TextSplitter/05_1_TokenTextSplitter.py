import os
from langchain_text_splitters import TokenTextSplitter

# 1. 准备一段文本
# 这里的文本看起来不长，但对于 Tokenizer 来说，中文字符通常占用更多的 Token。
# 例如："你好" 在 OpenAI 的编码中可能占用 1-3 个 Token。
text = (
    "LangChain 是一个强大的框架。\n"
    "TokenTextSplitter 的作用是按照 LLM 的 Token 数量来切分文本，"
    "而不是按照字符数。这对于控制 API 成本和防止超出上下文窗口非常有用。\n"
    "OpenAI 的模型（如 GPT-3.5/4）使用 cl100k_base 编码器。"
)

print(f"原始文本字符数: {len(text)}")
print("-" * 30)

# 2. 初始化 TokenTextSplitter
# chunk_size=10: 每个块约 10 个 Token（这非常小，仅用于演示）
# chunk_overlap=0: 不重叠
# encoding_name: 指定编码器，默认通常是 "gpt2" 或 "p50k_base"，
# 对于 GPT-3.5/4 建议使用 "cl100k_base"。
splitter = TokenTextSplitter(
    chunk_size=10,
    chunk_overlap=0,
    encoding_name="cl100k_base" # OpenAI GPT-4 标准编码
)

# 3. 执行分割
docs = splitter.create_documents([text])

# 4. 打印结果
print(f"分割后得到 {len(docs)} 个文档块：\n")

for i, doc in enumerate(docs):
    print(f"--- Chunk {i+1} ---")
    print(f"[Content]: {doc.page_content}")
    # 我们可以简单估算一下字符数，你会发现字符数并不固定
    print(f"[Chars]: {len(doc.page_content)}")
    print("-" * 20)

print("\n【注意】")
print("TokenTextSplitter 依赖 `tiktoken` 库。")
print("它的切分点可能在单词中间，或者汉字的中间（如果一个汉字由多个 Token 组成）。")
print("它最适合用于严格限制 Token 数量的场景，而不是追求语义完整的场景。")
