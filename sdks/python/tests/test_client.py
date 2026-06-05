import pytest
from unittest.mock import MagicMock, patch

from nelvra import Nelvra
from nelvra.client import EventSender
from nelvra.types import NelvraEvent


def test_nelvra_requires_api_key():
    with pytest.raises(ValueError, match="api_key is required"):
        Nelvra(api_key="")


def test_nelvra_sets_instance():
    client = Nelvra(api_key="nvl_live_" + "a" * 32)
    assert Nelvra.get_instance() is client


def test_nelvra_instrument_idempotent():
    client = Nelvra(api_key="nvl_live_" + "a" * 32, api_url="http://localhost:8000")
    client.instrument()
    assert client._instrumented is True
    # Calling again should not raise or re-patch
    client.instrument()
    assert client._instrumented is True


def test_event_sender_enqueue_does_not_block():
    """Enqueueing an event must return immediately without network I/O."""
    sender = EventSender(api_key="test", api_url="http://localhost:1")
    event = NelvraEvent(
        timestamp="2024-01-01T00:00:00Z",
        model="gpt-4o",
        provider="openai",
        messages=[{"role": "user", "content": "hi"}],
        response_text="hello",
        finish_reason="stop",
        prompt_tokens=5,
        completion_tokens=3,
        total_tokens=8,
        latency_ms=100,
        environment="production",
    )
    # Should return immediately
    sender.enqueue(event)


def test_event_sender_queue_full_drops_silently():
    """A full queue should drop events without raising an exception."""
    import queue as _queue
    sender = EventSender(api_key="test", api_url="http://localhost:1")
    # Fill the queue
    sender._queue = _queue.Queue(maxsize=1)
    sender._queue.put_nowait({"dummy": True})

    event = NelvraEvent(
        timestamp="2024-01-01T00:00:00Z",
        model="gpt-4o",
        provider="openai",
        messages=[],
        response_text="",
        finish_reason="stop",
        prompt_tokens=1,
        completion_tokens=1,
        total_tokens=2,
        latency_ms=1,
        environment="production",
    )
    # Must not raise
    sender.enqueue(event)


def test_event_sender_warns_on_send_failure():
    """A failed HTTP send should issue a warning, not raise."""
    sender = EventSender(api_key="invalid", api_url="http://localhost:1")
    with pytest.warns(UserWarning, match="Nelvra"):
        sender._send([{"model": "gpt-4o"}])


def test_nelvra_event_to_dict():
    event = NelvraEvent(
        timestamp="2024-01-01T00:00:00Z",
        model="gpt-4o",
        provider="openai",
        messages=[{"role": "user", "content": "hello"}],
        response_text="world",
        finish_reason="stop",
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        latency_ms=300,
        environment="production",
        feature="chat",
    )
    d = event.to_dict()
    assert d["model"] == "gpt-4o"
    assert d["feature"] == "chat"
    assert d["tags"] == []
    assert d["custom_metadata"] == {}
