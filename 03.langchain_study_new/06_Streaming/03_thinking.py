from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI

from env_utils import MODEL_NAME, API_KEY, BASE_URL


class DashScopeChatOpenAI(ChatOpenAI):
    """保留 DashScope/Qwen OpenAI 兼容接口中的 reasoning_content。"""

    def _convert_chunk_to_generation_chunk(
            self,
            chunk: dict,
            default_chunk_class: type,
            base_generation_info: dict | None,
    ):
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk,
            default_chunk_class,
            base_generation_info,
        )
        if generation_chunk is None:
            return None

        choices = chunk.get("choices", []) or chunk.get("chunk", {}).get("choices", [])
        if not choices:
            return generation_chunk

        delta = choices[0].get("delta") or {}
        reasoning = delta.get("reasoning_content")
        if reasoning and isinstance(generation_chunk.message, AIMessageChunk):
            generation_chunk.message.additional_kwargs["reasoning_content"] = reasoning

        return generation_chunk


# create_agent 需要 LangChain chat model，因为它会调用 model.bind_tools(...)。
# OpenAI SDK 的 client.chat.completions.create(..., stream=True) 返回的是 Stream，
# 不能直接作为 agent model 传入。
#
# ChatOpenAI 只保留 OpenAI 官方字段；DashScope/Qwen 的 reasoning_content 是扩展字段，
# 所以这里用一个小子类把它补回 AIMessageChunk.additional_kwargs。
model = DashScopeChatOpenAI(
    model=MODEL_NAME,  # 您可以按需更换为其它深度思考模型
    api_key=API_KEY,
    base_url=BASE_URL,
    extra_body={"enable_thinking": True},
    stream_usage=True,
)


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


agent = create_agent(
    model=model,
    tools=[get_weather],
)

is_printing_thinking = False
is_printing_answer = False

for token, metadata in agent.stream(
        {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
        stream_mode="messages",
):
    if not isinstance(token, AIMessageChunk):
        continue

    reasoning_content = token.additional_kwargs.get("reasoning_content")
    text = [b for b in token.content_blocks if b["type"] == "text"]
    if reasoning_content:
        if not is_printing_thinking:
            print("[thinking]")
            is_printing_thinking = True
        print(reasoning_content, end="", flush=True)
    if text:
        if not is_printing_answer:
            print("\n\n[answer]")
            is_printing_answer = True
        print(text[0]["text"], end="")
