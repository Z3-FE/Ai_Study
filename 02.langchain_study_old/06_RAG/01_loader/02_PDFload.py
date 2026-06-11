from langchain_community.document_loaders import PyPDFLoader

laoder_pdf = PyPDFLoader(
    file_path='asset/个人简历.pdf'
)
doc = laoder_pdf.load()

for i, content in enumerate(doc):
    print(content.page_content)

print('-' * 50)

# # 网上链接
# laoder_pdf2 = PyPDFLoader(
#     file_path="https://arxiv.org/pdf/2302.03803"
# )
#
# print(laoder_pdf2.load()[0])
