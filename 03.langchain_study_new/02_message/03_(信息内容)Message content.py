"""Message content (信息内容)"""
import base64
import os
from pathlib import Path
import dashscope

import requests
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from openai import OpenAI

from env_utils import (
    API_KEY,
    BASE_URL,
    MODEL_NAME,
    MODEL_NAME_OMNI, MODEL_NAME_36,
)

model = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME_OMNI,
)


# 转换url为base64编码
def url_to_base64(url):
    try:
        response = requests.get(url, timeout=10)
        # 如果状态码不是 200，这行会抛出异常
        response.raise_for_status()

        base64_str = base64.b64encode(response.content).decode('utf-8')
        return base64_str
    except requests.exceptions.HTTPError as e:
        print(f"HTTP 错误: {e}")  # 比如会打印 403 (过期) 或 404 (找不到)
    except Exception as e:
        print(f"发生其他错误: {e}")
    return None


def Standard_content_blocks():
    """标准内容块"""
    # 调用content_blocks 实现所有大模型的content进行统一化

    # 纯字符串形式
    human_message1 = HumanMessage("Hello, how are you?")

    # 厂商原生格式 (e.g., OpenAI)
    human_message2 = HumanMessage(content=[
        {"type": "text", "text": "Hello, how are you?"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
    ])

    # 标准化块格式
    human_message3 = HumanMessage(content_blocks=[
        {"type": "text", "text": "Hello, how are you?"},
        {"type": "image", "url": "https://example.com/image.jpg"},
    ])
    print(f'human_message1: {human_message1}')
    print(f'human_message2: {human_message2}')
    print(f'human_message3: {human_message3}')


def Multimodal_InputOut():
    """多态输入 三种格式（url, base64, file）"""
    message = [
        # 1. 结构化 & url 方式
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "图片中都有什么?"},
                {"type": "image",
                 "url": "https://dashscope-7c2c.oss-accelerate.aliyuncs.com/1d/9f/20260415/70729cf4/e52afcef-6272-4315-aa05-58fa15508dfd_0.png?Expires=1776334464&OSSAccessKeyId=LTAI5tPxpiCM2hjmWrFXrym1&Signature=nmGsrXhHl33dd1C0D7Av4nzr%2FJg%3D"},
            ]
        }
        # 2.调用HumanMessage & url 实现所有大模型的content进行统一化
        # HumanMessage(content_blocks=[
        #     {"type": "text", "text": "图片中都有什么?"},
        #     {"type": "image",
        #      "url": "https://dashscope-7c2c.oss-accelerate.aliyuncs.com/1d/9f/20260415/70729cf4/e52afcef-6272-4315-aa05-58fa15508dfd_0.png?Expires=1776334464&OSSAccessKeyId=LTAI5tPxpiCM2hjmWrFXrym1&Signature=nmGsrXhHl33dd1C0D7Av4nzr%2FJg%3D"},
        # ])
        # 3. 结构化 & base64 方式 （不支持，看原生写法）
        # {
        #     "role": "user",
        #     "content": [
        #         {"type": "text", "text": "图片中都有什么详细描述一下?"},
        #         {
        #             "type": "file",
        #             'file_id': 'file-fe-7e063d666aad4041a3cfdc31',
        #         },
        #     ]
        # }

    ]
    print(f'model.invoke(message): {model.invoke(message)}')

# Standard_content_blocks()
# Multimodal_InputOut()


# OpenAI上传阿里上传文件
# def upload_file_to_aliyun():
#     client = OpenAI(
#         # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
#         api_key=API_KEY,
#         base_url=BASE_URL,
#     )
#     # test.txt 是一个本地示例文件
#     file_object = client.files.create(file=Path("test.png"), purpose="file-extract")
#
#     print(file_object.model_dump_json())
#
#
# upload_file_to_aliyun()


# # # 注意：原生 SDK 的消息结构和 OpenAI 略有不同
# FILE_ID = 'file-fe-7e063d666aad4041a3cfdc31'
# messages = [
#     {'role': 'system', 'content': f'fileid://{FILE_ID}'},
#     {
#         "role": "user",
#         "content": "图片中都有什么详细描述一下?"
#     }
# ]
#
# response = dashscope.Generation.call(
#     # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
#     api_key=API_KEY,
#     model="qwen-long",
#     messages=messages,
#     result_format='message'
# )
# print(response)
