from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin

# Hard limits per plan — enforced at ingestion time
PLAN_LIMITS = {
    "free":  {"events_per_month": 50_000,    "retention_days": 7},
    "pro":   {"events_per_month": 500_000,   "retention_days": 30},
    "team":  {"events_per_month": 5_000_000, "retention_days": 90},
}


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (Index("ix_subscriptions_user_id", "user_id", unique=True),)

    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, unique=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)

    # "free" | "pro" | "team"
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    # "active" | "canceled" | "past_due" | "trialing"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Cached usage counters — refreshed monthly
    events_this_month: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    events_month_key: Mapped[str | None] = mapped_column(String(7), nullable=True)  # "2026-06"
