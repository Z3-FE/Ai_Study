from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

# 1. Python 代码案例
print(">>> 案例 1: Python 代码分割")
python_code = """
def hello_world():
    print("Hello, World!")

class MyClass:
    def __init__(self):
        self.value = 10

    def process(self):
        if self.value > 5:
            return True
        return False
"""

# 使用 from_language 方法，会自动配置适合 Python 的分隔符
# (如 class, def, \n 等)
python_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON,
    chunk_size=50,
    chunk_overlap=0
)
python_docs = python_splitter.create_documents([python_code])

for i, doc in enumerate(python_docs):
    print(f"--- Python Chunk {i+1} ---")
    print(doc.page_content)
print("-" * 30)


# 2. Markdown 案例
print("\n>>> 案例 2: Markdown 文档分割")
markdown_text = """
# LangChain 教程

## 核心模块
LangChain 包含多个核心模块。

### 1. Models
模型是基础组件。

### 2. Prompts
提示词工程很重要。

## 总结
这是一个很棒的框架。
"""

md_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.MARKDOWN,
    chunk_size=40,
    chunk_overlap=0
)
md_docs = md_splitter.create_documents([markdown_text])

for i, doc in enumerate(md_docs):
    print(f"--- Markdown Chunk {i+1} ---")
    print(doc.page_content)
print("-" * 30)


# 3. HTML 案例 (虽然通常用 HTML Loader，但这里演示纯文本切分)
print("\n>>> 案例 3: HTML 代码分割")
html_text = """
<!DOCTYPE html>
<html>
<body>
    <div>
        <h1>我的标题</h1>
        <p>这是一个段落。</p>
        <p>这是另一个段落。</p>
    </div>
</body>
</html>
"""

html_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.HTML,
    chunk_size=50,
    chunk_overlap=0
)
html_docs = html_splitter.create_documents([html_text])

for i, doc in enumerate(html_docs):
    print(f"--- HTML Chunk {i+1} ---")
    print(doc.page_content)
