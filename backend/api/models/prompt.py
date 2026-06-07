from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Prompt(TimestampMixin, Base):
    """A tracked prompt template with analytics, drift state, and optimization state."""

    __tablename__ = "prompts"
    __table_args__ = (Index("ix_prompts_project_id", "project_id"),)

    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[Any] = mapped_column(JSONB, nullable=False, default=list)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Cached analytics — updated by background worker
    avg_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Drift state
    # "stable" | "degrading" | "improving"
    quality_trend: Mapped[str] = mapped_column(String(20), nullable=False, default="stable")
    drift_detected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    drift_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optimization state
    # "none" | "suggested" | "testing" | "deployed"
    optimization_status: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    optimized_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Estimated token reduction percentage
    optimization_savings: Mapped[float | None] = mapped_column(Float, nullable=True)


class PromptVersion(TimestampMixin, Base):
    """Immutable version history for a prompt."""

    __tablename__ = "prompt_versions"
    __table_args__ = (Index("ix_prompt_versions_prompt_id", "prompt_id"),)

    prompt_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("prompts.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    change_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
