"""
Phase 9.8 — Statutory Cost Accounting & Friction Stress Test Suite.

Verifies:
1. Double-entry trade cost accounting: NET = GROSS - FRICTIONS exactly
2. Portfolio PnL = SUM(Trade PnL)
3. Breakdown of all statutory fees: Brokerage, STT, Exchange Turnover, SEBI, GST, Stamp Duty, Slippage
4. Stress tests under 1.0x, 1.5x, 2.0x friction multipliers
"""

import numpy as np
import pytest

from src.research.phase9_8.cost_analysis import Phase98CostEngine


def test_trade_level_cost_double_entry():
    """Verify NET PnL = GROSS PnL - FRICTIONS and sum of trades equals portfolio."""
    # Synthetic alternating positions and returns
    signals = np.array([1.0, 1.0, 0.0, -1.0, -1.0, 1.0, 0.0])
    returns = np.array([0.002, 0.001, -0.001, -0.003, 0.001, 0.004, 0.0])

    report = Phase98CostEngine.audit_trade_series(signals, returns, friction_multiplier=1.0)

    assert report.total_trades_audited > 0
    assert report.reconciliation_verified is True
    assert report.sum_trades_equals_portfolio is True
    assert report.gross_pnl_pct != 0.0
    assert report.total_friction_pct > 0.0

    # Verify individual trade items
    for trade in report.sample_trades:
        assert bool(trade.is_exact_match) is True
        expected_fric = trade.total_statutory_fees_pct + trade.slippage_pct
        assert abs(trade.total_friction_pct - expected_fric) < 1e-6
        assert abs(trade.net_pnl_pct - (trade.gross_pnl_pct - trade.total_friction_pct)) < 1e-6


def test_portfolio_pnl_reconciliation():
    """Verify portfolio net PnL matches sum of trades across multiple scenarios."""
    np.random.seed(42)
    signals = np.sign(np.random.randn(50))
    returns = np.random.randn(50) * 0.01

    report = Phase98CostEngine.audit_trade_series(signals, returns)
    assert report.reconciliation_verified is True
    assert report.sum_trades_equals_portfolio is True
    assert abs(report.net_pnl_pct - (report.gross_pnl_pct - report.total_friction_pct)) < 1e-6


def test_friction_stress_multipliers():
    """Verify performance decays monotonically under 1.0x, 1.5x, and 2.0x friction stress."""
    np.random.seed(42)
    signals = np.array([1.0] * 20 + [-1.0] * 20)
    returns = np.random.randn(40) * 0.005

    report = Phase98CostEngine.audit_trade_series(signals, returns)

    s10 = report.stress_test_1_0x
    s15 = report.stress_test_1_5x
    s20 = report.stress_test_2_0x

    assert s10.friction_multiplier == 1.0
    assert s15.friction_multiplier == 1.5
    assert s20.friction_multiplier == 2.0

    assert s10.net_return_pct > s15.net_return_pct > s20.net_return_pct
    assert s10.total_friction_pct < s15.total_friction_pct < s20.total_friction_pct
