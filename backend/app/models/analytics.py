import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50))  # film_created, login, export, upload, etc.
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DailyStat(Base):
    __tablename__ = "daily_stats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    films_created: Mapped[int] = mapped_column(Integer, default=0)
    users_registered: Mapped[int] = mapped_column(Integer, default=0)
    exports_count: Mapped[int] = mapped_column(Integer, default=0)
    uploads_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_pipeline_time: Mapped[float] = mapped_column(Float, default=0.0)
    total_scenes: Mapped[int] = mapped_column(Integer, default=0)
