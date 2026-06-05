"""
Tests for OpenAI and Anthropic instrumentation.

These tests mock the underlying LLM SDKs to verify that:
- Methods are wrapped correctly
- Events are captured with the right fields
- Streaming calls pass through unmodified
- Exceptions from the LLM call still propagate
- nelvra_metadata is extracted and mapped correctly
"""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nelvra.client import EventSender
from nelvra.types import NelvraEvent, calculate_cost


# ── OpenAI ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_sender():
    sender = MagicMock(spec=EventSender)
    return sender


@pytest.fixture
def mock_openai_response():
    response = MagicMock()
    response.model = "gpt-4o"
    response.choices = [MagicMock()]
    response.choices[0].message.content = "Hello!"
    response.choices[0].finish_reason = "stop"
    response.usage.prompt_tokens = 10
    response.usage.completion_tokens = 5
    response.usage.total_tokens = 15
    return response


def test_openai_instrument_patches_sync(mock_sender):
    from nelvra.instruments.openai import instrument_openai

    with patch("openai.resources.chat.completions.Completions.create") as mock_create:
        mock_create.return_value = MagicMock(
            model="gpt-4o",
            choices=[MagicMock(message=MagicMock(content="hi"), finish_reason="stop")],
            usage=MagicMock(prompt_tokens=5, completion_tokens=3, total_tokens=8),
        )
        instrument_openai(mock_sender, "production")

        from openai.resources.chat.completions import Completions
        assert Completions.create.__name__ == "patched_create"


def test_openai_event_captured(mock_sender):
    from nelvra.instruments.openai import instrument_openai

    fake_response = MagicMock()
    fake_response.model = "gpt-4o"
    fake_response.choices = [MagicMock()]
    fake_response.choices[0].message.content = "Answer text"
    fake_response.choices[0].finish_reason = "stop"
    fake_response.usage.prompt_tokens = 20
    fake_response.usage.completion_tokens = 10
    fake_response.usage.total_tokens = 30

    with patch(
        "openai.resources.chat.completions.Completions.create",
        return_value=fake_response,
    ):
        instrument_openai(mock_sender, "staging")

        from openai.resources.chat.completions import Completions
        comp = Completions.__new__(Completions)
        comp.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "What is 2+2?"}],
        )

    mock_sender.enqueue.assert_called_once()
    event: NelvraEvent = mock_sender.enqueue.call_args[0][0]
    assert event.model == "gpt-4o"
    assert event.provider == "openai"
    assert event.prompt_tokens == 20
    assert event.completion_tokens == 10
    assert event.environment == "staging"
    assert event.response_text == "Answer text"


def test_openai_nelvra_metadata_extracted(mock_sender):
    from nelvra.instruments.openai import instrument_openai

    fake_response = MagicMock()
    fake_response.model = "gpt-4o"
    fake_response.choices = [MagicMock()]
    fake_response.choices[0].message.content = "ok"
    fake_response.choices[0].finish_reason = "stop"
    fake_response.usage.prompt_tokens = 5
    fake_response.usage.completion_tokens = 2
    fake_response.usage.total_tokens = 7

    with patch(
        "openai.resources.chat.completions.Completions.create",
        return_value=fake_response,
    ):
        instrument_openai(mock_sender, "production")

        from openai.resources.chat.completions import Completions
        comp = Completions.__new__(Completions)
        # nelvra_metadata should be stripped before reaching the real API
        comp.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            nelvra_metadata={
                "user_id": "user_123",
                "feature": "support_chat",
                "tags": ["v2"],
            },
        )

    event: NelvraEvent = mock_sender.enqueue.call_args[0][0]
    assert event.user_id == "user_123"
    assert event.feature == "support_chat"
    assert event.tags == ["v2"]


