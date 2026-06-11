"""
批次调用示例
"""

import os

from langchain_openai import ChatOpenAI

from env_utils import (
    API_KEY,
    BASE_URL,
    MODEL_NAME,
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

# 3. 批次调用, 处理可以并行完成的任务 : model.batch() 方法

responses = model.batch([
    "为什么鹦鹉的羽毛如此多彩？",
    "飞机是怎么飞起来的？",
    "什么是量子计算？"
],
    config={
        'max_concurrency': 5,  # 最大并发数设置
    }
)

# 3.1打印每个响应的内容

for i, response in enumerate(responses):
    print('#' * 40, f"第{i+1}个响应", '#' * 40)
    print(response.content)

# 3.2 流模式打印每个响应的内容 : model.batch_as_completed() 方法

for i, response in enumerate(model.batch_as_completed([
    "为什么鹦鹉的羽毛如此多彩？",
    "飞机是怎么飞起来的？",
    "什么是量子计算？"
])):
    print('#' * 40, f"第{i+1}个响应", '#' * 40)
    print(response.content)