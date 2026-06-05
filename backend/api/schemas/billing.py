from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    current_period_end: datetime | None
    cancel_at_period_end: bool
    events_this_month: int
    events_limit: int
    retention_days: int

    model_config = {"from_attributes": True}


class CheckoutRequest(BaseModel):
    plan: Literal["pro", "team"]
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str


class UsageResponse(BaseModel):
    events_this_month: int
    events_limit: int
    pct_used: float
    plan: str
