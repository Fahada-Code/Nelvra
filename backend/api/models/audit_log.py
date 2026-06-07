from typing import Any

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class AuditLog(TimestampMixin, Base):
    """Immutable record of every write operation — never soft-deleted."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_project_id", "project_id"),
        Index("ix_audit_logs_user_id", "user_id"),
    )

    project_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )
    # e.g. "api_key.created", "alert.triggered", "prompt.deployed"
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. "api_key", "alert", "prompt", "project"
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    details: Mapped[Any] = mapped_column(JSONB, nullable=False, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
