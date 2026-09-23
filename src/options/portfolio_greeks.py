"""
Portfolio & Multi-Leg Strategy Greeks Architecture.

Aggregates Net Greeks across multiple option legs:
- Long Call (+1 qty): +Delta, +Gamma, -Theta, +Vega, +Rho
- Short Call (-1 qty): -Delta, -Gamma, +Theta, -Vega, -Rho
- Long Put (+1 qty): -Delta, +Gamma, -Theta, +Vega, -Rho
- Short Put (-1 qty): +Delta, -Gamma, +Theta, -Vega, +Rho
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from src.ingestion.schemas import GreeksObservation, OptionType


class OptionLeg(BaseModel):
    """A single option leg within a strategy or portfolio position."""
    symbol: str = "NIFTY"
    strike_price: float
    option_type: OptionType
    quantity: int = Field(description="Positive for Long (+1), Negative for Short (-1)")
    lot_size: int = 1
    greeks: GreeksObservation


class PortfolioGreeks(BaseModel):
    """Aggregated Net Greeks for a multi-leg options strategy/portfolio."""
    total_legs: int = 0
    net_delta: float = 0.0
    net_gamma: float = 0.0
    net_theta: float = 0.0  # Daily decay in currency/points
    net_vega: float = 0.0   # Impact per 1% change in vol
    net_rho: float = 0.0    # Impact per 1% change in rate


def aggregate_portfolio_greeks(legs: list[OptionLeg]) -> PortfolioGreeks:
    """
    Computes Net Delta, Net Gamma, Net Theta, Net Vega, Net Rho across all legs.
    """
    net_delta = 0.0
    net_gamma = 0.0
    net_theta = 0.0
    net_vega = 0.0
    net_rho = 0.0

    for leg in legs:
        multiplier = leg.quantity * leg.lot_size
        g = leg.greeks

        if g.delta is not None:
            net_delta += g.delta * multiplier
        if g.gamma is not None:
            net_gamma += g.gamma * multiplier
        if g.theta is not None:
            net_theta += g.theta * multiplier
        if g.vega is not None:
            net_vega += g.vega * multiplier
        if g.rho is not None:
            net_rho += g.rho * multiplier

    return PortfolioGreeks(
        total_legs=len(legs),
        net_delta=round(net_delta, 4),
        net_gamma=round(net_gamma, 6),
        net_theta=round(net_theta, 4),
        net_vega=round(net_vega, 4),
        net_rho=round(net_rho, 4),
    )
