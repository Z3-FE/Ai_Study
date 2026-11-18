from fastapi import APIRouter

from ..store import store

router = APIRouter(prefix="/semantic/assets", tags=["semantic-assets"])


@router.get("/metrics")
def list_metric_assets():
    """查询指标资产列表，供指标管理页面使用。"""

    return {"metrics": store.list_metric_assets()}


@router.get("/dimensions")
def list_dimension_assets():
    """查询维度资产列表，供维度管理页面使用。"""

    return {"dimensions": store.list_dimension_assets()}


@router.get("/datasets")
def list_dataset_assets():
    """查询 Olist 数据集表、字段和关联说明。"""

    return {"datasets": store.list_dataset_assets()}


@router.get("/glossary")
def list_glossary_assets():
    """查询业务术语和业务规则资产列表。"""

    return {"glossary": store.list_glossary_assets()}
