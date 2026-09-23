"""
Tests for Independent Trade Cashflow & Reconciliation Engine.
"""

from datetime import datetime
import pytest

from src.backtesting.models import ExecutedTrade, TradeLegExecution
from src.backtesting.reconciliation import reconcile_backtest_trades
from src.backtesting.models import BacktestResult, BacktestConfig, PerformanceMetrics
from src.ingestion.schemas import OptionType


def test_trade_reconciliation_matching():
    now = datetime(2026, 1, 1, 10, 0)
    leg1 = TradeLegExecution(
        contract_symbol="NIFTY26JAN24000CE",
        option_type=OptionType.CE,
        strike_price=24000.0,
        expiry_date=now.date(),
        action="BUY",
        quantity=25,
        lots=1,
        entry_timestamp=now,
        entry_bid=100.0,
        entry_ask=100.0,
        entry_exec_price=100.0,
        entry_costs=25.0,
        exit_timestamp=now,
        exit_bid=120.0,
        exit_ask=120.0,
        exit_exec_price=120.0,
        exit_costs=25.0,
        leg_pnl=450.0,
    )

    t = ExecutedTrade(
        trade_id="t_rec_1",
        strategy_name="Long Call",
        symbol="NIFTY",
        entry_timestamp=now,
        exit_timestamp=now,
        entry_underlying_price=24000.0,
        exit_underlying_price=24200.0,
        legs=[leg1],
        lots=1,
        gross_pnl=500.0,
        total_costs=50.0,
        net_pnl=450.0,
        return_pct_on_risk=0.18,
        exit_reason="PROFIT_TARGET",
        max_adverse_excursion=0.0,
        max_favorable_excursion=500.0,
        holding_days=1.0,
    )

    result = BacktestResult(
        config=BacktestConfig(),
        data_source="TEST",
        data_quality_label="GOOD",
        critical_labels=[],
        metrics=PerformanceMetrics(),
        trades=[t],
    )

    rec_report = reconcile_backtest_trades(result)
    assert rec_report.total_trades_evaluated == 1
    assert rec_report.fully_reconciled_count == 1
    assert rec_report.is_100_pct_reconciled is True
