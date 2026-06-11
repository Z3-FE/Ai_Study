import os
import sys
from langchain_community.document_loaders import JSONLoader

# 1. 构建文件路径
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "asset", "projects.json")

print(f"正在加载文件: {file_path}")

# 2. 定义提取数据的 jq schema
# '.' 表示根元素（如果根是列表，则遍历列表中的每个对象）
# 这里的 jq_schema 意味着我们将提取 JSON 数组中的每个对象作为单独的文档
# 如果你想提取特定的字段，比如 'details' 下的内容，可以写成 '.[] .details'
jq_schema = '.'

# 3. 初始化加载器
# content_key: 可选，指定从 JSON 对象中提取哪个字段作为 page_content。
# 如果不指定，整个 JSON 对象将作为 content。
loader = JSONLoader(
    file_path=file_path,
    jq_schema=jq_schema,
    text_content=False  # 设置为 False 表示我们加载的是结构化数据（字典/列表），而不是纯文本字符串
)

# 4. 加载数据
try:
    docs = loader.load()
    print(docs)
    print(f"成功加载 {len(docs)} 条记录\n")

    for i, doc in enumerate(docs):
        print(f"--- 记录 {i + 1} ---")
        print(f"[Content]:\n{doc.page_content}")
        print(f"[Metadata]: {doc.metadata}")
        print("-" * 30)

except Exception as e:
    print(f"加载出错: {e}")
    print("提示: JSONLoader 依赖 'jq' 包。请确保已运行 `poetry add jq` 安装依赖。")

# 5. 单独取某一个字段的值

loader2 = JSONLoader(
    file_path=file_path,
    jq_schema=".[].details.deadline",
    text_content=False
)

docs2 = loader2.load()

print(docs2)
for i, doc in enumerate(docs2):
    print(doc.page_content)
