import os
from langchain_community.document_loaders import UnstructuredHTMLLoader

# 1. 构建文件路径
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "asset", "sample.html")

print(f"正在加载 HTML 文件: {file_path}")

# 2. 初始化加载器
# UnstructuredHTMLLoader 使用 unstructured 库解析 HTML
# mode="single" (默认): 将整个 HTML 文件加载为一个 Document。
# mode="elements": 将 HTML 拆分为多个 Document（例如每个段落、标题作为一个 Document）。
# mode="paged": (仅某些 Loader 支持) 按页拆分。
loader = UnstructuredHTMLLoader(file_path, mode="elements")

# 3. 加载数据
try:
    docs = loader.load()

    # 4. 打印结果
    print(f"成功加载 {len(docs)} 个文档\n")

    for i, doc in enumerate(docs):
        print(f"--- Document {i+1} ---")
        print(f"[Content]:\n{doc.page_content}")
        print(f"[Metadata]: {doc.metadata}")
        print("-" * 30)
except Exception as e:
    print(f"加载出错: {e}")
    # 特别针对 NLTK 权限问题的友好提示
    if "PermissionError" in str(e) and "nltk_data" in str(e):
        print("\n>>> 检测到 NLTK 权限问题 <<<")
        print("这通常是因为 Python 试图写入受保护的系统目录。")
        print("请尝试手动设置 NLTK 数据目录到用户目录下，例如：")
        print("import nltk")
        print("nltk.data.path.append('/Users/z523/nltk_data_local')")
