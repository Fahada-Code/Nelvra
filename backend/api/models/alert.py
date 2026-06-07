from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Alert(TimestampMixin, Base):
    """User-defined threshold rule that triggers notifications."""

    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_project_id", "project_id"),)

    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # What to measure
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    # "gt" | "lt" | "gte" | "lte"
    operator: Mapped[str] = mapped_column(String(10), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    # Rolling window in minutes to evaluate the metric over
    window_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Notification channels
    notify_slack: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    slack_webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notify_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # State
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Consecutive windows in breach — used to avoid notification spam
    consecutive_breaches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class AlertIncident(TimestampMixin, Base):
    """A recorded breach of an Alert threshold."""

    __tablename__ = "alert_incidents"
    __table_args__ = (
        Index("ix_alert_incidents_alert_id", "alert_id"),
        Index("ix_alert_incidents_project_id", "project_id"),
    )

    alert_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("alerts.id"), nullable=False
    )
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    triggered_value: Mapped[float] = mapped_column(Float, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notification_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
