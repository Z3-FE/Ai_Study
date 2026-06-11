"UniversalProcessor : 通用处理方法"
import os
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    TextLoader,
    CSVLoader,
    JSONLoader,
    UnstructuredExcelLoader
)


class UniversalDocumentProcessor:
    """
    通用文档处理器：自动加载并分割多种格式的文件
    """

    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 1. 注册 Loader (文件后缀 -> Loader类)
        self.loader_map = {
            ".pdf": PyPDFLoader,
            ".md": UnstructuredMarkdownLoader,
            ".html": UnstructuredHTMLLoader,
            ".htm": UnstructuredHTMLLoader,
            ".txt": TextLoader,
            ".csv": CSVLoader,
            ".json": self._create_json_loader,  # 特殊处理
            ".xlsx": UnstructuredExcelLoader,
            ".xls": UnstructuredExcelLoader
        }

        # 2. 注册 Splitter 策略 (文件后缀 -> Language枚举)
        # 如果不在这个表中，将使用默认的通用分割器
        self.language_map = {
            ".py": Language.PYTHON,
            ".js": Language.JS,
            ".ts": Language.TS,
            ".md": Language.MARKDOWN,
            ".html": Language.HTML,
            ".htm": Language.HTML,
        }

    def _create_json_loader(self, file_path):
        """JSONLoader 需要特殊参数"""
        return JSONLoader(file_path, jq_schema=".", text_content=False)

    def process_file(self, file_path: str) -> List[Document]:
        """
        核心方法：给定文件路径，自动加载并分割
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # --- 步骤 1: 加载 (Load) ---
        print(f"\n>>> 处理文件: {file_path} (类型: {ext})")
        loader_cls = self.loader_map.get(ext)

        docs = []
        if loader_cls:
            try:
                # 处理 JSONLoader 的特殊工厂方法情况
                if ext == ".json":
                    loader = self._create_json_loader(file_path)
                else:
                    loader = loader_cls(file_path)

                print(f"使用加载器: {loader.__class__.__name__}")
                docs = loader.load()
                print(f"加载成功，原始文档数: {len(docs)}")
            except Exception as e:
                print(f"加载失败: {e}")
                return []
        else:
            # 尝试作为纯文本加载
            print("未找到专用加载器，尝试作为纯文本加载...")
            try:
                loader = TextLoader(file_path)
                docs = loader.load()
            except Exception as e:
                print(f"纯文本加载也失败了: {e}")
                return []

        # --- 步骤 2: 分割 (Split) ---
        if not docs:
            return []

        # 根据文件类型选择最佳分割策略
        language = self.language_map.get(ext)

        if language:
            print(f"应用 {language} 专用分割策略...")
            splitter = RecursiveCharacterTextSplitter.from_language(
                language=language,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        else:
            print("应用通用文本分割策略...")
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", " ", ""]
            )

        # 执行分割
        final_docs = splitter.split_documents(docs)
        print(f"分割完成，生成块数: {len(final_docs)}")

        return final_docs


# --- 测试代码 ---
if __name__ == "__main__":
    # 假设我们有一些测试文件在 asset 目录下
    # 这里我们直接复用之前创建的文件进行测试

    processor = UniversalDocumentProcessor(chunk_size=100, chunk_overlap=0)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    asset_dir = os.path.join(current_dir, "./asset")

    # 测试文件列表
    test_files = [
        "guide.md",
        "sample.html",
        "employees.csv",
        "个人简历.pdf"  # 注意：PDF加载需要 pypdf 库
    ]

    for filename in test_files:
        file_path = os.path.join(asset_dir, filename)
        if os.path.exists(file_path):
            result_docs = processor.process_file(file_path)
            # 打印前2个块作为示例
            for i, doc in enumerate(result_docs[:2]):
                print(f"  [Chunk {i + 1}]: {doc.page_content[:50]}...")
        else:
            print(f"\n跳过测试 (文件不存在): {file_path}")
