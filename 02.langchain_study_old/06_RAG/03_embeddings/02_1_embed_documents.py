"""
embed_documents: 数组向量化
"""
import os

from langchain_community.document_loaders import CSVLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import TextSplitter
from tornado.locale import CSVLocale

from langchain_study.env_utils import MODEL_NAME, EMBEDDING_MODEL_NAME, API_KEY, BASE_URL

embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    check_embedding_ctx_length=False
)

embed_query = embeddings.embed_documents(texts=[
    "Hi there!",
    "Oh, hello!",
    "What's your name?",
    "My friends call me World",
    "Hello World!"
])

print(len(embed_query))  # 5
print(embed_query[0][:10])  # 去第一组数据中前10个
print(50 * "-")

csv_loader = CSVLoader(
    file_path='./asset/employees.csv'
)

# load_and_split 直接进行文本切割
text_splitter = csv_loader.load_and_split()

embed_query_csv = embeddings.embed_documents(texts=[x.page_content for x in text_splitter])

print(len(embed_query_csv))
print(embed_query_csv)
