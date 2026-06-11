from langchain_community.tools import StructuredTool
from pydantic import BaseModel, Field


class FieldInfo(BaseModel):
    query: str = Field('输入查询参数')


def search(query: str) -> str:
    return '最终查询结果'


search_tool = StructuredTool.from_function(
    func=search,
    name="search",
    description="调用浏览器查询",
    args_schema=FieldInfo
)

print(search_tool.invoke({'03_embeddings': '你是一个大信球'}))

print("name", search_tool.name)
print("args", search_tool.args)
print("description", search_tool.description)
print("return_direct", search_tool.return_direct)
