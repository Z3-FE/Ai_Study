"""创建工具"""
from typing import Literal

from langchain.tools import tool
from pydantic import BaseModel, Field

"""1. 创建工具"""


@tool
def search_database(query: str, limit: int = 10) -> str:
    """在客户数据库中搜索与查询条件相匹配的记录。

    Args:
        query: 查询条件，用于搜索数据库中的记录。
        limit: 返回的最大记录数，默认值为10。
    """
    return f"Found {limit} results for '{query}'"


print(search_database.invoke({"query": "查询所有客户", "limit": 10}))

"""2. 自定义工具属性"""

"""2.1 自定义工具名称"""


@tool("search_records")
def search(query: str) -> str:
    """在客户数据库中搜索与查询条件相匹配的记录。"""
    return "搜索客户数据库"


print(search.name)  # search_records

"""2.2 自定义工具描述"""


@tool('desc_base', description="根据文本描述元素类型11111")
def desc(query: str) -> str:
    """根据文本描述元素类型22222"""
    return "根据文本描述元素类型"


print(desc.description)  # 根据文本描述元素类型11111

"""2.3高级模式定义"""


# 方式1：pydantic

class Weather_Input(BaseModel):
    city: str = Field(description="城市名称", default='北京')
    units: Literal['摄氏度', '华氏温度'] = Field(description="温度单位", default='摄氏度')  # literal类型, 相当于 枚举类型
    # 其他字段...


@tool(args_schema=Weather_Input)
def weather(city: str = '北京', units: Literal['摄氏度', '华氏温度'] = '摄氏度') -> str:
    """查询城市的天气"""
    return f"查询 {city} 的天气，单位为 {units}"


print(weather.invoke({}))
