from pydantic import BaseModel


class HourlyBucket(BaseModel):
    hour: str
    requests: int
    cost_usd: float


class OverviewResponse(BaseModel):
    period_hours: int
    total_requests: int
    total_cost_usd: float
    avg_latency_ms: float
    error_count: int
    error_rate: float
    requests_by_model: dict[str, int]
    requests_by_provider: dict[str, int]
    cost_by_model: dict[str, float]
    hourly_requests: list[HourlyBucket]


class RequestSummary(BaseModel):
    id: str
    timestamp: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float | None
    latency_ms: int
    finish_reason: str
    environment: str
    feature: str | None
    prompt_id: str | None

    model_config = {"from_attributes": True}


class RequestsListResponse(BaseModel):
    items: list[RequestSummary]
    total: int
    page: int
    per_page: int
