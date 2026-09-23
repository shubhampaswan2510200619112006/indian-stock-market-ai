"""
Realized volatility engine.

CRITICAL MATHEMATICAL SPECIFICATION:
Realized Volatility is calculated as the sample standard deviation of log daily returns
multiplied by the square root of annual trading days (252):

    RV_N = std(ln(P_t / P_{t-1})) * sqrt(252)

Tested windows: 5D, 10D, 20D, 30D, 60D.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def calculate_log_returns(prices: pd.Series) -> pd.Series:
    """Computes daily log returns: ln(P_t / P_{t-1})."""
    if len(prices) < 2:
        return pd.Series(dtype=float)
    return np.log(prices / prices.shift(1))


def calculate_realized_volatility(
    prices: pd.Series, window: int, min_periods: Optional[int] = None
) -> float | None:
    """
    Computes annualized realized volatility for a specific window length.
    Annualization factor: sqrt(252).
    """
    if len(prices) < window:
        if min_periods is None or len(prices) < min_periods:
            return None

    log_returns = calculate_log_returns(prices)
    recent_returns = log_returns.tail(window).dropna()

    req_min = min_periods if min_periods is not None else max(2, window // 2)
    if len(recent_returns) < req_min:
        return None

    std_dev = recent_returns.std(ddof=1)
    if pd.isna(std_dev):
        return None

    annualized_vol = float(std_dev * np.sqrt(252))
    return float(annualized_vol)


def calculate_realized_volatility_table(
    df: pd.DataFrame, windows: list[int] = [5, 10, 20, 30, 60]
) -> dict[str, float | None]:
    """
    Calculates realized volatility for all requested windows from an OHLCV DataFrame.
    Expects df column 'close'.
    """
    if "close" not in df.columns or len(df) < 3:
        return {f"realized_vol_{w}d": None for w in windows}

    prices = df["close"].copy()
    results = {}

    for w in windows:
        rv = calculate_realized_volatility(prices, window=w)
        results[f"realized_vol_{w}d"] = rv

    return results


def compare_rv_iv(
    realized_vol_20d: float | None, implied_vol: float | None
) -> dict[str, str | float | None]:
    """
    Compares 20-day realized volatility with ATM implied volatility.
    Yields volatility risk premium (VRP) evidence.
    """
    if realized_vol_20d is None or implied_vol is None:
        return {
            "vrp": None,
            "vrp_status": "UNAVAILABLE",
            "interpretation": "Insufficient data to compute Volatility Risk Premium.",
        }

    vrp = implied_vol - realized_vol_20d
    if vrp > 0.03:  # IV > RV by > 3 percentage points
        status = "IV_PREMIUM"
        interp = f"Options IV ({implied_vol*100:.1f}%) trades at a premium over 20D Realized Vol ({realized_vol_20d*100:.1f}%). Premium: +{vrp*100:.1f}%."
    elif vrp < -0.03:
        status = "IV_DISCOUNT"
        interp = f"Options IV ({implied_vol*100:.1f}%) trades at a discount below 20D Realized Vol ({realized_vol_20d*100:.1f}%). Discount: {vrp*100:.1f}%."
    else:
        status = "FAIR_VALUE"
        interp = f"Options IV ({implied_vol*100:.1f}%) is aligned with 20D Realized Vol ({realized_vol_20d*100:.1f}%)."

    return {
        "vrp": vrp,
        "vrp_status": status,
        "interpretation": interp,
    }
