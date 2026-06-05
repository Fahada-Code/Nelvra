"""Add prompts and prompt_versions tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-05
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("variables", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("avg_quality_score", sa.Float(), nullable=True),
        sa.Column("avg_tokens", sa.Integer(), nullable=True),
        sa.Column("avg_cost_usd", sa.Float(), nullable=True),
        sa.Column("avg_latency_ms", sa.Integer(), nullable=True),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quality_trend", sa.String(20), nullable=False, server_default="stable"),
        sa.Column("drift_detected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("drift_explanation", sa.Text(), nullable=True),
        sa.Column("optimization_status", sa.String(20), nullable=False, server_default="none"),
        sa.Column("optimized_version", sa.Text(), nullable=True),
        sa.Column("optimization_savings", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_prompts_project_id", "prompts", ["project_id"])

    op.create_table(
        "prompt_versions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("prompt_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("prompts.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("change_note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_prompt_versions_prompt_id", "prompt_versions", ["prompt_id"])

    # Link LLM events to prompts
    op.add_column("llm_events", sa.Column(
        "prompt_version", sa.Integer(), nullable=True
    ))


def downgrade() -> None:
    op.drop_column("llm_events", "prompt_version")
    op.drop_table("prompt_versions")
    op.drop_table("prompts")
