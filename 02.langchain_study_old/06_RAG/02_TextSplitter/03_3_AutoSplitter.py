import os
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

class AutoTextSplitter:
    """
    自动根据文件扩展名选择合适的分割策略的封装类
    """
    
    def __init__(self, chunk_size=100, chunk_overlap=20):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 映射文件扩展名到 LangChain 的 Language 枚举
        self.extension_map = {
            ".py": Language.PYTHON,
            ".js": Language.JS,
            ".java": Language.JAVA,
            ".go": Language.GO,
            ".cpp": Language.CPP,
            ".cs": Language.CSHARP,
            ".ts": Language.TS,
            ".md": Language.MARKDOWN,
            ".html": Language.HTML,
            ".htm": Language.HTML,
            ".sol": Language.SOL, # Solidity
            ".rb": Language.RUBY,
            ".php": Language.PHP,
        }

    def split_documents(self, file_path, text):
        """
        根据文件路径后缀自动选择分割器并分割文本
        
        Args:
            file_path: 文件路径（用于提取后缀）
            text: 要分割的文本内容
            
        Returns:
            List[Document]: 分割后的文档列表
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        language = self.extension_map.get(ext)
        
        if language:
            print(f"检测到 {ext} 文件，使用 {language} 专用分割策略...")
            splitter = RecursiveCharacterTextSplitter.from_language(
                language=language,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        else:
            print(f"检测到普通文本文件 ({ext})，使用默认分割策略...")
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                # 默认分隔符，优先段落，其次句子
                separators=["\n\n", "\n", " ", ""]
            )
            
        return splitter.create_documents([text])

# --- 测试代码 ---

if __name__ == "__main__":
    auto_splitter = AutoTextSplitter(chunk_size=50, chunk_overlap=0)

    # 1. 测试 Python 文件
    py_code = """
class Demo:
    def run(self):
        print("Running...")
    """
    print("\n>>> 测试 1: Python")
    docs = auto_splitter.split_documents("script.py", py_code)
    for doc in docs: print(f"[Chunk]: {doc.page_content}")

    # 2. 测试 Markdown 文件
    md_text = """
# Title
## Section 1
Content here.
    """
    print("\n>>> 测试 2: Markdown")
    docs = auto_splitter.split_documents("README.md", md_text)
    for doc in docs: print(f"[Chunk]: {doc.page_content}")

    # 3. 测试普通文本文件
    txt_text = "这是一个普通的文本文件。\n\n它没有特殊的语法结构。\n只是简单的段落。"
    print("\n>>> 测试 3: Plain Text")
    docs = auto_splitter.split_documents("notes.txt", txt_text)
    for doc in docs: print(f"[Chunk]: {doc.page_content}")
