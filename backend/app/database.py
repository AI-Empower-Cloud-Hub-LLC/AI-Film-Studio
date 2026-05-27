"""
Database — thin wrapper over the canonical app.db.session module.

Re-exports engine, SessionLocal, and get_db from the shared DB module so all
routes use a single engine/connection-pool. Adds create_tables() for
dev/test use only — production schema management is handled by Alembic.
"""
from sqlalchemy.orm import Session
from typing import Generator

from app.db.session import engine, SessionLocal, get_db  # noqa: F401 — canonical source


def create_tables() -> None:
    """Create all ORM-declared tables (dev/test only — use Alembic in production)."""
    import app.models  # noqa: F401 — registers models with Base.metadata
    from app.models.base import Base
    Base.metadata.create_all(bind=engine)


__all__ = ["engine", "SessionLocal", "get_db", "create_tables"]
