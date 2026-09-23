"""
Scenario Analysis Engine for Options Strategies.

Evaluates P/L under 5 price scenarios (-2sigma, -1sigma, 0, +1sigma, +2sigma),
distinguishing exact expiry payoffs from estimated pre-expiry P/L.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from pydantic import BaseModel, Field

from src.options.portfolio_greeks import OptionLeg
from src.strategies.payoff import calculate_multi_leg_payoff
from src.strategies.templates import StrategyCandidate


class ScenarioPL(BaseModel):
    """P/L result for a single underlying price scenario."""
    scenario_label: str  # "Large Bearish (-2σ)", "Moderate Bearish (-1σ)", "Unchanged (0)", "Moderate Bullish (+1σ)", "Large Bullish (+2σ)"
    underlying_price: float
    price_change_pct: float
    expiry_pl_pts: float
    expiry_pl_amount: float
    estimated_pre_expiry_pl_pts: Optional[float] = Field(description="Estimated P/L prior to expiry (subject to Greek & IV shifts)")


class StrategyScenarioAnalysis(BaseModel):
    """Multi-scenario analysis summary for a strategy candidate."""
    strategy_name: str
    spot_price: float
    expected_move_pts: float
    scenarios: list[ScenarioPL]
    disclaimer: str = "Pre-expiry P/L is estimated using Delta/Gamma/Vega sensitivities — actual pricing will vary with IV and time."


def compute_scenario_analysis(
    candidate: StrategyCandidate,
    legs: list[OptionLeg],
    entry_prices: list[float],
    expected_move_pts: Optional[float] = None,
    lot_size: int = 25,
) -> StrategyScenarioAnalysis:
    """
    Computes scenario P/L grid across -2sigma, -1sigma, 0, +1sigma, +2sigma price shocks.
    """
    spot = candidate.spot_price
    move = expected_move_pts or (spot * 0.02)  # Default 2% move if missing

    scenarios_def = [
        ("Large Bearish (-2σ)", spot - (2.0 * move)),
        ("Moderate Bearish (-1σ)", spot - (1.0 * move)),
        ("Unchanged (0)", spot),
        ("Moderate Bullish (+1σ)", spot + (1.0 * move)),
        ("Large Bullish (+2σ)", spot + (2.0 * move)),
    ]

    scenario_results = []
    greeks = candidate.net_greeks

    for label, price_target in scenarios_def:
        pct_chg = ((price_target - spot) / spot) * 100.0
        dS = price_target - spot

        # 1. Expiry P/L (Exact)
        exp_pl = calculate_multi_leg_payoff(price_target, legs, entry_prices)

        # 2. Pre-Expiry P/L Estimation (1st & 2nd order Taylor expansion using Delta & Gamma)
        pre_exp_pl = (greeks.net_delta * dS) + (0.5 * greeks.net_gamma * (dS ** 2))

        scenario_results.append(ScenarioPL(
            scenario_label=label,
            underlying_price=round(price_target, 2),
            price_change_pct=round(pct_chg, 2),
            expiry_pl_pts=round(exp_pl / lot_size, 2),
            expiry_pl_amount=round(exp_pl, 2),
            estimated_pre_expiry_pl_pts=round(pre_exp_pl, 2),
        ))

    return StrategyScenarioAnalysis(
        strategy_name=candidate.strategy_name,
        spot_price=spot,
        expected_move_pts=round(move, 2),
        scenarios=scenario_results,
    )
