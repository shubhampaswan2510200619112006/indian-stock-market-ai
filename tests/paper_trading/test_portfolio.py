"""
Tests for PaperPortfolioTracker in Phase 8.
"""

from datetime import datetime, timezone
import pytest

from src.paper_trading.models import (
    PaperFill,
    PaperFillSource,
    PaperOrderSide,
)
from src.paper_trading.portfolio import PaperPortfolioTracker


@pytest.fixture
def tracker():
    return PaperPortfolioTracker(initial_capital=1_000_000.0, session_id="test_session")


def test_initial_portfolio_state(tracker):
    """Initial state should reflect starting capital and zero positions."""
    assert tracker.cash == 1_000_000.0
    assert tracker.get_equity() == 1_000_000.0
    assert len(tracker.get_open_positions()) == 0


def test_open_long_position(tracker):
    """Buying should open long position and deduct cash including transaction costs."""
    now = datetime.now(timezone.utc)
    fill = PaperFill(
        order_id="ORD-1",
        symbol="NIFTY",
        fill_quantity=50,
        fill_price=22000.0,
        fill_timestamp=now,
        provider_timestamp=now,
        received_timestamp=now,
        execution_timestamp=now,
        source_provider="YFINANCE",
        price_source=PaperFillSource.PROVIDER_ASK_WITH_SLIPPAGE,
        price_source_description="Ask fill",
        data_status_at_fill="DELAYED",
        slippage_applied=2.0,
        transaction_costs=50.0,
        quote_age_seconds=1.0,
    )

    trade = tracker.apply_fill(fill, side=PaperOrderSide.BUY)
    assert trade is None  # Opened, not closed
    assert tracker.cash == 1_000_000.0 - (50 * 22000.0 + 50.0)

    positions = tracker.get_open_positions()
    assert len(positions) == 1
    assert positions[0].symbol == "NIFTY"
    assert positions[0].quantity == 50
    assert positions[0].average_entry_price == 22000.0


def test_close_position_realized_pnl(tracker):
    """Selling previously bought position closes it and records realized P&L."""
    now = datetime.now(timezone.utc)
    fill_buy = PaperFill(
        order_id="ORD-1",
        symbol="NIFTY",
        fill_quantity=50,
        fill_price=22000.0,
        fill_timestamp=now,
        provider_timestamp=now,
        received_timestamp=now,
        execution_timestamp=now,
        source_provider="YFINANCE",
        price_source=PaperFillSource.PROVIDER_ASK_WITH_SLIPPAGE,
        price_source_description="Ask fill",
        data_status_at_fill="DELAYED",
        slippage_applied=2.0,
        transaction_costs=50.0,
        quote_age_seconds=1.0,
    )
    tracker.apply_fill(fill_buy, side=PaperOrderSide.BUY)

    # Sell at 22100 (+100 pts * 50 = +5000 gross)
    fill_sell = PaperFill(
        order_id="ORD-2",
        symbol="NIFTY",
        fill_quantity=50,
        fill_price=22100.0,
        fill_timestamp=now,
        provider_timestamp=now,
        received_timestamp=now,
        execution_timestamp=now,
        source_provider="YFINANCE",
        price_source=PaperFillSource.PROVIDER_BID_WITH_SLIPPAGE,
        price_source_description="Bid fill",
        data_status_at_fill="DELAYED",
        slippage_applied=2.0,
        transaction_costs=50.0,
        quote_age_seconds=1.0,
    )
    trade = tracker.apply_fill(fill_sell, side=PaperOrderSide.SELL)

    assert trade is not None
    assert trade.quantity == 50
    assert trade.entry_price == 22000.0
    assert trade.exit_price == 22100.0
    # Net PnL = 5000 - 50.0 (fee on sell) = 4950.0
    assert trade.net_pnl == 4950.0
    assert len(tracker.get_open_positions()) == 0


def test_mark_to_market_unavailable(tracker):
    """When market price is None, mark status becomes MARK_UNAVAILABLE, never synthetic."""
    now = datetime.now(timezone.utc)
    fill = PaperFill(
        order_id="ORD-1",
        symbol="NIFTY",
        fill_quantity=50,
        fill_price=22000.0,
        fill_timestamp=now,
        provider_timestamp=now,
        received_timestamp=now,
        execution_timestamp=now,
        source_provider="YFINANCE",
        price_source=PaperFillSource.PROVIDER_ASK_WITH_SLIPPAGE,
        price_source_description="Ask fill",
        data_status_at_fill="DELAYED",
        slippage_applied=2.0,
        transaction_costs=50.0,
        quote_age_seconds=1.0,
    )
    tracker.apply_fill(fill, side=PaperOrderSide.BUY)

    # Mark with valid price
    tracker.mark_to_market("NIFTY", 22050.0)
    pos = tracker._positions["NIFTY"]
    assert pos.last_mark_status == "MARKET_PRICE"
    assert pos.unrealized_pnl == 2500.0

    # Mark with None (unavailable)
    tracker.mark_to_market("NIFTY", None)
    assert pos.last_mark_status == "MARK_UNAVAILABLE"
    assert pos.unrealized_pnl is None
    assert tracker.get_unrealized_pnl() is None
