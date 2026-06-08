import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from .base import Base


class PlanType(str, enum.Enum):
    free = "free"
    starter = "starter"
    professional = "professional"
    enterprise = "enterprise"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    refunded = "refunded"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True)
    plan: Mapped[PlanType] = mapped_column(SAEnum(PlanType), default=PlanType.free)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    films_limit: Mapped[int] = mapped_column(Integer, default=5)  # per month
    films_used: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[int] = mapped_column(Integer)  # cents
    currency: Mapped[str] = mapped_column(String(3), default="usd")
    status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus), default=PaymentStatus.pending)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


PLAN_DETAILS = {
    PlanType.free: {"name": "Free", "price": 0, "films_limit": 5, "features": ["5 films/month", "Basic agents", "Local TTS"]},
    PlanType.starter: {"name": "Starter", "price": 1999, "films_limit": 25, "features": ["25 films/month", "All 10 agents", "Google AI", "Priority support"]},
    PlanType.professional: {"name": "Professional", "price": 4999, "films_limit": 100, "features": ["100 films/month", "All 10 agents", "Claude AI", "ElevenLabs TTS", "Runway video", "Team collaboration"]},
    PlanType.enterprise: {"name": "Enterprise", "price": 0, "films_limit": -1, "features": ["Unlimited films", "Custom agents", "Dedicated support", "SLA", "Custom domain"]},
}
