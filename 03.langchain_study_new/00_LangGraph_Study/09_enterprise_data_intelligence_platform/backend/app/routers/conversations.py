from fastapi import APIRouter, HTTPException, Query

from ..models import ConversationCreate, ConversationUpdate, MessageCreate
from ..store import store

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
def list_conversations(keyword: str | None = Query(default=None)):
    """List conversations for the left sidebar."""

    return {"conversations": store.list_conversations(keyword)}


@router.post("")
def create_conversation(payload: ConversationCreate):
    """Create a new business conversation and its LangGraph thread id."""

    conversation = store.create_conversation(payload)
    return {
        "conversation_id": conversation.id,
        "thread_id": conversation.thread_id,
        "conversation": conversation,
    }


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str):
    """Fetch one conversation detail by id."""

    conversation = store.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation": conversation}


@router.put("/{conversation_id}")
def update_conversation(conversation_id: str, payload: ConversationUpdate):
    """Update conversation title or status."""

    conversation = store.update_conversation(conversation_id, payload)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation": conversation}


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str):
    """Delete one conversation and its messages."""

    deleted = store.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "deleted": True}


@router.get("/{conversation_id}/messages")
def list_messages(conversation_id: str):
    """List frontend-display messages under one conversation."""

    messages = store.list_messages(conversation_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"messages": messages}


@router.post("/{conversation_id}/messages")
def create_message(conversation_id: str, payload: MessageCreate):
    """Append a user or assistant message to one conversation."""

    message = store.add_message(conversation_id, payload)
    if not message:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": message}
