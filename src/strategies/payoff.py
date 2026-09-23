"""
Options Strategy Payoff Engine & Mathematical Computations.

Computes exact expiry payoffs, breakevens, max profit, max loss, and price grid matrices
for single-leg and multi-leg strategies.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from src.ingestion.schemas import OptionType
from src.options.portfolio_greeks import OptionLeg


def calculate_leg_payoff(
    spot: float,
    strike: float,
    option_type: OptionType | str,
    entry_price: float,
    quantity: int = 1,
    lot_size: int = 1,
) -> float:
    """
    Computes expiry payoff for a single option leg at a given underlying spot price.
    - Long Call (qty = +1): max(0, spot - strike) - entry_price
    - Short Call (qty = -1): entry_price - max(0, spot - strike)
    - Long Put (qty = +1): max(0, strike - spot) - entry_price
    - Short Put (qty = -1): entry_price - max(0, strike - spot)
    Returns payoff in total currency (multiplied by lot_size).
    """
    opt_type = OptionType(option_type) if isinstance(option_type, str) else option_type

    if opt_type == OptionType.CE:
        intrinsic = max(0.0, spot - strike)
    else:
        intrinsic = max(0.0, strike - spot)

    per_unit_payoff = (intrinsic - entry_price) if quantity > 0 else (entry_price - intrinsic)
    return float(per_unit_payoff * abs(quantity) * lot_size)


def calculate_multi_leg_payoff(
    spot: float,
    legs: list[OptionLeg],
    entry_prices: list[float],
) -> float:
    """Computes total expiry net payoff across all legs for a given spot price."""
    total_payoff = 0.0
    for leg, price in zip(legs, entry_prices):
        leg_p = calculate_leg_payoff(
            spot=spot,
            strike=leg.strike_price,
            option_type=leg.option_type,
            entry_price=price,
            quantity=leg.quantity,
            lot_size=leg.lot_size,
        )
        total_payoff += leg_p
    return total_payoff


def generate_payoff_grid(
    spot_range: list[float] | np.ndarray,
    legs: list[OptionLeg],
    entry_prices: list[float],
) -> pd.DataFrame:
    """
    Generates a DataFrame of expiry payoffs across an underlying price grid.
    Columns: ['underlying_price', 'payoff', 'payoff_pct_spot']
    """
    payoffs = []
    for s in spot_range:
        p = calculate_multi_leg_payoff(s, legs, entry_prices)
        payoffs.append({"underlying_price": float(s), "payoff": float(p)})

    df = pd.DataFrame(payoffs)
    return df


def calculate_strategy_breakevens_and_bounds(
    strategy_name: str,
    spot: float,
    legs: list[OptionLeg],
    entry_prices: list[float],
) -> tuple[list[float], Optional[float], Optional[float]]:
    """
    Analytical breakeven, max profit, and max loss solver for standard strategies.
    Returns: (breakevens_list, max_profit, max_loss)
    If max profit or max loss is unlimited, returns float("inf").
    """
    # Evaluate payoff on a fine grid to determine bounds empirically & analytically
    min_k = min([leg.strike_price for leg in legs])
    max_k = max([leg.strike_price for leg in legs])
    grid_min = max(1.0, min(spot * 0.5, min_k * 0.7))
    grid_max = max(spot * 1.5, max_k * 1.3)

    grid = np.linspace(grid_min, grid_max, 5000)
    payoffs = np.array([calculate_multi_leg_payoff(s, legs, entry_prices) for s in grid])

    # Find Zero Crossings (Breakevens)
    zero_crossings = []
    for i in range(len(payoffs) - 1):
        if (payoffs[i] <= 0 and payoffs[i+1] > 0) or (payoffs[i] >= 0 and payoffs[i+1] < 0):
            # Linear interpolation for exact breakeven spot price
            s1, s2 = grid[i], grid[i+1]
            p1, p2 = payoffs[i], payoffs[i+1]
            if abs(p2 - p1) > 1e-9:
                be = s1 + (0.0 - p1) * (s2 - s1) / (p2 - p1)
            else:
                be = s1
            zero_crossings.append(float(round(be, 2)))

    # Deduplicate close breakevens
    unique_be = []
    for b in zero_crossings:
        if not any(abs(b - u) < 1.0 for u in unique_be):
            unique_be.append(b)

    # Max Profit / Max Loss
    raw_max_p = float(np.max(payoffs))
    raw_max_l = float(np.min(payoffs))

    # Check for unlimited profit/loss on grid bounds
    if payoffs[-1] > raw_max_p * 1.1 or payoffs[0] > raw_max_p * 1.1:
        max_profit = float("inf")
    else:
        max_profit = round(raw_max_p, 2)

    if payoffs[-1] < raw_max_l * 1.1 or payoffs[0] < raw_max_l * 1.1:
        max_loss = float("-inf")
    else:
        max_loss = round(raw_max_l, 2)

    return unique_be, max_profit, max_loss
