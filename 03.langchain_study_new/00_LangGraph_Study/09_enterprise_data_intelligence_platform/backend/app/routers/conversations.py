from fastapi import APIRouter, HTTPException, Query

from ..models import ConversationCreate, ConversationUpdate, MessageCreate
from ..store import store

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
def list_conversations(keyword: str | None = Query(default=None)):
    """查询会话列表，主要供左侧历史记录使用。"""

    return {"conversations": store.list_conversations(keyword)}


@router.post("")
def create_conversation(payload: ConversationCreate):
    """创建一个业务会话，并同时生成后续 LangGraph 使用的 thread_id。"""

    conversation = store.create_conversation(payload)
    return {
        "conversation_id": conversation.id,
        "thread_id": conversation.thread_id,
        "conversation": conversation,
    }


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str):
    """根据会话 ID 查询单个会话详情。"""

    conversation = store.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation": conversation}


@router.put("/{conversation_id}")
def update_conversation(conversation_id: str, payload: ConversationUpdate):
    """更新会话标题或状态。"""

    conversation = store.update_conversation(conversation_id, payload)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation": conversation}


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str):
    """删除一个会话以及它关联的消息。"""

    deleted = store.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "deleted": True}


@router.get("/{conversation_id}/messages")
def list_messages(conversation_id: str):
    """查询某个会话下用于前端展示的消息列表。"""

    messages = store.list_messages(conversation_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"messages": messages}


@router.post("/{conversation_id}/messages")
def create_message(conversation_id: str, payload: MessageCreate):
    """向某个会话追加一条用户消息或助手消息。"""

    message = store.add_message(conversation_id, payload)
    if not message:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": message}
