from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class NelvraEvent:
    """Represents a single LLM call to be sent to the Nelvra API."""

    timestamp: str
    model: str
    provider: str
    messages: list[dict[str, Any]]
    response_text: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    environment: str
    system_prompt: str | None = None
    prompt_id: str | None = None
    cost_usd: float | None = None
    user_id: str | None = None
    session_id: str | None = None
    feature: str | None = None
    tags: list[str] = field(default_factory=list)
    custom_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "provider": self.provider,
            "messages": self.messages,
            "response_text": self.response_text,
            "finish_reason": self.finish_reason,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "environment": self.environment,
            "system_prompt": self.system_prompt,
            "prompt_id": self.prompt_id,
            "cost_usd": self.cost_usd,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "feature": self.feature,
            "tags": self.tags,
            "custom_metadata": self.custom_metadata,
        }


# Pricing in USD per 1M tokens
COST_PER_1M_TOKENS: dict[str, dict[str, float]] = {
    # OpenAI
    "gpt-4o": {"input": 5.00, "output": 15.00},
    "gpt-4o-2024-08-06": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-4-turbo-preview": {"input": 10.00, "output": 30.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    # Anthropic
    "claude-opus-4-8": {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    """Returns cost in USD, or None if the model is not in the pricing table."""
    pricing = COST_PER_1M_TOKENS.get(model)
    if pricing is None:
        return None
    cost = (prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]) / 1_000_000
    return round(cost, 8)
