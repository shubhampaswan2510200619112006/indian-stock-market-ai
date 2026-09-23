"""
Unit tests for SimulatedFillEngine in Phase 8.
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from src.paper_trading.fill_engine import SimulatedFillEngine
from src.paper_trading.models import (
    PaperOrder,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
)


@pytest.fixture
def fill_engine():
    return SimulatedFillEngine(
        slippage_pct=0.001,
        max_fill_age_seconds=120.0,
        max_spread_pct=0.10,
        delayed_data_fill_allowed=True,
    )


@patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN"))
def test_market_buy_fills_from_ask(mock_market, fill_engine):
    """BUY order must execute against Ask price (never Bid or LTP)."""
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
    )

    fill, refusal = fill_engine.attempt_fill(
        order=order,
        bid=22000.0,
        ask=22005.0,
        provider_timestamp=now,
        received_timestamp=now,
        data_status="DELAYED",
        source_provider="YFINANCE",
    )

    assert refusal is None
    assert fill is not None
    assert fill.fill_quantity == 50
    # Fill price should be ask + slippage
    assert fill.fill_price >= 22005.0
    assert fill.price_source.value == "PROVIDER_ASK_WITH_SLIPPAGE"


@patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN"))
def test_market_sell_fills_from_bid(mock_market, fill_engine):
    """SELL order must execute against Bid price (never Ask or LTP)."""
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="BANKNIFTY",
        side=PaperOrderSide.SELL,
        order_type=PaperOrderType.MARKET,
        quantity=15,
        status=PaperOrderStatus.OPEN,
    )

    fill, refusal = fill_engine.attempt_fill(
        order=order,
        bid=48000.0,
        ask=48010.0,
        provider_timestamp=now,
        received_timestamp=now,
        data_status="DELAYED",
        source_provider="YFINANCE",
    )

    assert refusal is None
    assert fill is not None
    assert fill.fill_quantity == 15
    # Fill price should be bid - slippage
    assert fill.fill_price <= 48000.0
    assert fill.price_source.value == "PROVIDER_BID_WITH_SLIPPAGE"


@patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN"))
def test_missing_bid_or_ask_refuses_execution(mock_market, fill_engine):
    """Missing Bid or Ask must refuse execution, never substitute LTP."""
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
    )

    fill, refusal = fill_engine.attempt_fill(
        order=order,
        bid=22000.0,
        ask=None,
        provider_timestamp=now,
        received_timestamp=now,
        data_status="DELAYED",
        source_provider="YFINANCE",
    )

    assert fill is None
    assert refusal is not None
    assert refusal.reason == "NO_VALID_EXECUTABLE_QUOTE"


@patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN"))
def test_stale_data_refuses_execution(mock_market, fill_engine):
    """STALE or UNAVAILABLE data must be refused."""
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
    )

    for bad_status in ["STALE", "UNAVAILABLE", "ERROR"]:
        fill, refusal = fill_engine.attempt_fill(
            order=order,
            bid=22000.0,
            ask=22005.0,
            provider_timestamp=now,
            received_timestamp=now,
            data_status=bad_status,
            source_provider="YFINANCE",
        )
        assert fill is None
        assert refusal is not None
        assert "DATA" in refusal.reason


@patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(False, "MARKET_CLOSED"))
def test_market_closed_refuses_execution(mock_market, fill_engine):
    """Fills during closed market hours must be refused."""
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
    )

    fill, refusal = fill_engine.attempt_fill(
        order=order,
        bid=22000.0,
        ask=22005.0,
        provider_timestamp=now,
        received_timestamp=now,
        data_status="DELAYED",
        source_provider="YFINANCE",
    )
    assert fill is None
    assert refusal is not None
    assert refusal.reason == "MARKET_CLOSED"


@patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN"))
def test_wide_spread_refuses_execution(mock_market, fill_engine):
    """Spread wider than threshold must refuse execution."""
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
    )

    fill, refusal = fill_engine.attempt_fill(
        order=order,
        bid=20000.0,
        ask=25000.0,  # 22% spread > 10% max
        provider_timestamp=now,
        received_timestamp=now,
        data_status="DELAYED",
        source_provider="YFINANCE",
    )
    assert fill is None
    assert refusal is not None
    assert refusal.reason == "SPREAD_TOO_WIDE"


@patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN"))
def test_idempotent_fills(mock_market, fill_engine):
    """Processing identical observation twice must produce only one fill."""
    now = datetime.now(timezone.utc)
    order = PaperOrder(
        symbol="NIFTY",
        side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET,
        quantity=50,
        status=PaperOrderStatus.OPEN,
    )

    fill1, ref1 = fill_engine.attempt_fill(
        order=order,
        bid=22000.0,
        ask=22005.0,
        provider_timestamp=now,
        received_timestamp=now,
        data_status="DELAYED",
        source_provider="YFINANCE",
    )
    assert fill1 is not None
    assert ref1 is None

    # Second identical attempt
    fill2, ref2 = fill_engine.attempt_fill(
        order=order,
        bid=22000.0,
        ask=22005.0,
        provider_timestamp=now,
        received_timestamp=now,
        data_status="DELAYED",
        source_provider="YFINANCE",
    )
    assert fill2 is None
    assert ref2 is not None
    assert ref2.reason == "DUPLICATE_OBSERVATION"
