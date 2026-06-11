from langchain_community.document_loaders import TextLoader

file = 'asset/01_langchain_utf-8.txt'
# encoding='utf-8' 非必填
loader = TextLoader(file_path=file, encoding='utf-8')
print(loader.load())  # list[Document]

doc = loader.load()

for i, content in enumerate(doc):
    print(content.page_content)
