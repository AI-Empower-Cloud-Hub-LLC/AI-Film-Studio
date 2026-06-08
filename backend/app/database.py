"""
Database — thin wrapper over the canonical app.db.session module.

Re-exports engine, SessionLocal, and get_db from the shared DB module so all
routes use a single engine/connection-pool. Adds create_tables() for
dev/test use only — production schema management is handled by Alembic.
"""
import logging
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from typing import Generator

from app.db.session import engine, SessionLocal, get_db  # noqa: F401 — canonical source

logger = logging.getLogger(__name__)


def _migrate_missing_columns() -> None:
    """Add any columns declared in the ORM but missing from the DB (SQLite only)."""
    from app.core.config import settings
    db_url = str(settings.DATABASE_URL)
    if not db_url.startswith("sqlite"):
        return
    from app.models.base import Base
    insp = inspect(engine)
    for table_name, table in Base.metadata.tables.items():
        if not insp.has_table(table_name):
            continue
        existing = {col["name"] for col in insp.get_columns(table_name)}
        for column in table.columns:
            if column.name not in existing:
                col_type = column.type.compile(engine.dialect)
                with engine.begin() as conn:
                    conn.execute(text(
                        f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}"
                    ))
                logger.info("Added column %s.%s (%s)", table_name, column.name, col_type)


def create_tables() -> None:
    """Create all ORM-declared tables (dev/test only — use Alembic in production)."""
    import app.models  # noqa: F401 — registers models with Base.metadata
    from app.models.base import Base
    Base.metadata.create_all(bind=engine)
    _migrate_missing_columns()


__all__ = ["engine", "SessionLocal", "get_db", "create_tables"]
