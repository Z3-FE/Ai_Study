from fastapi import APIRouter, HTTPException, Query

from ..models import (
    SemanticDraftReview,
    SemanticDraftStatus,
    SemanticDraftUpdate,
    VectorSyncMode,
)
from ..store import store

router = APIRouter(prefix="/semantic/drafts", tags=["semantic-drafts"])


@router.get("")
def list_semantic_drafts(status: SemanticDraftStatus | None = Query(default=None)):
    """List document-extracted semantic candidates."""

    return {"drafts": store.list_drafts(status)}


@router.patch("/{draft_id}")
def update_semantic_draft(draft_id: str, payload: SemanticDraftUpdate):
    """Edit a candidate semantic asset before adoption or publish."""

    draft = store.update_draft(draft_id, payload)
    if not draft:
        raise HTTPException(status_code=404, detail="Semantic draft not found")
    return {"draft": draft}


@router.post("/{draft_id}/adopt")
def adopt_semantic_draft(draft_id: str, payload: SemanticDraftReview):
    """Adopt one semantic candidate into the current conversation context."""

    draft = store.adopt_draft(draft_id, payload)
    if not draft:
        raise HTTPException(status_code=404, detail="Semantic draft not found")
    return {"draft": draft}


@router.post("/{draft_id}/reject")
def reject_semantic_draft(draft_id: str):
    """Reject one semantic candidate."""

    draft = store.reject_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Semantic draft not found")
    return {"draft": draft}


@router.post("/{draft_id}/publish")
def publish_semantic_draft(draft_id: str, mode: VectorSyncMode = VectorSyncMode.sync):
    """Publish one semantic candidate globally and trigger vector sync."""

    result = store.publish_draft(draft_id, mode)
    if not result:
        raise HTTPException(status_code=404, detail="Semantic draft not found")
    draft, vector_job = result
    return {"draft": draft, "vector_job": vector_job}
