
"""
End-to-end Integration tests for Phase 8 Paper Trading System.
"""

from datetime import datetime, timezone
from unittest.mock import patch
import pytest

from src.paper_trading.execution_guard import LiveExecutionDisabledError
from src.paper_trading.service import PaperTradingService


@pytest.fixture
def paper_service():
    return PaperTradingService(initial_capital=1_000_000.0)


def test_paper_trading_end_to_end_flow(paper_service):
    """
    Test full lifecycle:
    1. Start session
    2. Place BUY order
    3. Process market update with valid Ask -> fill
    4. Mark to market
    5. Place SELL order -> close position
    6. Reconcile portfolio
    """
    # 1. Start session
    start_info = paper_service.start_session()
    assert start_info["execution_mode"] == "PAPER_TRADE"
    assert start_info["status"] == "STARTED"

    # 2. Place BUY order
    order_res = paper_service.place_order(
        symbol="NIFTY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )
    assert order_res["execution_mode"] == "PAPER_TRADE"
    assert order_res["status"] == "PENDING"
    assert order_res["risk_approved"] is True
    order_id = order_res["order_id"]

    # 3. Process market update with simulated open market
    now = datetime.now(timezone.utc)
    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        update_res = paper_service.process_market_update(
            symbol="NIFTY",
            bid=22000.0,
            ask=22005.0,
            ltp=22002.5,
            provider_timestamp=now,
            received_timestamp=now,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )

    assert update_res["execution_mode"] == "PAPER_TRADE"
    assert len(update_res["fills"]) == 1
    assert update_res["fills"][0]["order_id"] == order_id

    # Check position opened
    summary = paper_service.get_portfolio_summary()
    assert summary["open_positions_count"] == 1
    assert summary["cash"] < 1_000_000.0

    # 4. Mark to market with new higher price (e.g. 22300, well above entry + slippage)
    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        paper_service.process_market_update(
            symbol="NIFTY",
            bid=22300.0,
            ask=22305.0,
            ltp=22302.0,
            provider_timestamp=now,
            received_timestamp=now,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )

    summary_marked = paper_service.get_portfolio_summary()
    assert summary_marked["unrealized_pnl"] is not None
    assert summary_marked["unrealized_pnl"] > 0

    # 5. Place SELL order to close position at profitable price
    sell_res = paper_service.place_order(
        symbol="NIFTY",
        side="SELL",
        quantity=50,
        order_type="MARKET",
    )
    sell_order_id = sell_res["order_id"]

    sell_time = datetime.now(timezone.utc)
    with patch("src.paper_trading.fill_engine.is_fill_eligible_market_state", return_value=(True, "MARKET_OPEN")):
        update_sell = paper_service.process_market_update(
            symbol="NIFTY",
            bid=22300.0,
            ask=22305.0,
            ltp=22302.0,
            provider_timestamp=sell_time,
            received_timestamp=sell_time,
            data_status="DELAYED",
            source_provider="YFINANCE",
        )
        assert len(update_sell["fills"]) == 1
    assert update_sell["fills"][0]["order_id"] == sell_order_id

    # Open positions should be 0 now
    summary_closed = paper_service.get_portfolio_summary()
    assert summary_closed["open_positions_count"] == 0
    assert summary_closed["realized_pnl"] > 0

    # 6. Reconcile portfolio
    rec = paper_service.reconcile()
    assert rec["status"] == "RECONCILIATION_PASS"
    assert rec["is_reconciled"] is True

    # 7. Journal entries
    journal = paper_service.get_journal_entries()
    assert len(journal) >= 2


def test_live_mode_rejected_architecturally(paper_service):
    """Any attempt to request LIVE execution must raise LiveExecutionDisabledError."""
    with pytest.raises(LiveExecutionDisabledError):
        from src.paper_trading.execution_guard import ExecutionGuard
        ExecutionGuard.validate_execution_mode("LIVE")
