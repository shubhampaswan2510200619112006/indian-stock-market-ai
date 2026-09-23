"""
Unit tests for Position Sizing Engine.
"""

from datetime import date, datetime

import pytest

from src.options.portfolio_greeks import PortfolioGreeks
from src.strategies.position_sizing import calculate_position_size
from src.strategies.templates import StrategyCandidate


def test_position_sizing_standard_account():
    g = PortfolioGreeks(total_legs=1, net_delta=0.5, net_gamma=0.01, net_theta=-5.0, net_vega=12.0)
    candidate = StrategyCandidate(
        strategy_name="Bull Call Spread",
        symbol="NIFTY",
        expiry_date=date.today(),
        dte=7,
        spot_price=24000.0,
        legs=[],
        net_cost_or_credit=2750.0,  # Max loss per lot = ₹2,750
        capital_required=2750.0,
        max_profit=7250.0,
        max_loss=-2750.0,
        breakevens=[24110.0],
        net_greeks=g,
        liquidity_score=0.85,
    )

    # ₹500,000 Equity, 2% max risk = ₹10,000 budget
    # Max loss per lot = ₹2,750 -> 10,000 // 2,750 = 3 lots
    res = calculate_position_size(candidate, account_equity=500000.0, max_risk_pct=2.0)

    assert res.suggested_lots == 3
    assert res.suggested_quantity == 75
    assert res.max_loss_amount == 8250.0  # 3 * 2750
    assert res.actual_risk_pct_of_account == 1.65  # 8250 / 500000 = 1.65%
    assert abs(res.scaled_net_greeks.net_delta - 1.5) < 1e-4  # 0.5 * 3


def test_position_sizing_zero_equity():
    g = PortfolioGreeks()
    candidate = StrategyCandidate(
        strategy_name="Long Call",
        symbol="NIFTY",
        expiry_date=date.today(),
        dte=7,
        spot_price=24000.0,
        legs=[],
        net_cost_or_credit=3000.0,
        capital_required=3000.0,
        max_loss=-3000.0,
        net_greeks=g,
        liquidity_score=0.85,
    )

    res = calculate_position_size(candidate, account_equity=0.0, max_risk_pct=2.0)
    assert res.suggested_lots == 0
    assert "Invalid account equity" in res.sizing_explanation
