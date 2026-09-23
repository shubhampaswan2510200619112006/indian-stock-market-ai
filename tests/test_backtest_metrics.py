"""
Tests for Quantitative Performance Metrics Calculator.
"""

from datetime import datetime
import pytest

from src.backtesting.models import ExecutedTrade, PortfolioSnapshot
from src.backtesting.metrics import calculate_performance_metrics


def test_metrics_empty_trades():
    m = calculate_performance_metrics([], [], 100000.0)
    assert m.total_trades == 0
    assert m.sample_size_sufficient is False


def test_metrics_calculation_sample():
    now = datetime(2026, 1, 1, 15, 30)
    t1 = ExecutedTrade(
        trade_id="t1",
        strategy_name="Bull Call Spread",
        symbol="NIFTY",
        entry_timestamp=now,
        exit_timestamp=now,
        entry_underlying_price=24000.0,
        exit_underlying_price=24200.0,
        legs=[],
        lots=1,
        gross_pnl=5000.0,
        total_costs=200.0,
        net_pnl=4800.0,
        return_pct_on_risk=0.5,
        exit_reason="PROFIT_TARGET",
        max_adverse_excursion=-500.0,
        max_favorable_excursion=5000.0,
        holding_days=3.0,
    )
    t2 = ExecutedTrade(
        trade_id="t2",
        strategy_name="Bull Call Spread",
        symbol="NIFTY",
        entry_timestamp=now,
        exit_timestamp=now,
        entry_underlying_price=24200.0,
        exit_underlying_price=24000.0,
        legs=[],
        lots=1,
        gross_pnl=-2000.0,
        total_costs=200.0,
        net_pnl=-2200.0,
        return_pct_on_risk=-0.22,
        exit_reason="STOP_LOSS",
        max_adverse_excursion=-2200.0,
        max_favorable_excursion=100.0,
        holding_days=2.0,
    )

    trades = [t1, t2]
    eq_curve = [
        PortfolioSnapshot(timestamp=now, cash_balance=1000000.0, equity=1000000.0, unrealized_pnl=0.0, realized_pnl_cum=0.0, open_positions_count=0),
        PortfolioSnapshot(timestamp=now, cash_balance=1002600.0, equity=1002600.0, unrealized_pnl=0.0, realized_pnl_cum=2600.0, open_positions_count=0),
    ]

    m = calculate_performance_metrics(trades, eq_curve, 1000000.0, min_sample_size=5)

    assert m.total_trades == 2
    assert m.winning_trades == 1
    assert m.losing_trades == 1
    assert m.win_rate == 0.5
    assert m.net_pnl == 2600.0
    assert m.sample_size_sufficient is False  # 2 trades < min 5
