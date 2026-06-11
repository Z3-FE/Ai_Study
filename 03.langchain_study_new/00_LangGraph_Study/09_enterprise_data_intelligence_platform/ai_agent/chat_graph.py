from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, MessagesState, StateGraph
from .env_utils import API_KEY, BASE_URL, MODEL_NAME

load_dotenv()

SYSTEM_PROMPT = """你是 Insight Agent 的普通聊天助手。
当前阶段只负责普通问答和学习陪伴，不生成 SQL，不执行数据库查询。
如果用户询问数据分析能力，请说明后续会接入语义层、SQL 审核、PostgreSQL 查询和审计。
回答要简洁、自然，并尽量帮助用户理解下一步。"""


def _build_model() -> ChatOpenAI | None:
    if os.getenv("INSIGHT_CHAT_MODEL_MODE") == "mock":
        return None

    # api_key = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
    # base_url = os.getenv("BASE_URL")
    # model_name = os.getenv("MODEL_NAME", "qwen-plus")
    #
    # if not api_key:
    #     return None

    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=30,
        max_retries=2,
    )


def _fallback_response(messages: list[BaseMessage]) -> str:
    last_user = next((message.content for message in reversed(messages) if message.type == "human"), "")
    return (
        "我已经收到你的问题。当前先跑通普通聊天最小链路：会话消息会写入 PostgreSQL，"
        "LangGraph 会执行一个 chat 节点，并通过 SSE 把步骤和回复返回前端。"
        f"\n\n你的问题是：{last_user}"
    )


async def _chat_node(state: MessagesState) -> dict:
    writer = get_stream_writer()
    messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
    model = _build_model()

    full_text = ""
    try:
        if model is None:
            full_text = _fallback_response(state["messages"])
            for token in full_text:
                writer({"type": "message.delta", "content": token})
                await asyncio.sleep(0)
        else:
            async for chunk in model.astream(messages):
                content = chunk.content or ""
                print(f"content: {content}")
                if content:
                    full_text += content
                    writer({"type": "message.delta", "content": content})
    except Exception as exc:
        full_text = f"模型调用暂时失败，已切换为本地兜底回复。错误信息：{exc}"
        writer({"type": "message.delta", "content": full_text})

    writer({"type": "message.completed", "content": full_text})
    return {"messages": [AIMessage(content=full_text)]}


def build_chat_graph():
    builder = StateGraph(MessagesState)
    builder.add_node("chat", _chat_node)
    builder.add_edge(START, "chat")
    builder.add_edge("chat", END)
    return builder.compile()


chat_graph = build_chat_graph()


async def stream_chat_graph(messages: list[BaseMessage], thread_id: str) -> AsyncIterator[dict]:
    config = {"configurable": {"thread_id": thread_id}}
    async for event in chat_graph.astream(
            {"messages": messages},
            config=config,
            stream_mode="custom",
    ):
        yield event
