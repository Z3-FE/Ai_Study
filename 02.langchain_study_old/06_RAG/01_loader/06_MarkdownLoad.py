import os
from langchain_community.document_loaders import UnstructuredMarkdownLoader, DirectoryLoader
from langchain_text_splitters import TextSplitter

# 1. 构建文件路径
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "asset", "guide.md")

print(f"正在加载 Markdown 文件: {file_path}")

# 2. 初始化加载器
# UnstructuredMarkdownLoader 可以很好地处理 Markdown 结构
# mode="elements" 会将文档拆分成不同的元素（如标题、段落、列表项），
# mode="single" (默认) 会将整个文档加载为一个 Document。
loader = UnstructuredMarkdownLoader(
    file_path,
    mode="single"  # 尝试改为 "elements" 看看效果
)

# 3. 加载数据
try:
    docs = loader.load()
    print(f"成功加载 {len(docs)} 个文档\n")

    for i, doc in enumerate(docs):
        print(f"--- Document {i + 1} ---")
        # 截取前 200 个字符避免输出太长
        preview = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
        print(f"[Content Preview]:\n{preview}")
        print(f"[Metadata]: {doc.metadata}")
        print("-" * 30)

except Exception as e:
    print(f"加载出错: {e}")
    print("提示：UnstructuredMarkdownLoader 依赖 'unstructured' 和 'markdown'。")
    print("请运行: poetry add unstructured markdown")
