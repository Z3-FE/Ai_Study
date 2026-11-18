from fastapi import APIRouter

from ..models import VectorRebuildRequest, VectorSyncMode, VectorSyncRequest
from ..store import store

router = APIRouter(prefix="/vector", tags=["vector"])


@router.post("/assets/{asset_type}/{asset_id}/sync")
def sync_vector_asset(asset_type: str, asset_id: str, payload: VectorSyncRequest):
    """把单个语义资产同步到向量索引中。"""

    job = store.sync_vector_asset(asset_type, asset_id, payload.mode)
    return {"job": job}


@router.post("/rebuild")
def rebuild_vector_index(payload: VectorRebuildRequest | None = None):
    """手动重建向量索引，后续也可接入定时任务。"""

    request = payload or VectorRebuildRequest(mode=VectorSyncMode.async_)
    jobs = store.rebuild_vectors(request)
    return {"jobs": jobs}


@router.get("/jobs")
def list_vector_jobs():
    """查询向量同步和重建任务列表。"""

    return {"jobs": store.list_vector_jobs()}
