"""Convert llm_events.timestamp from VARCHAR to TIMESTAMPTZ

Stored as a string the column forced every analytics/drift/alert query to cast
it, which prevented the (project_id, timestamp) btree index from serving range
scans. Switching to native TIMESTAMPTZ lets those range filters use the index.

Existing values are ISO-8601 strings written by the SDK, which PostgreSQL parses
directly via ::timestamptz.

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "llm_events",
        "timestamp",
        existing_type=sa.String(length=50),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=False,
        postgresql_using="timestamp::timestamptz",
    )


def downgrade() -> None:
    op.alter_column(
        "llm_events",
        "timestamp",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.String(length=50),
        existing_nullable=False,
        postgresql_using="timestamp::text",
    )
