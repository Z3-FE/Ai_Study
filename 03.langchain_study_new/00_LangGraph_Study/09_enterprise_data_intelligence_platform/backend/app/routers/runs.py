from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..models import (
    AnalysisRunStatus,
    ChatRunCreate,
    ConversationStatus,
    MessageCreate,
    MessageRole,
)
from ..services.agent_client import agent_client, to_agent_messages
from ..store import store

router = APIRouter(tags=["runs"])


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunEventBroker:
    """In-memory SSE event buffer for the local single-process development server."""

    def __init__(self) -> None:
        self._history: dict[str, list[dict]] = defaultdict(list)
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._completed_runs: set[str] = set()

    async def publish(self, run_id: str, event_type: str, data: dict | None = None) -> None:
        event = {
            "id": f"evt_{uuid4().hex[:12]}",
            "type": event_type,
            "run_id": run_id,
            "created_at": _utcnow_iso(),
            "data": data or {},
        }
        self._history[run_id].append(event)

        if event_type in {"run.completed", "run.failed", "run.cancelled"}:
            self._completed_runs.add(run_id)

        for queue in tuple(self._subscribers[run_id]):
            await queue.put(event)

    async def subscribe(self, run_id: str) -> AsyncIterator[dict]:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[run_id].add(queue)
        history_index = 0
        try:
            while True:
                history = self._history.get(run_id, [])
                while history_index < len(history):
                    event = history[history_index]
                    history_index += 1
                    yield event
                    if event["type"] in {"run.completed", "run.failed", "run.cancelled"}:
                        return

                if run_id in self._completed_runs:
                    return

                event = await queue.get()
                history = self._history.get(run_id, [])
                history_index = max(history_index, len(history))
                yield event
                if event["type"] in {"run.completed", "run.failed", "run.cancelled"}:
                    return
        finally:
            self._subscribers[run_id].discard(queue)


event_broker = RunEventBroker()
background_tasks: set[asyncio.Task] = set()
started_run_tasks: dict[str, asyncio.Task] = {}


def _start_chat_run(run_id: str) -> None:
    """Start one run in the same process that owns the SSE subscription."""

    task = started_run_tasks.get(run_id)
    if task and not task.done():
        return

    run = store.get_analysis_run(run_id)
    if not run or run.status in {
        AnalysisRunStatus.completed,
        AnalysisRunStatus.failed,
        AnalysisRunStatus.cancelled,
    }:
        return

    task = asyncio.create_task(_execute_chat_run(run_id))
    started_run_tasks[run_id] = task
    background_tasks.add(task)

    def cleanup(done_task: asyncio.Task) -> None:
        background_tasks.discard(done_task)
        if started_run_tasks.get(run_id) is done_task:
            started_run_tasks.pop(run_id, None)

    task.add_done_callback(cleanup)


async def _execute_chat_run(run_id: str) -> None:
    run = store.get_analysis_run(run_id)
    if not run:
        return

    try:
        store.update_analysis_run(run_id, AnalysisRunStatus.running, "understand_question")
        await event_broker.publish(
            run_id,
            "run.started",
            {
                "conversation_id": run.conversation_id,
                "thread_id": run.thread_id,
                "question": run.question,
            },
        )

        await event_broker.publish(
            run_id,
            "step.started",
            {"step": "understand_question", "name": "问题理解"},
        )
        await asyncio.sleep(0)
        await event_broker.publish(
            run_id,
            "step.completed",
            {
                "step": "understand_question",
                "name": "问题理解",
                "summary": "已识别为普通聊天请求，进入 chat 节点。",
            },
        )

        store.update_analysis_run(run_id, AnalysisRunStatus.running, "chat")
        await event_broker.publish(
            run_id,
            "step.started",
            {"step": "chat", "name": "普通聊天"},
        )

        final_text = ""
        messages = to_agent_messages(store.list_messages(run.conversation_id) or [])
        async for graph_event in agent_client.stream_chat(messages, run.thread_id):
            event_type = graph_event.get("type", "graph.event")
            data = {key: value for key, value in graph_event.items() if key != "type"}
            if event_type == "message.completed":
                final_text = data.get("content", "")
            await event_broker.publish(run_id, event_type, data)

        assistant_message = store.add_message(
            run.conversation_id,
            MessageCreate(
                role=MessageRole.assistant,
                content=final_text,
                run_id=run_id,
                metadata={"node": "chat", "streamed": True},
            ),
        )
        store.update_analysis_run(run_id, AnalysisRunStatus.completed, "chat")
        store.update_conversation_status(run.conversation_id, ConversationStatus.completed)

        await event_broker.publish(
            run_id,
            "step.completed",
            {
                "step": "chat",
                "name": "普通聊天",
                "summary": "助手回复已生成并写入 PostgreSQL。",
            },
        )
        await event_broker.publish(
            run_id,
            "run.completed",
            {
                "assistant_message": (
                    assistant_message.model_dump(mode="json") if assistant_message else None
                )
            },
        )
    except Exception as exc:
        store.update_analysis_run(run_id, AnalysisRunStatus.failed, "chat")
        store.update_conversation_status(run.conversation_id, ConversationStatus.failed)
        await event_broker.publish(
            run_id,
            "run.failed",
            {"message": str(exc)},
        )


@router.post("/conversations/{conversation_id}/runs")
async def create_chat_run(conversation_id: str, payload: ChatRunCreate):
    """Create one minimal LangGraph chat run and return its SSE stream URL."""

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question cannot be empty")

    run = store.create_analysis_run(conversation_id, question)
    if not run:
        raise HTTPException(status_code=404, detail="Conversation not found")

    user_message = store.add_message(
        conversation_id,
        MessageCreate(
            role=MessageRole.user,
            content=question,
            run_id=run.id,
            metadata={"source": "chat_composer"},
        ),
    )
    return {
        "run_id": run.id,
        "conversation_id": conversation_id,
        "thread_id": run.thread_id,
        "events_url": f"/api/runs/{run.id}/events",
        "user_message": user_message,
    }


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    """Fetch the persisted status of one analysis run."""

    run = store.get_analysis_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run": run}


@router.get("/runs/{run_id}/events")
async def stream_run_events(run_id: str):
    """Stream buffered and live LangGraph events using Server-Sent Events."""

    if not store.get_analysis_run(run_id):
        raise HTTPException(status_code=404, detail="Run not found")

    _start_chat_run(run_id)

    async def event_stream():
        async for event in event_broker.subscribe(run_id):
            yield f"id: {event['id']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
