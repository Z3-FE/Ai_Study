""" version="v2", 可以直接区分信息的类型，例如：消息和更新"""
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from env_utils import MODEL_NAME, API_KEY, BASE_URL

model = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
)


def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"{city}, 今天天气晴朗!"


agent = create_agent(model=model, tools=[get_weather])

input_message = {"role": "user", "content": "波士顿今天天气怎么样?"}
for chunk in agent.stream(
        {"messages": [input_message]},
        stream_mode=["messages", "updates"],
        version="v2",
):
    print(chunk)
