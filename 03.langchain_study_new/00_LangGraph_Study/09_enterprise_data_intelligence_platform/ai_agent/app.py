from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from .chat_graph import stream_chat_graph
from .schemas import AgentChatMessage, AgentChatStreamRequest


def _to_langchain_message(message: AgentChatMessage) -> BaseMessage:
    """把接口层传入的 role/content 消息转换为 LangChain 消息对象。"""

    if message.role in {"user", "human"}:
        return HumanMessage(content=message.content)
    if message.role == "assistant":
        return AIMessage(content=message.content)
    if message.role == "system":
        return SystemMessage(content=message.content)
    return HumanMessage(content=message.content)


def create_app() -> FastAPI:
    """创建 AI Agent 服务，提供健康检查和 LangGraph 聊天流式接口。"""

    app = FastAPI(
        title="Insight Agent AI Service",
        description="LangGraph AI layer for the enterprise data intelligence platform.",
        version="0.1.0",
    )

    @app.get("/api/health")
    def health_check():
        """返回 AI 层健康状态，方便业务后端或开发者确认服务是否启动。"""

        return {"status": "ok", "service": "ai_agent"}

    @app.post("/api/chat/stream")
    async def stream_chat(payload: AgentChatStreamRequest):
        """接收后端转发的聊天消息，并以 SSE 形式返回 LangGraph 执行事件。"""

        messages = [_to_langchain_message(message) for message in payload.messages]

        async def event_stream():
            """把 LangGraph 事件包装成 SSE data 行返回给调用方。"""

            async for event in stream_chat_graph(
                    messages,
                    payload.thread_id,
                    semantic_context=payload.semantic_context,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return app


app = create_app()
