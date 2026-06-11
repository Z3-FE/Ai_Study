from fastapi import APIRouter

from ..store import store

router = APIRouter(prefix="/semantic/assets", tags=["semantic-assets"])


@router.get("/metrics")
def list_metric_assets():
    """List metrics used by the semantic asset management page."""

    return {"metrics": store.list_metric_assets()}


@router.get("/dimensions")
def list_dimension_assets():
    """List dimensions used by the semantic asset management page."""

    return {"dimensions": store.list_dimension_assets()}


@router.get("/datasets")
def list_dataset_assets():
    """List Olist dataset tables and field metadata."""

    return {"datasets": store.list_dataset_assets()}


@router.get("/glossary")
def list_glossary_assets():
    """List business terms and business rules used by the semantic layer."""

    return {"glossary": store.list_glossary_assets()}
