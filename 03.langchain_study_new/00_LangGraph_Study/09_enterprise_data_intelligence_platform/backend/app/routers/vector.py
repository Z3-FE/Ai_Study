from fastapi import APIRouter

from ..models import VectorRebuildRequest, VectorSyncMode, VectorSyncRequest
from ..store import store

router = APIRouter(prefix="/vector", tags=["vector"])


@router.post("/assets/{asset_type}/{asset_id}/sync")
def sync_vector_asset(asset_type: str, asset_id: str, payload: VectorSyncRequest):
    """Synchronize one semantic asset into the vector index."""

    job = store.sync_vector_asset(asset_type, asset_id, payload.mode)
    return {"job": job}


@router.post("/rebuild")
def rebuild_vector_index(payload: VectorRebuildRequest | None = None):
    """Rebuild vector index manually; later this can also be called by a scheduler."""

    request = payload or VectorRebuildRequest(mode=VectorSyncMode.async_)
    jobs = store.rebuild_vectors(request)
    return {"jobs": jobs}


@router.get("/jobs")
def list_vector_jobs():
    """List vector sync and rebuild jobs."""

    return {"jobs": store.list_vector_jobs()}
