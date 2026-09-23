"""
Tests for PaperRiskManager in Phase 8.
"""

import pytest

from src.paper_trading.models import (
    PaperOrder,
    PaperOrderSide,
    PaperOrderType,
    PaperPosition,
)
from src.paper_trading.risk_manager import PaperRiskManager


@pytest.fixture
def risk_manager():
    return PaperRiskManager(
        max_position_size_lots=10,
        max_open_positions=3,
        max_risk_per_trade_pct=5.0,
        max_daily_loss_pct=3.0,
        max_portfolio_drawdown_pct=10.0,
        lot_size=25,
    )


def test_order_within_limits_approved(risk_manager):
    """Order complying with all paper limits must be approved."""
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,  # 2 lots
    )
    result = risk_manager.check_order(
        order=order,
        current_equity=1_000_000.0,
        daily_pnl=0.0,
        drawdown_pct=0.0,
        open_positions=[],
    )
    assert result.is_approved is True
    assert len(result.rejection_reasons) == 0


def test_order_exceeding_position_size_rejected(risk_manager):
    """Order exceeding max position size must be rejected."""
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=500,  # 20 lots > 10
    )
    result = risk_manager.check_order(
        order=order,
        current_equity=1_000_000.0,
        daily_pnl=0.0,
        drawdown_pct=0.0,
        open_positions=[],
    )
    assert result.is_approved is False
    assert any("POSITION_SIZE" in r for r in result.rejection_reasons)


def test_order_exceeding_open_positions_rejected(risk_manager):
    """Order placed when max open positions reached must be rejected."""
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=25,
    )
    # 3 already open positions
    open_positions = [
        PaperPosition(symbol=f"SYM_{i}", quantity=25, average_entry_price=100.0)
        for i in range(3)
    ]
    result = risk_manager.check_order(
        order=order,
        current_equity=1_000_000.0,
        daily_pnl=0.0,
        drawdown_pct=0.0,
        open_positions=open_positions,
    )
    assert result.is_approved is False
    assert any("OPEN_POSITIONS" in r for r in result.rejection_reasons)


def test_circuit_breaker_triggers_on_daily_loss(risk_manager):
    """Circuit breaker activates when daily loss threshold breached."""
    # 40,000 loss on 1,000,000 equity is 4% > 3%
    triggered = risk_manager.update_circuit_breakers(
        daily_pnl=-40000.0,
        current_equity=1_000_000.0,
        drawdown_pct=0.04,
    )
    assert "DAILY_LOSS_CIRCUIT_BREAKER" in triggered
    assert risk_manager.is_circuit_breaker_active is True

    # Order now rejected
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=25,
    )
    result = risk_manager.check_order(
        order=order,
        current_equity=960000.0,
        daily_pnl=-40000.0,
        drawdown_pct=0.04,
        open_positions=[],
    )
    assert result.is_approved is False
    assert any("CIRCUIT_BREAKER" in r for r in result.rejection_reasons)

    # Reset breaker
    risk_manager.reset_circuit_breakers()
    assert risk_manager.is_circuit_breaker_active is False


def test_options_order_rejected(risk_manager):
    """Options orders must be rejected as options paper trading is UNAVAILABLE."""
    order = PaperOrder(
        symbol="NIFTY24DEC22000CE",
        instrument_type="INDEX_OPTION",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=25,
    )
    result = risk_manager.check_order(
        order=order,
        current_equity=1_000_000.0,
        daily_pnl=0.0,
        drawdown_pct=0.0,
        open_positions=[],
    )
    assert result.is_approved is False
    assert any("OPTIONS_DATA_UNAVAILABLE" in r for r in result.rejection_reasons)
