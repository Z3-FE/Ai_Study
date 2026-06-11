from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from env_utils import API_KEY, BASE_URL, MODEL_NAME
from rich import inspect

model = ChatOpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
)


def message_summary():
    agent = create_agent(
        model=model,
        system_prompt="你是一个专业的助手。",
        tools=[],
        middleware=[
            SummarizationMiddleware(
                model=model,
                trigger=("tokens", 400),
                keep=("messages", 5)
            )
        ],
        checkpointer=InMemorySaver()
    )

    history = []
    config = {"configurable": {"thread_id": "message_summary_demo_1"}}
    # 模拟 10 轮对话
    for i in range(10):
        user_input = f"这是第 {i + 1} 次提问。现在是几点给我时间戳格式"
        print(f"\n--- 第 {i + 1} 轮交互 ---")

        response = agent.invoke({"messages": [{"role": "user", "content": user_input}]}, config)

        # 更新历史记录（在实际 LangGraph 项目中，这通常由 checkpointer 自动完成）
        # 这里手动模拟历史增长
        history = response
        print(f"当前消息总数: {len(history['messages'])}")
        for index, message in enumerate(history["messages"]):
            #  判断是否是摘要消息中间件触发
            if hasattr(message, 'additional_kwargs') and message.additional_kwargs.get("lc_source") == "summarization":
                print(f'{index}:✨{inspect(message)} 触发了总结中间件！历史记录已被压缩！！！！！！！！！！！！！！！！！！！！')
            else:
                print(f"{index}: {message.content}")


if __name__ == '__main__':
    message_summary()
