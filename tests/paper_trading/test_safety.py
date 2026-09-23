"""
Tests for Phase 8 Execution Safety & ExecutionGuard.
"""

import pytest

from src.paper_trading.execution_guard import ExecutionGuard, LiveExecutionDisabledError
from src.paper_trading.models import (
    PaperExecutionMode,
    PaperOrder,
    PaperOrderSide,
    PaperOrderType,
)


def test_guard_constants():
    """Verify hard-coded safety flags."""
    assert ExecutionGuard.is_live_enabled() is False

    status = ExecutionGuard.get_execution_status()
    assert status["LIVE_EXECUTION"] == "DISABLED"
    assert status["BROKER_CONNECTIONS"] == "NONE"
    assert status["PAPER_EXECUTION"] == "ENABLED"
    assert status["ALLOW_LIVE_EXECUTION"] is False


def test_guard_rejects_live_mode():
    """Verify validate_execution_mode raises LiveExecutionDisabledError on live attempts."""
    # Valid paper mode
    ExecutionGuard.validate_execution_mode("PAPER")
    ExecutionGuard.validate_execution_mode("BACKTEST")

    # Invalid live modes
    with pytest.raises(LiveExecutionDisabledError) as exc_info:
        ExecutionGuard.validate_execution_mode("LIVE")
    assert "LIVE EXECUTION IS NOT IMPLEMENTED" in str(exc_info.value)

    with pytest.raises(LiveExecutionDisabledError):
        ExecutionGuard.validate_execution_mode("REAL")

    with pytest.raises(LiveExecutionDisabledError):
        ExecutionGuard.validate_execution_mode("PRODUCTION")


def test_assert_paper_mode():
    """Verify assert_paper_mode runs without error in standard configuration."""
    ExecutionGuard.assert_paper_mode()


def test_live_execution_error():
    """Verify LiveExecutionDisabledError behaves as standard exception."""
    err = LiveExecutionDisabledError("Live trading blocked")
    assert "Live trading blocked" in str(err)
