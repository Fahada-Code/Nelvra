from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class LLMEventCreate(BaseModel):
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone(cls, ts: datetime) -> datetime:
        # Treat naive timestamps as UTC so they store unambiguously in TIMESTAMPTZ.
        if ts.tzinfo is None:
            return ts.replace(tzinfo=UTC)
        return ts.astimezone(UTC)

    model: str = Field(max_length=100)
    provider: Literal["openai", "anthropic"]
    prompt_id: str | None = Field(None, max_length=255)
    messages: list[dict[str, Any]] = Field(min_length=1)
    system_prompt: str | None = None
    response_text: str
    finish_reason: str = Field(max_length=50)
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cost_usd: float | None = Field(None, ge=0)
    latency_ms: int = Field(ge=0)
    user_id: str | None = Field(None, max_length=255)
    session_id: str | None = Field(None, max_length=255)
    feature: str | None = Field(None, max_length=255)
    environment: Literal["production", "staging", "development"] = "production"
    tags: list[str] = Field(default_factory=list, max_length=20)
    custom_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        for tag in tags:
            if len(tag) > 100:
                raise ValueError("Each tag must be 100 characters or fewer")
        return tags

    @field_validator("total_tokens")
    @classmethod
    def validate_total_tokens(cls, total: int, info: Any) -> int:
        prompt = info.data.get("prompt_tokens", 0)
        completion = info.data.get("completion_tokens", 0)
        if total < prompt + completion:
            raise ValueError("total_tokens must be >= prompt_tokens + completion_tokens")
        return total


class LLMEventBatchCreate(BaseModel):
    events: list[LLMEventCreate] = Field(min_length=1, max_length=100)


class LLMEventResponse(BaseModel):
    id: str
    project_id: str
    timestamp: datetime
    model: str
    provider: str
    prompt_id: str | None
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float | None
    latency_ms: int
    user_id: str | None
    session_id: str | None
    feature: str | None
    environment: str
    tags: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class LLMEventDetailResponse(LLMEventResponse):
    """Full event data including messages and response — used for single-event views."""

    messages: list[dict[str, Any]]
    system_prompt: str | None
    response_text: str
    quality_score: float | None
    quality_flags: list[str] | None
    custom_metadata: dict[str, Any]


class LLMEventBatchResponse(BaseModel):
    created: int
    ids: list[str]
