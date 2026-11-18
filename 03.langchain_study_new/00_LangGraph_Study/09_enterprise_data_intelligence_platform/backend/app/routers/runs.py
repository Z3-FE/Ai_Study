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
    """生成 ISO 格式 UTC 时间，作为 SSE 事件时间戳。"""

    return datetime.now(timezone.utc).isoformat()


class RunEventBroker:
    """本地单进程 SSE 事件中心，负责缓存 run 事件并推送给订阅者。"""

    def __init__(self) -> None:
        """初始化事件历史、订阅队列和已完成 run 标记。"""

        self._history: dict[str, list[dict]] = defaultdict(list)
        self._subscribers: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._completed_runs: set[str] = set()

    async def publish(self, run_id: str, event_type: str, data: dict | None = None) -> None:
        """发布一条 run 事件，同时写入历史缓存并推送给当前订阅者。"""

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
        """订阅某个 run 的事件流，先补发历史事件，再等待实时事件。"""

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


def _build_semantic_context(conversation_id: str) -> dict:
    """组装传给 AI 层的语义上下文，优先使用结构化语义资产。"""

    conversation = store.get_conversation(conversation_id)
    conversation_assets = store.list_conversation_semantic_assets(conversation_id)
    return {
        "data_source_id": conversation.data_source_id if conversation else "olist",
        "adopted_semantic_draft_ids": conversation.adopted_semantic_draft_ids if conversation else [],
        "adopted_semantic_draft_titles": conversation.adopted_semantic_draft_titles if conversation else [],
        "conversation_assets": conversation_assets,
        "metrics": store.list_metric_assets(),
        "dimensions": store.list_dimension_assets(),
        "datasets": store.list_dataset_assets(),
        "glossary": store.list_glossary_assets(),
    }


def _start_chat_run(run_id: str) -> None:
    """在当前进程启动聊天 run，避免重复启动同一个未完成任务。"""

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
        """后台任务结束后清理任务集合，避免内存中残留已完成任务。"""

        background_tasks.discard(done_task)
        if started_run_tasks.get(run_id) is done_task:
            started_run_tasks.pop(run_id, None)

    task.add_done_callback(cleanup)


async def _execute_chat_run(run_id: str) -> None:
    """执行一次聊天 run：更新状态、发布步骤事件、调用 AI 层并写入助手消息。"""

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

        final_text = ""
        messages = to_agent_messages(store.list_messages(run.conversation_id) or [])

        semantic_context = _build_semantic_context(run.conversation_id)  # 语义上下文 ,真实项目：业务层先根据用户、数据源、问题、权限筛选出候选上下文

        async for graph_event in agent_client.stream_chat(
                messages,
                run.thread_id,
                semantic_context=semantic_context,
        ):
            event_type = graph_event.get("type", "graph.event")
            data = {key: value for key, value in graph_event.items() if key != "type"}
            if event_type == "message.completed":
                final_text = data.get("content", "")
            if event_type == "step.started":
                store.update_analysis_run(run_id, AnalysisRunStatus.running, data.get("step"))
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
        store.update_analysis_run(run_id, AnalysisRunStatus.completed, "report")
        store.update_conversation_status(run.conversation_id, ConversationStatus.completed)
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
    """创建一次最小聊天 run，写入用户消息，并返回前端订阅用的 SSE 地址。"""

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
    """查询某个 run 的持久化状态。"""

    run = store.get_analysis_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run": run}


@router.get("/runs/{run_id}/events")
async def stream_run_events(run_id: str):
    """通过 SSE 返回某个 run 的历史事件和实时事件。"""

    run = store.get_analysis_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # 终止状态枚举
    terminal_statuses = {
        AnalysisRunStatus.completed,
        AnalysisRunStatus.failed,
        AnalysisRunStatus.cancelled,
    }
    has_cached_events = bool(event_broker._history.get(run_id))  # 检查是否有缓存事件
    if run.status not in terminal_statuses:
        _start_chat_run(run_id)

    async def event_stream():
        """把内部事件对象序列化成浏览器 EventSource/fetch 可读取的 SSE 文本。"""

        # 最后一次事件
        if run.status in terminal_statuses and not has_cached_events:
            event_type = {
                AnalysisRunStatus.completed: "run.completed",
                AnalysisRunStatus.failed: "run.failed",
                AnalysisRunStatus.cancelled: "run.cancelled",
            }[run.status]
            event = {
                "id": f"evt_{uuid4().hex[:12]}",
                "type": event_type,
                "run_id": run_id,
                "created_at": _utcnow_iso(),
                "data": {
                    "message": f"Run 已处于 {run.status.value} 状态，当前进程没有缓存到历史 SSE 事件。"
                },
            }
            yield f"id: {event['id']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            return

        # 实时事件
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
