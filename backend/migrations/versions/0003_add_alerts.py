"""Add alerts and alert_incidents tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-05
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("metric", sa.String(50), nullable=False),
        sa.Column("operator", sa.String(10), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("window_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_slack", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("slack_webhook_url", sa.String(500), nullable=True),
        sa.Column("notify_email", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("email_address", sa.String(255), nullable=True),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_breaches", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alerts_project_id", "alerts", ["project_id"])

    op.create_table(
        "alert_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("alert_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("alerts.id"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("triggered_value", sa.Float(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notification_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alert_incidents_alert_id", "alert_incidents", ["alert_id"])
    op.create_index("ix_alert_incidents_project_id", "alert_incidents", ["project_id"])


def downgrade() -> None:
    op.drop_table("alert_incidents")
    op.drop_table("alerts")
