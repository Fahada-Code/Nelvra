from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AlertCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    metric: Literal["cost_usd", "error_rate", "latency_p95", "request_count", "quality_drift"]
    operator: Literal["gt", "lt", "gte", "lte"]
    threshold: float = Field(ge=0)
    window_minutes: int = Field(default=60, ge=1, le=1440)
    notify_slack: bool = False
    slack_webhook_url: str | None = Field(None, max_length=500)
    notify_email: bool = False
    email_address: str | None = Field(None, max_length=255)

    @model_validator(mode="after")
    def validate_notifications(self) -> "AlertCreate":
        if self.notify_slack and not self.slack_webhook_url:
            raise ValueError("slack_webhook_url required when notify_slack is true")
        if self.notify_email and not self.email_address:
            raise ValueError("email_address required when notify_email is true")
        return self


class AlertUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    threshold: float | None = Field(None, ge=0)
    window_minutes: int | None = Field(None, ge=1, le=1440)
    enabled: bool | None = None
    notify_slack: bool | None = None
    slack_webhook_url: str | None = Field(None, max_length=500)
    notify_email: bool | None = None
    email_address: str | None = Field(None, max_length=255)


class AlertResponse(BaseModel):
    id: str
    project_id: str
    name: str
    metric: str
    operator: str
    threshold: float
    window_minutes: int
    enabled: bool
    notify_slack: bool
    notify_email: bool
    last_triggered_at: datetime | None
    consecutive_breaches: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertIncidentResponse(BaseModel):
    id: str
    alert_id: str
    project_id: str
    triggered_value: float
    resolved_at: datetime | None
    notification_sent: bool
    created_at: datetime

    model_config = {"from_attributes": True}