def test_openai_streaming_not_instrumented(mock_sender):
    """Streaming calls must pass through without event capture."""
    from nelvra.instruments.openai import instrument_openai

    stream_sentinel = object()

    with patch(
        "openai.resources.chat.completions.Completions.create",
        return_value=stream_sentinel,
    ):
        instrument_openai(mock_sender, "production")

        from openai.resources.chat.completions import Completions
        comp = Completions.__new__(Completions)
        result = comp.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hi"}],
            stream=True,
        )

    assert result is stream_sentinel
    mock_sender.enqueue.assert_not_called()


def test_openai_exception_propagates(mock_sender):
    """Exceptions from the LLM call must still reach the caller."""
    from nelvra.instruments.openai import instrument_openai

    with patch(
        "openai.resources.chat.completions.Completions.create",
        side_effect=RuntimeError("API error"),
    ):
        instrument_openai(mock_sender, "production")

        from openai.resources.chat.completions import Completions
        comp = Completions.__new__(Completions)
        with pytest.raises(RuntimeError, match="API error"):
            comp.create(model="gpt-4o", messages=[])


# ── Anthropic ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_anthropic_response():
    response = MagicMock()
    response.model = "claude-3-5-sonnet-20241022"
    response.content = [MagicMock(text="Sure, I can help!")]
    response.stop_reason = "end_turn"
    response.usage.input_tokens = 12
    response.usage.output_tokens = 8
    return response


def test_anthropic_event_captured(mock_sender, mock_anthropic_response):
    from nelvra.instruments.anthropic import instrument_anthropic

    with patch(
        "anthropic.resources.messages.Messages.create",
        return_value=mock_anthropic_response,
    ):
        instrument_anthropic(mock_sender, "production")

        from anthropic.resources.messages import Messages
        msgs = Messages.__new__(Messages)
        msgs.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Help me"}],
            system="You are helpful.",
        )

    mock_sender.enqueue.assert_called_once()
    event: NelvraEvent = mock_sender.enqueue.call_args[0][0]
    assert event.provider == "anthropic"
    assert event.model == "claude-3-5-sonnet-20241022"
    assert event.system_prompt == "You are helpful."
    assert event.prompt_tokens == 12
    assert event.completion_tokens == 8
    assert event.total_tokens == 20
    assert "help" in event.response_text.lower()


def test_anthropic_streaming_not_instrumented(mock_sender):
    from nelvra.instruments.anthropic import instrument_anthropic

    stream_sentinel = object()
    with patch(
        "anthropic.resources.messages.Messages.create",
        return_value=stream_sentinel,
    ):
        instrument_anthropic(mock_sender, "production")

        from anthropic.resources.messages import Messages
        msgs = Messages.__new__(Messages)
        result = msgs.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[],
            stream=True,
        )

    assert result is stream_sentinel
    mock_sender.enqueue.assert_not_called()


def test_anthropic_exception_propagates(mock_sender):
    from nelvra.instruments.anthropic import instrument_anthropic

    with patch(
        "anthropic.resources.messages.Messages.create",
        side_effect=ValueError("Bad request"),
    ):
        instrument_anthropic(mock_sender, "production")

        from anthropic.resources.messages import Messages
        msgs = Messages.__new__(Messages)
        with pytest.raises(ValueError, match="Bad request"):
            msgs.create(model="claude-3-5-sonnet-20241022", max_tokens=100, messages=[])


# ── Cost calculation ─────────────────────────────────────────────────────────


def test_cost_known_model():
    cost = calculate_cost("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    # 1000 * 5.00/1M + 500 * 15.00/1M = 0.005 + 0.0075 = 0.0125
    assert cost == pytest.approx(0.0125, rel=1e-5)


def test_cost_unknown_model():
    cost = calculate_cost("some-future-model", prompt_tokens=100, completion_tokens=50)
    assert cost is None


def test_cost_anthropic_model():
    cost = calculate_cost("claude-3-5-sonnet-20241022", prompt_tokens=500, completion_tokens=200)
    # 500 * 3.00/1M + 200 * 15.00/1M = 0.0015 + 0.003 = 0.0045
    assert cost == pytest.approx(0.0045, rel=1e-5)
