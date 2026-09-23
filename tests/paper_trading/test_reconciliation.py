"""
Tests for Paper Reconciliation in Phase 8.
"""

from datetime import datetime, timezone
import pytest

from src.paper_trading.models import PaperFill, PaperFillSource, PaperTradeRecord
from src.paper_trading.reconciliation import reconcile_paper_account


def test_reconciliation_empty_account():
    """Account with no trades should reconcile cleanly."""
    res = reconcile_paper_account(
        starting_cash=1_000_000.0,
        ending_cash=1_000_000.0,
        positions=[],
        fills=[],
        closed_trades=[],
    )
    assert res.is_reconciled is True
    assert res.status == "RECONCILIATION_PASS"
    assert len(res.discrepancies) == 0


def test_reconciliation_with_trade():
    """Account with consistent completed trade should reconcile."""
    now = datetime.now(timezone.utc)
    fills = [
        PaperFill(
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
            price_source_description="Buy",
            data_status_at_fill="DELAYED",
            slippage_applied=2.0,
            transaction_costs=50.0,
            quote_age_seconds=1.0,
        ),
        PaperFill(
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
            price_source_description="Sell",
            data_status_at_fill="DELAYED",
            slippage_applied=2.0,
            transaction_costs=50.0,
            quote_age_seconds=1.0,
        ),
    ]

    trade = PaperTradeRecord(
        symbol="NIFTY",
        direction="LONG",
        entry_timestamp=now,
        exit_timestamp=now,
        quantity=50,
        entry_price=22000.0,
        exit_price=22100.0,
        gross_pnl=5000.0,
        fees=100.0,
        slippage=200.0,
        net_pnl=4900.0,
        holding_period_seconds=60.0,
    )

    # starting cash = 1,000,000. ending cash = 1,000,000 + 5000 (gain) - 100 (fees) = 1,004,900
    ending_cash = 1_000_000.0 + trade.gross_pnl - sum(f.transaction_costs for f in fills)
    res = reconcile_paper_account(
        starting_cash=1_000_000.0,
        ending_cash=ending_cash,
        positions=[],
        fills=fills,
        closed_trades=[trade],
    )
    assert res.is_reconciled is True
    assert res.status == "RECONCILIATION_PASS"


def test_reconciliation_failure_on_cash_discrepancy():
    """Unexplained cash discrepancy must fail reconciliation with failure status."""
    now = datetime.now(timezone.utc)
    trade = PaperTradeRecord(
        symbol="NIFTY",
        direction="LONG",
        entry_timestamp=now,
        exit_timestamp=now,
        quantity=50,
        entry_price=22000.0,
        exit_price=22100.0,
        gross_pnl=5000.0,
        fees=100.0,
        slippage=200.0,
        net_pnl=4900.0,
        holding_period_seconds=60.0,
    )

    # Mismatched ending cash
    bad_ending_cash = 900_000.0
    res = reconcile_paper_account(
        starting_cash=1_000_000.0,
        ending_cash=bad_ending_cash,
        positions=[],
        fills=[],
        closed_trades=[trade],
    )
    assert res.is_reconciled is False
    assert res.status == "RECONCILIATION_FAILURE"
    assert len(res.discrepancies) > 0
    assert "Cash discrepancy" in res.discrepancies[0]
