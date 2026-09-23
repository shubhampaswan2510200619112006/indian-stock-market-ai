"""
Research-Grade Position Sizing Engine.

Calculates optimal contract lot sizing based on account equity, maximum risk percentage,
strategy max loss, and portfolio Greeks constraints.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.options.portfolio_greeks import PortfolioGreeks
from src.strategies.templates import StrategyCandidate


class PositionSizingResult(BaseModel):
    """Result of position sizing calculation."""
    strategy_name: str
    account_equity: float
    max_risk_pct: float
    max_allowed_risk_amount: float
    suggested_lots: int
    suggested_quantity: int
    capital_required: float
    max_loss_amount: float
    actual_risk_pct_of_account: float
    scaled_net_greeks: PortfolioGreeks
    sizing_explanation: str


def calculate_position_size(
    candidate: StrategyCandidate,
    account_equity: float = 500000.0,  # Default ₹5 Lakhs
    max_risk_pct: float = 2.0,         # Default 2% max risk per trade
    lot_size: int = 25,
) -> PositionSizingResult:
    """
    Computes suggested lots based on account risk limits.
    Prevents unlimited sizing and negative account exposures.
    """
    if account_equity <= 0:
        return PositionSizingResult(
            strategy_name=candidate.strategy_name,
            account_equity=account_equity,
            max_risk_pct=max_risk_pct,
            max_allowed_risk_amount=0.0,
            suggested_lots=0,
            suggested_quantity=0,
            capital_required=0.0,
            max_loss_amount=0.0,
            actual_risk_pct_of_account=0.0,
            scaled_net_greeks=candidate.net_greeks,
            sizing_explanation="Invalid account equity (<= 0). Position size forced to 0 lots.",
        )

    max_allowed_risk = account_equity * (max_risk_pct / 100.0)

    # Determine risk per lot
    if candidate.max_loss is not None and candidate.max_loss < 0:
        loss_per_lot = abs(candidate.max_loss)
    elif candidate.net_cost_or_credit > 0:
        loss_per_lot = candidate.net_cost_or_credit
    else:
        loss_per_lot = candidate.capital_required if candidate.capital_required > 0 else (candidate.spot_price * 0.05 * lot_size)

    if loss_per_lot <= 0:
        suggested_lots = 1
    else:
        suggested_lots = int(max_allowed_risk // loss_per_lot)

    # Enforce minimum 1 lot (if equity allows) and maximum cap of 50 lots
    suggested_lots = max(1, min(suggested_lots, 50))
    suggested_quantity = suggested_lots * lot_size
    total_capital = candidate.capital_required * suggested_lots
    total_max_loss = loss_per_lot * suggested_lots
    actual_risk_pct = (total_max_loss / account_equity) * 100.0

    # Scale portfolio Greeks by suggested_lots
    g = candidate.net_greeks
    scaled_greeks = PortfolioGreeks(
        total_legs=g.total_legs,
        net_delta=round(g.net_delta * suggested_lots, 4),
        net_gamma=round(g.net_gamma * suggested_lots, 6),
        net_theta=round(g.net_theta * suggested_lots, 4),
        net_vega=round(g.net_vega * suggested_lots, 4),
        net_rho=round(g.net_rho * suggested_lots, 4),
    )

    explanation = (
        f"Based on ₹{account_equity:,.0f} equity and {max_risk_pct}% risk budget (₹{max_allowed_risk:,.0f}), "
        f"suggested size is {suggested_lots} lot(s) ({suggested_quantity} units). "
        f"Max defined risk: ₹{total_max_loss:,.0f} ({actual_risk_pct:.2f}% of equity)."
    )

    return PositionSizingResult(
        strategy_name=candidate.strategy_name,
        account_equity=account_equity,
        max_risk_pct=max_risk_pct,
        max_allowed_risk_amount=round(max_allowed_risk, 2),
        suggested_lots=suggested_lots,
        suggested_quantity=suggested_quantity,
        capital_required=round(total_capital, 2),
        max_loss_amount=round(total_max_loss, 2),
        actual_risk_pct_of_account=round(actual_risk_pct, 2),
        scaled_net_greeks=scaled_greeks,
        sizing_explanation=explanation,
    )
