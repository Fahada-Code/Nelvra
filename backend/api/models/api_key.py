from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class ApiKey(TimestampMixin, Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("ix_api_keys_project_id", "project_id"),
        Index("ix_api_keys_key_prefix", "key_prefix"),
    )

    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # SHA-256 of the full key — never store the plaintext key
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    # First 8 hex chars after "nvl_live_" prefix — used for fast lookup
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
