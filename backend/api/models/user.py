from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_github_id", "github_id", unique=True),)

    github_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    github_login: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
