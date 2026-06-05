from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PromptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    variables: list[str] = Field(default_factory=list)


class PromptUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = Field(None, min_length=1)
    variables: list[str] | None = None
    change_note: str | None = Field(None, max_length=500)


class PromptResponse(BaseModel):
    id: str
    project_id: str
    name: str
    content: str
    variables: list[str]
    version: int
    avg_quality_score: float | None
    avg_tokens: int | None
    avg_cost_usd: float | None
    avg_latency_ms: int | None
    request_count: int
    quality_trend: str
    drift_detected_at: datetime | None
    drift_explanation: str | None
    optimization_status: str
    optimized_version: str | None
    optimization_savings: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PromptVersionResponse(BaseModel):
    id: str
    prompt_id: str
    version: int
    content: str
    change_note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeployOptimizationRequest(BaseModel):
    confirm: bool = Field(..., description="Must be true to deploy")
