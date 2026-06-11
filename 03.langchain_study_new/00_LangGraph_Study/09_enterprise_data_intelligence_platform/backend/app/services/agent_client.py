from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from ..models import MessageRole
from ..settings import settings


class AgentApiError(RuntimeError):
    pass


class AgentApiClient:
    """HTTP client for the separate AI Agent service."""

    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ai_agent_base_url).rstrip("/")
        self.transport = transport

    async def stream_chat(self, messages: list[dict], thread_id: str) -> AsyncIterator[dict]:
        payload = {
            "thread_id": thread_id,
            "messages": messages,
        }

        async with httpx.AsyncClient(timeout=None, transport=self.transport) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat/stream",
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        yield json.loads(line.removeprefix("data: "))
            except httpx.HTTPError as exc:
                raise AgentApiError(f"AI Agent API 调用失败：{exc}") from exc


def to_agent_messages(messages) -> list[dict[str, str]]:
    converted = []
    for message in messages:
        if message.role == MessageRole.user:
            role = "user"
        elif message.role == MessageRole.assistant:
            role = "assistant"
        elif message.role == MessageRole.system:
            role = "system"
        else:
            role = "user"

        converted.append(
            {
                "role": role,
                "content": message.content,
            }
        )
    return converted


agent_client = AgentApiClient()
