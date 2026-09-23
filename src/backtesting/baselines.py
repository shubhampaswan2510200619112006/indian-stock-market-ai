"""
Baseline Benchmark Comparison Engine.

Calculates benchmark performance for:
1. Buy & Hold Underlying
2. Simple Moving Average Directional Trend
"""

from __future__ import annotations

from typing import List, Tuple
from datetime import datetime
from pydantic import BaseModel


class BaselineComparison(BaseModel):
    strategy_total_return_pct: float
    underlying_buy_hold_return_pct: float
    outperformance_vs_buy_hold_pct: float
    comparison_summary: str


def compute_baseline_comparison(
    strategy_return_pct: float,
    underlying_start_price: float,
    underlying_end_price: float,
) -> BaselineComparison:
    if underlying_start_price <= 0:
        buy_hold_return = 0.0
    else:
        buy_hold_return = (underlying_end_price - underlying_start_price) / underlying_start_price

    outperformance = strategy_return_pct - buy_hold_return

    if outperformance > 0.02:
        summary = f"Strategy OUTPERFORMED Buy & Hold by +{outperformance:.1%}."
    elif outperformance < -0.02:
        summary = f"Strategy UNDERPERFORMED Buy & Hold by {outperformance:.1%}."
    else:
        summary = f"Strategy performed inline with Buy & Hold ({outperformance:+.1%})."

    return BaselineComparison(
        strategy_total_return_pct=round(strategy_return_pct, 4),
        underlying_buy_hold_return_pct=round(buy_hold_return, 4),
        outperformance_vs_buy_hold_pct=round(outperformance, 4),
        comparison_summary=summary,
    )
