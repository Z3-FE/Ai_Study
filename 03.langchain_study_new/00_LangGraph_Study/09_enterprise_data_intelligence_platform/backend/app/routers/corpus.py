from fastapi import APIRouter, HTTPException

from ..models import DocumentCreate
from ..store import store

router = APIRouter(prefix="/corpus", tags=["corpus"])


@router.post("/documents")
def create_document(payload: DocumentCreate):
    """Register an uploaded metric or business semantics document."""

    document = store.create_document(payload)
    return {"document": document}


@router.post("/documents/{document_id}/extract-semantic-assets")
def extract_semantic_assets(document_id: str):
    """Extract candidate semantic assets from one document."""

    drafts = store.extract_semantic_drafts(document_id)
    if drafts is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"drafts": drafts}
