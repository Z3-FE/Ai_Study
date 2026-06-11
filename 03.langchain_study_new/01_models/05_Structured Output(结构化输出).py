"结构化输出 : with_structured_output"
from langchain_openai import ChatOpenAI
from pydantic.v1 import BaseModel

from pydantic import BaseModel, Field

from env_utils import (
    MODEL_NAME,
    API_KEY,
    BASE_URL,
)

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
    max_retries=6,

)


class Add(BaseModel):
    "计算两个数的和"
    arg1: int = Field(description="第一个数")
    arg2: int = Field(description="第二个数")


result = model.with_structured_output(Add).invoke('1 + 2 等于几')  #
print(result)  # arg1=1 arg2=2

with_structured_output_raw = model.with_structured_output(Add, include_raw=True)  # 输出结构化
print(with_structured_output_raw.invoke('1 + 2 等于几')['raw'].content)  # { "arg1": 1, "arg2": 2 }


# 2.结构嵌套
class Actor(BaseModel):
    name: str
    role: str


class MovieDetails(BaseModel):
    title: str
    year: int
    cast: list[Actor]  # 嵌套 Actor
    genres: list[str]
    budget: float | None = Field(None, description="Budget in millions USD")


model_with_structure = model.with_structured_output(MovieDetails)

print(model_with_structure.invoke('请提供电影《盗梦空间》的详细信息'))
