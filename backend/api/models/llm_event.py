from typing import Any

from sqlalchemy import Float, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class LLMEvent(TimestampMixin, Base):
    __tablename__ = "llm_events"
    __table_args__ = (
        # Compound index covers time-range queries scoped to a project
        Index("ix_llm_events_project_timestamp", "project_id", "timestamp"),
        Index("ix_llm_events_project_model", "project_id", "model"),
        Index("ix_llm_events_project_environment", "project_id", "environment"),
        Index("ix_llm_events_prompt_id", "prompt_id"),
    )

    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False
    )
    # Caller-provided timestamp — preserves the actual event time even if ingestion is delayed
    timestamp: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    messages: Mapped[Any] = mapped_column(JSONB, nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    finish_reason: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(12, 8), nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    feature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    environment: Mapped[str] = mapped_column(String(50), nullable=False, default="production")
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_flags: Mapped[Any] = mapped_column(JSONB, nullable=True)
    tags: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    custom_metadata: Mapped[Any] = mapped_column(JSONB, nullable=False, default=dict)
