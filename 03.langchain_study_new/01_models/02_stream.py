"""
流式调用示例
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

# 2.流式调用
streamdata = model.stream("为什么鹦鹉的羽毛如此鲜艳多彩？")
"""
流式调用：
flush=True 强制程序立即将缓冲区里的数据推送到屏幕上，而不是等待缓冲区填满
end
\n (默认)：打印完后另起一行。

"" (空字符串)：打印完后紧跟下一个字符，无缝连接。

"|"：打印完后不换行，并加上一个竖线作为视觉上的“切割符”。

"""
for chunk in streamdata:
    print(chunk.text, end="", flush=True)