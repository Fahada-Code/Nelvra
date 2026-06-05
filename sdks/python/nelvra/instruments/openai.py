"""
Auto-instrumentation for the OpenAI Python SDK (v1+).

Wraps Completions.create and AsyncCompletions.create to capture every chat
completion call as a NelvraEvent. Streaming calls (stream=True) are passed
through untouched — streaming instrumentation is out of scope for v1.
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


def instrument_openai(sender: "EventSender", environment: str) -> None:
    """Monkey-patches the OpenAI SDK. Safe to call multiple times."""
    global _sender, _environment, _patched
    if _patched:
        return

    try:
        from openai.resources.chat.completions import AsyncCompletions, Completions
    except ImportError:
        return  # openai not installed — skip silently

    _sender = sender
    _environment = environment

    _original_create = Completions.create
    _original_acreate = AsyncCompletions.create

    def patched_create(self: Any, *args: Any, **kwargs: Any) -> Any:
        if kwargs.get("stream"):
            return _original_create(self, *args, **kwargs)

        nelvra_meta: dict[str, Any] = kwargs.pop("nelvra_metadata", {})
        start = time.monotonic()
        response = _original_create(self, *args, **kwargs)
        latency_ms = int((time.monotonic() - start) * 1000)
        _capture_openai_response(kwargs, response, latency_ms, nelvra_meta)
        return response

    async def patched_acreate(self: Any, *args: Any, **kwargs: Any) -> Any:
        if kwargs.get("stream"):
            return await _original_acreate(self, *args, **kwargs)

        nelvra_meta: dict[str, Any] = kwargs.pop("nelvra_metadata", {})
        start = time.monotonic()
        response = await _original_acreate(self, *args, **kwargs)
        latency_ms = int((time.monotonic() - start) * 1000)
        _capture_openai_response(kwargs, response, latency_ms, nelvra_meta)
        return response

    Completions.create = patched_create  # type: ignore[method-assign]
    AsyncCompletions.create = patched_acreate  # type: ignore[method-assign]
    _patched = True


def _capture_openai_response(
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
        model: str = response.model or kwargs.get("model", "unknown")
        usage = response.usage

        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0

        choice = response.choices[0] if response.choices else None
        response_text = choice.message.content or "" if choice else ""
        finish_reason = choice.finish_reason or "unknown" if choice else "unknown"

        # Extract system prompt from messages if present (OpenAI embeds it in messages)
        system_prompt: str | None = None
        user_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
            else:
                user_messages.append(msg)

        event = NelvraEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            model=model,
            provider="openai",
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
        # Instrumentation errors must never surface to the caller
        warnings.warn("Nelvra: error capturing OpenAI event", stacklevel=3)


def _reset_for_testing() -> None:
    """Restores original methods. Used in tests only."""
    global _patched, _sender
    if not _patched:
        return
    try:
        from openai.resources.chat.completions import AsyncCompletions, Completions
        # Re-import originals by removing our wrappers
        # The simplest approach: reload the module
        import importlib
        import openai.resources.chat.completions as mod
        importlib.reload(mod)
    except Exception:
        pass
    _patched = False
    _sender = None
