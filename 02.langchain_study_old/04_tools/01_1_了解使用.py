from langchain_core.tools import tool
from pydantic import Field, BaseModel


@tool
def add_sum(a: int, b: int) -> int:
    """
    (描述是必须的，没有会报错！！！！！！！！！！！！)
    (ValueError: Function must have a docstring if description not provided.)
    计算两个整数的和。

    Args:
        a: 第一个整数
        b: 第二个整数

    Returns:
        两个整数的和
    """
    return a + b


print("name", add_sum.name)
print("args", add_sum.args)
print("description", add_sum.description)
print("return_direct", add_sum.return_direct)

print('#' * 50)


class FieldInfo(BaseModel):
    a: int = Field("第一个参数")
    b: int = Field("第二个参数")


@tool(
    return_direct=True,
    name_or_callable="add_sum22222",
    description="两个整数的和",
    args_schema=FieldInfo
)
def add_sum2(a: int, b: int) -> int:
    return a + b


print(add_sum2.invoke({"a": 1, "b": 2}))  # 使用

print("name2", add_sum2.name)
print("args2", add_sum2.args)
print("description2", add_sum2.description)
print("return_direct2", add_sum2.return_direct)
