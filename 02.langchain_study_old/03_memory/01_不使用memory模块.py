import os
from typing import List

from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI

from langchain_study.env_utils import API_KEY, BASE_URL, MODEL_NAME, TEMPERATURE

# --- 配置 ---
# 1. 实例化 LLM
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL
# 任何大语言模型都匹配 openai
llm = ChatOpenAI(
    model_name=MODEL_NAME,
    temperature=TEMPERATURE,
    # api_key=API_KEY,
    # base_url=BASE_URL
)
print(f"✅ 模型 '{llm.model_name}' 实例创建成功。")


# 方式1：
def chat_with_model():
    prompt = ChatPromptTemplate([
        ("system", "你是一个人工智能助手"),
        ("human", "{03_embeddings}"),
    ])

    chains = prompt | llm

    while True:
        input_data = input('======行输入您的问题，输入"退出"以结束对话。\n')
        if input_data == "退出":
            break
        else:

            response = chains.invoke({"03_embeddings": input_data})
            print(f"大模型返回的结果：{response.content}")
            prompt.messages.append(AIMessage(response.content))
            prompt.messages.append(HumanMessage(input_data))


# 方式二：
def chat_with_model_optimized():
    # 1. 初始化聊天历史列表
    # 历史消息将存储在这个列表中，供每一轮对话使用
    history_messages: List[BaseMessage] = []

    # 2. 定义静态 Prompt 模板
    # 注意：模板中包含 {history} 和 {03_embeddings} 两个变量
    system_instruction = "你是一个专业的人工智能助手，请基于提供的上下文和历史记录，准确回答用户的问题。"

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_instruction),
            # 动态插入历史消息列表
            ("placeholder", "{history}"),
            # 插入当前用户问题
            ("human", "{03_embeddings}"),
        ]
    )

    # 3. 构建 LCEL Chain
    # Chain 结构：(输入: history, 03_embeddings) -> Prompt -> LLM -> Parser (纯文本)
    chain = prompt | llm | StrOutputParser()

    # 4. 进入聊天循环
    while True:
        input_data = input('======请输入您的问题，输入"退出"以结束对话。=========\n')
        if input_data.lower() == "退出":
            print("\n对话已结束。")
            break

        # 5. 构造 Chain 的输入字典
        try:
            # 6. 调用 Chain
            response_content = chain.invoke({
                "history": history_messages,  # 传入历史消息列表
                "03_embeddings": input_data  # 传入当前问题字符串
            })

            # 7. 打印结果
            print(f"\n大模型返回的结果：{response_content}")
            print("-" * 50)

            # 8. 更新聊天历史 (关键步骤！)
            # 存储当前用户的消息和模型的回复，为下一轮对话做准备
            history_messages.append(HumanMessage(content=input_data))
            history_messages.append(AIMessage(content=response_content))

        except Exception as e:
            print(f"发生错误: {e}")
            print("请检查 API 密钥、Base URL 和网络连接。")
            break


# 聊天函数
# chat_with_model()
chat_with_model_optimized()
