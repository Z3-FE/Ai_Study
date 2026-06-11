from fastapi import APIRouter

from ..database import check_database_connection
from ..store import store

router = APIRouter(prefix="/app", tags=["app"])


@router.get("/bootstrap")
def get_app_bootstrap():
    """Return initial app data used by the frontend shell."""

    return {
        "current_user": store.current_user,
        "data_sources": [store.data_source],
        "recent_conversations": store.list_conversations()[:5],
        "semantic_counts": store.semantic_counts(),
        "database": check_database_connection(),
    }
