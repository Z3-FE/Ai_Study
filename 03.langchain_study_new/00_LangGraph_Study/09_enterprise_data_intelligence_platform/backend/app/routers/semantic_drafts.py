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
    """查询文档提取出的候选语义资产，可按审核状态过滤。"""

    return {"drafts": store.list_drafts(status)}


@router.patch("/{draft_id}")
def update_semantic_draft(draft_id: str, payload: SemanticDraftUpdate):
    """在采用或发布前编辑候选语义资产。"""

    draft = store.update_draft(draft_id, payload)
    if not draft:
        raise HTTPException(status_code=404, detail="Semantic draft not found")
    return {"draft": draft}


@router.post("/{draft_id}/adopt")
def adopt_semantic_draft(draft_id: str, payload: SemanticDraftReview):
    """把某个候选语义资产采用到当前会话上下文中。"""

    draft = store.adopt_draft(draft_id, payload)
    if not draft:
        raise HTTPException(status_code=404, detail="Semantic draft not found")
    return {"draft": draft}


@router.post("/{draft_id}/reject")
def reject_semantic_draft(draft_id: str):
    """驳回某个候选语义资产。"""

    draft = store.reject_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Semantic draft not found")
    return {"draft": draft}


@router.post("/{draft_id}/publish")
def publish_semantic_draft(draft_id: str, mode: VectorSyncMode = VectorSyncMode.sync):
    """将候选语义资产发布为全局资产，并触发向量索引同步。"""

    result = store.publish_draft(draft_id, mode)
    if not result:
        raise HTTPException(status_code=404, detail="Semantic draft not found")
    draft, vector_job = result
    return {"draft": draft, "vector_job": vector_job}
