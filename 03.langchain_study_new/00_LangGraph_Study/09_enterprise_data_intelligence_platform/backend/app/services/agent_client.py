from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import date, datetime
from enum import Enum
from typing import Any

import httpx

from ..models import MessageRole
from ..settings import settings


class AgentApiError(RuntimeError):
    """AI Agent 服务调用失败时抛出的业务异常。"""

    pass


class AgentApiClient:
    """封装业务后端到独立 AI Agent 服务的 HTTP 调用。"""

    def __init__(
            self,
            base_url: str | None = None,
            transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """初始化 AI Agent 客户端，允许测试时注入自定义 transport。"""

        self.base_url = (base_url or settings.ai_agent_base_url).rstrip("/")
        self.transport = transport

    def _json_safe(self, value: Any) -> Any:
        """把 datetime、Enum 等对象转换成 HTTP JSON 请求可序列化的数据。"""

        if isinstance(value, datetime | date):
            return value.isoformat()
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {key: self._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._json_safe(item) for item in value]
        return value

    async def stream_chat(
            self,
            messages: list[dict],
            thread_id: str,
            semantic_context: dict | None = None,
    ) -> AsyncIterator[dict]:
        """把会话消息发送给 AI Agent，并逐行解析其 SSE data 事件。"""

        payload = {
            "thread_id": thread_id,
            "messages": messages,
            "semantic_context": semantic_context or {},
        }
        payload = self._json_safe(payload)

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
    """把后端 Message 模型列表转换为 AI Agent 接口需要的 role/content 列表。"""

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
