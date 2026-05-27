"""
Database — thin wrapper over the canonical app.db.session module.

Re-exports engine, SessionLocal, and get_db from the shared DB module so all
routes use a single engine/connection-pool. Adds create_tables() for
dev/test use only — production schema management is handled by Alembic.
"""
import logging
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.models.base import Base

logger = logging.getLogger(__name__)

# Allow DATABASE_URL to be overridden via env; default to local SQLite for development.
_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_film_studio.db")

# SQLite needs check_same_thread=False; the connect_args key is ignored by other drivers.
_connect_args = {"check_same_thread": False} if _DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(_DATABASE_URL, connect_args=_connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_missing_columns() -> None:
    """Add any columns declared in the ORM but missing from the DB (SQLite only)."""
    if not _DATABASE_URL.startswith("sqlite"):
        return
    inspector = inspect(engine)
    for table_name, table in Base.metadata.tables.items():
        if not inspector.has_table(table_name):
            continue
        existing = {col["name"] for col in inspector.get_columns(table_name)}
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
