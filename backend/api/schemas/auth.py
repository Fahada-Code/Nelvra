from datetime import datetime

from pydantic import BaseModel, Field


class GitHubRegisterRequest(BaseModel):
    github_id: str = Field(max_length=50)
    github_login: str = Field(max_length=100)
    email: str | None = Field(None, max_length=255)
    name: str | None = Field(None, max_length=255)
    avatar_url: str | None = Field(None, max_length=500)


class UserResponse(BaseModel):
    id: str
    github_id: str
    github_login: str
    email: str | None
    name: str | None
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RegisterResponse(BaseModel):
    user: UserResponse
    project_id: str
    api_key: str | None  # None if key already existed and was not re-created
    existing_api_key_prefix: str | None  # Prefix for display if key already exists
