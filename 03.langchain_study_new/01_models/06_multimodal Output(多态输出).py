"多态输出"

import dashscope
from dashscope.aigc.image_generation import ImageGeneration
from dashscope.api_entities.dashscope_response import Message
from langchain_core.messages import ToolMessage
from langchain_openai import ChatOpenAI

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

from langchain.tools import tool


@tool
def wanx_image_generator(prompt: str):
    """
    当用户请求画图、生成图片或视觉创作时，调用此工具。
    输入参数 prompt 是对图片的详细英文描述。
    """
    message = Message(
        role="user",
        content=[
            {
                "text": prompt}
        ]
    )
    dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
    response = ImageGeneration.async_call(
        model="wan2.7-image-pro",
        prompt=prompt,
        api_key=API_KEY,
        messages=[message],
        n=1,
        size='1024*1024'
    )
    if response.status_code == 200:
        print(f"任务提交成功，任务ID: {response.output.task_id}")

        # 等待任务完成
        status = ImageGeneration.wait(task=response, api_key=API_KEY)

        if status.output.task_status == "SUCCEEDED":
            print("任务完成!")
            print(f"结果:")
            print(status)
            return status
        else:
            print(f"任务失败，状态: {status.output.task_status}")
    else:
        print(f"任务创建失败: {response.code} - {response.message}")


model_with_tools = model.bind_tools([wanx_image_generator])
message = [{"role": "user", "content": "Create a picture of a cat"}]
response_tool = model_with_tools.invoke(message)
message.append(response_tool)

for tool in response_tool.tool_calls:
    print(tool)
    # 1. 运行工具获取原始结果对象
    raw_res = wanx_image_generator.invoke(tool['args'])

    # 2. 从原始结果中提取出图片的 URL (根据你打印出来的 JSON 结构)
    # 结构是: raw_res.output.choices[0].message.content[0]['image']
    image_url = raw_res.output.choices[0].message.content[0]['image']

    # 3. 创建标准的 ToolMessage
    # 注意：tool_call_id 必须等于上面 tool_call 里的 id
    tool_msg = ToolMessage(
        content=f"Successfully generated image. URL: {image_url}",
        tool_call_id=tool['id']
    )

    # 4. 把标准的消息对象加入列表
    message.append(tool_msg)

final_response = model_with_tools.invoke(message)
print(f"最终响应: {final_response}")
