from __future__ import annotations

import psycopg

from .settings import settings


def check_database_connection() -> dict[str, str | bool]:
    """Return a lightweight PostgreSQL connectivity check without failing app startup."""

    try:
        with psycopg.connect(settings.postgres_uri, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("select current_database(), current_user")
                database_name, user_name = cur.fetchone()

        return {
            "connected": True,
            "database": database_name,
            "user": user_name,
        }
    except Exception as exc:  # pragma: no cover - depends on local PostgreSQL state
        return {
            "connected": False,
            "error": str(exc),
        }
