"""
embed_query: 句子向量化

"""
import os

from langchain_openai import OpenAIEmbeddings

from langchain_study.env_utils import MODEL_NAME, EMBEDDING_MODEL_NAME, API_KEY, BASE_URL

embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    check_embedding_ctx_length=False
)
#
embed_query = embeddings.embed_query(text="你好")

print(len(embed_query))  # 1024
print(embed_query)
