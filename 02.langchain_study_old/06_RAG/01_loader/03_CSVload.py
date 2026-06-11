import os
from langchain_community.document_loaders import CSVLoader

# 1. 构建文件路径
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "asset", "employees.csv")

print(f"正在加载文件: {file_path}")

# 2. 初始化加载器
# source_column 参数可选，用于指定哪一列作为 metadata 中的 'source'，
# 如果不指定，默认 'source' 是文件路径。
loader = CSVLoader(
    file_path=file_path,
    source_column="name",  # 将 'name' 列作为源标识 ， [Metadata]: {'source': '张三', 'row': 0}
    encoding="utf-8"  # 指定编码，防止中文乱码
)

# 3. 加载数据
docs = loader.load()

# 4. 打印结果
print(f"成功加载 {len(docs)} 条记录\n")

for i, doc in enumerate(docs):
    print(f"--- 记录 {i + 1} ---")
    print(f"[Content]:\n{doc.page_content}")
    print(f"[Metadata]: {doc.metadata}")
    print("-" * 30)
