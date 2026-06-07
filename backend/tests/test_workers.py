"""Unit tests for pure worker helper functions (no DB, no broker, no network)."""

from workers.alert_dispatcher import _check_threshold
from workers.drift_detector import _fallback_explanation
from workers.prompt_optimizer import _estimate_savings
from workers.quality_evaluator import _format_conversation


class TestCheckThreshold:
    def test_gt(self):
        assert _check_threshold(5.0, "gt", 3.0) is True
        assert _check_threshold(2.0, "gt", 3.0) is False

    def test_lt(self):
        assert _check_threshold(2.0, "lt", 3.0) is True
        assert _check_threshold(5.0, "lt", 3.0) is False

    def test_gte_lte_boundaries(self):
        assert _check_threshold(3.0, "gte", 3.0) is True
        assert _check_threshold(3.0, "lte", 3.0) is True
        assert _check_threshold(3.0, "gt", 3.0) is False

    def test_unknown_operator_is_false(self):
        assert _check_threshold(5.0, "eq", 3.0) is False


class TestEstimateSavings:
    def test_shorter_prompt_yields_positive_savings(self):
        # optimized is half the length -> (1 - 0.5) * 0.4 * 100 = 20%
        savings = _estimate_savings("x" * 100, "x" * 50, avg_tokens=1000)
        assert savings == 20.0

    def test_longer_prompt_yields_zero(self):
        assert _estimate_savings("x" * 100, "x" * 200, avg_tokens=1000) == 0.0

    def test_zero_tokens_yields_zero(self):
        assert _estimate_savings("x" * 100, "x" * 50, avg_tokens=0) == 0.0

    def test_empty_inputs_yield_zero(self):
        assert _estimate_savings("", "shorter", avg_tokens=1000) == 0.0


class TestFormatConversation:
    def test_includes_system_and_messages(self):
        out = _format_conversation(
            [{"role": "user", "content": "hello there"}], system_prompt="be brief"
        )
        assert "[System]: be brief" in out
        assert "[User]: hello there" in out

    def test_handles_block_content(self):
        out = _format_conversation(
            [{"role": "assistant", "content": [{"type": "text", "text": "block answer"}]}],
            system_prompt=None,
        )
        assert "block answer" in out

    def test_only_keeps_last_five_messages(self):
        messages = [{"role": "user", "content": f"msg{i}"} for i in range(7)]
        out = _format_conversation(messages, system_prompt=None)
        assert "msg0" not in out
        assert "msg1" not in out
        assert "msg6" in out

    def test_empty_messages(self):
        assert _format_conversation([], system_prompt=None) == ""


class TestFallbackExplanation:
    def test_contains_numbers(self):
        msg = _fallback_explanation(drop_pct=23.0, avg_7d=0.90, avg_24h=0.70)
        assert "23.0%" in msg
        assert "0.90" in msg
        assert "0.70" in msg
