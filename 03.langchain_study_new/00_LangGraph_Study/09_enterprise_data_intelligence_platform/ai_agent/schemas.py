from __future__ import annotations

from pydantic import BaseModel, Field


class AgentChatMessage(BaseModel):
    role: str
    content: str


class AgentChatStreamRequest(BaseModel):
    thread_id: str
    messages: list[AgentChatMessage] = Field(default_factory=list)
    semantic_context: dict = Field(default_factory=dict)
