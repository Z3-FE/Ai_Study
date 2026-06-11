import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader, UnstructuredMarkdownLoader

# 1. 构建目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.join(current_dir, "asset")

print(f"正在扫描目录: {target_dir}\n")

# 2. 初始化 DirectoryLoader
# 默认情况下，DirectoryLoader 使用 UnstructuredLoader 加载文件。
# 但我们可以通过 `loader_cls` 参数指定特定的加载器，
# 或者通过 `glob` 参数过滤特定的文件类型。

# 示例 A: 加载所有 .txt 文件，使用 TextLoader
print(">>> 示例 A: 加载所有 .txt 文件 (使用 TextLoader)")
txt_loader = DirectoryLoader(
    path=target_dir,
    glob="**/*.txt",      # 匹配模式：递归查找所有 txt 文件
    loader_cls=TextLoader # 指定使用 TextLoader 加载
)
txt_docs = txt_loader.load()
print(f"找到 {len(txt_docs)} 个 txt 文档")
for doc in txt_docs:
    print(f"- {doc.metadata['source']}")

print("-" * 30)

# 示例 B: 加载所有 .pdf 文件，使用 PyPDFLoader
print("\n>>> 示例 B: 加载所有 .pdf 文件 (使用 PyPDFLoader)")
pdf_loader = DirectoryLoader(
    path=target_dir,
    glob="**/*.pdf",
    loader_cls=PyPDFLoader
)
pdf_docs = pdf_loader.load()
print(f"找到 {len(pdf_docs)} 个 pdf 文档")
for doc in pdf_docs:
    print(f"- {doc.metadata['source']}")

print("-" * 30)

# 示例 C: 混合加载 (默认使用 UnstructuredLoader)
# 注意：这需要安装大量的依赖 (unstructured)，且速度较慢，通常建议指定 loader_cls
print("\n>>> 示例 C: 加载所有 .md 文件 (使用 UnstructuredMarkdownLoader)")
md_loader = DirectoryLoader(
    path=target_dir,
    glob="**/*.md",
    loader_cls=UnstructuredMarkdownLoader
)
try:
    md_docs = md_loader.load()
    print(f"找到 {len(md_docs)} 个 md 文档")
    for doc in md_docs:
        print(f"- {doc.metadata['source']}")
except Exception as e:
    print(f"Markdown 加载出错: {e}")
