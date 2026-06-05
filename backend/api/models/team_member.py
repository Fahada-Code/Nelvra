from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class TeamMember(TimestampMixin, Base):
    __tablename__ = "team_members"
    __table_args__ = (
        Index("ix_team_members_project_id", "project_id"),
        Index("ix_team_members_user_id", "user_id"),
        UniqueConstraint("project_id", "user_id", name="uq_team_members_project_user"),
    )

    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    # "owner" | "admin" | "member" | "viewer"
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")
    invited_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
