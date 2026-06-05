from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TeamMemberInvite(BaseModel):
    github_login: str = Field(min_length=1, max_length=100)
    role: Literal["admin", "member", "viewer"] = "member"


class TeamMemberUpdate(BaseModel):
    role: Literal["admin", "member", "viewer"]


class TeamMemberResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: str
    joined_at: datetime | None
    created_at: datetime

    # Populated from user join
    github_login: str | None = None
    name: str | None = None
    avatar_url: str | None = None

    model_config = {"from_attributes": True}
