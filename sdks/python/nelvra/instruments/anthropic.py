"""
Auto-instrumentation for the Anthropic Python SDK (v0.25+).

Wraps Messages.create and AsyncMessages.create to capture every messages
API call. Streaming calls (stream=True) are passed through untouched.
"""
import time
import warnings
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import EventSender

_sender: "EventSender | None" = None
_environment: str = "production"
_patched = False


def instrument_anthropic(sender: "EventSender", environment: str) -> None:
    """Monkey-patches the Anthropic SDK. Safe to call multiple times."""
    global _sender, _environment, _patched
    if _patched:
        return

    try:
        from anthropic.resources.messages import AsyncMessages, Messages
    except ImportError:
        return  # anthropic not installed — skip silently

    _sender = sender
    _environment = environment

    _original_create = Messages.create
    _original_acreate = AsyncMessages.create

    def patched_create(self: Any, *args: Any, **kwargs: Any) -> Any:
        if kwargs.get("stream"):
            return _original_create(self, *args, **kwargs)

        nelvra_meta: dict[str, Any] = kwargs.pop("nelvra_metadata", {})
        start = time.monotonic()
        response = _original_create(self, *args, **kwargs)
        latency_ms = int((time.monotonic() - start) * 1000)
        _capture_anthropic_response(kwargs, response, latency_ms, nelvra_meta)
        return response

    async def patched_acreate(self: Any, *args: Any, **kwargs: Any) -> Any:
        if kwargs.get("stream"):
            return await _original_acreate(self, *args, **kwargs)

        nelvra_meta: dict[str, Any] = kwargs.pop("nelvra_metadata", {})
        start = time.monotonic()
        response = await _original_acreate(self, *args, **kwargs)
        latency_ms = int((time.monotonic() - start) * 1000)
        _capture_anthropic_response(kwargs, response, latency_ms, nelvra_meta)
        return response

    Messages.create = patched_create  # type: ignore[method-assign]
    AsyncMessages.create = patched_acreate  # type: ignore[method-assign]
    _patched = True


def _capture_anthropic_response(
    kwargs: dict[str, Any],
    response: Any,
    latency_ms: int,
    nelvra_meta: dict[str, Any],
) -> None:
    if _sender is None:
        return

    try:
        from ..types import NelvraEvent, calculate_cost

        messages: list[dict[str, Any]] = kwargs.get("messages", [])
        system_prompt: str | None = kwargs.get("system")
        model: str = response.model or kwargs.get("model", "unknown")
        usage = response.usage

        prompt_tokens = usage.input_tokens if usage else 0
        completion_tokens = usage.output_tokens if usage else 0
        total_tokens = prompt_tokens + completion_tokens

        response_text = ""
        if response.content:
            text_blocks = [b.text for b in response.content if hasattr(b, "text")]
            response_text = "".join(text_blocks)

        finish_reason = response.stop_reason or "unknown"

        event = NelvraEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            model=model,
            provider="anthropic",
            messages=messages,
            system_prompt=system_prompt,
            response_text=response_text,
            finish_reason=finish_reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=calculate_cost(model, prompt_tokens, completion_tokens),
            latency_ms=latency_ms,
            environment=_environment,
            prompt_id=nelvra_meta.get("prompt_id"),
            user_id=nelvra_meta.get("user_id"),
            session_id=nelvra_meta.get("session_id"),
            feature=nelvra_meta.get("feature"),
            tags=nelvra_meta.get("tags", []),
            custom_metadata=nelvra_meta.get("metadata", {}),
        )
        _sender.enqueue(event)
    except Exception:
        warnings.warn("Nelvra: error capturing Anthropic event", stacklevel=3)


def _reset_for_testing() -> None:
    """Restores original methods. Used in tests only."""
    global _patched, _sender
    if not _patched:
        return
    try:
        import importlib
        import anthropic.resources.messages as mod
        importlib.reload(mod)
    except Exception:
        pass
    _patched = False
    _sender = None
