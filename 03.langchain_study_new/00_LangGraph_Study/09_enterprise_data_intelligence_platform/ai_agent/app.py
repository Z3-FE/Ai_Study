from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from .chat_graph import stream_chat_graph
from .schemas import AgentChatMessage, AgentChatStreamRequest


def _to_langchain_message(message: AgentChatMessage) -> BaseMessage:
    if message.role in {"user", "human"}:
        return HumanMessage(content=message.content)
    if message.role == "assistant":
        return AIMessage(content=message.content)
    if message.role == "system":
        return SystemMessage(content=message.content)
    return HumanMessage(content=message.content)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Insight Agent AI Service",
        description="LangGraph AI layer for the enterprise data intelligence platform.",
        version="0.1.0",
    )

    @app.get("/api/health")
    def health_check():
        return {"status": "ok", "service": "ai_agent"}

    @app.post("/api/chat/stream")
    async def stream_chat(payload: AgentChatStreamRequest):
        """Stream LangGraph chat events as Server-Sent Events."""

        messages = [_to_langchain_message(message) for message in payload.messages]

        async def event_stream():
            async for event in stream_chat_graph(messages, payload.thread_id):
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
