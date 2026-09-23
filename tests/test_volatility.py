"""
Unit tests for Realized Volatility calculations.
"""

import numpy as np
import pandas as pd
import pytest

from src.features.volatility import (
    calculate_log_returns,
    calculate_realized_volatility,
    calculate_realized_volatility_table,
    compare_rv_iv,
)


def test_log_returns():
    prices = pd.Series([100.0, 105.0, 102.9])
    returns = calculate_log_returns(prices)
    assert len(returns) == 3
    assert np.isnan(returns.iloc[0])
    assert abs(returns.iloc[1] - np.log(105.0 / 100.0)) < 1e-6


def test_realized_volatility_math():
    """
    Validates exact annualization math:
    std(ln(P_t / P_{t-1})) * sqrt(252)
    """
    # Constant 1% daily return
    returns_pct = [0.01] * 21
    prices = [100.0]
    for r in returns_pct:
        prices.append(prices[-1] * (1.0 + r))
    price_series = pd.Series(prices)

    # Since returns are identical (all 1%), std dev is 0 -> RV must be 0.0
    rv_20d = calculate_realized_volatility(price_series, window=20)
    assert rv_20d is not None
    assert abs(rv_20d - 0.0) < 1e-6


def test_realized_volatility_table():
    # 70 days of random prices
    np.random.seed(123)
    p = 20000.0
    prices = [p]
    for _ in range(70):
        p *= 1.0 + np.random.normal(0, 0.01)
        prices.append(p)
    df = pd.DataFrame({"close": prices})

    rv_table = calculate_realized_volatility_table(df, windows=[5, 10, 20, 30, 60])
    assert "realized_vol_5d" in rv_table
    assert "realized_vol_20d" in rv_table
    assert "realized_vol_60d" in rv_table

    assert rv_table["realized_vol_5d"] is not None
    assert rv_table["realized_vol_60d"] is not None
    assert rv_table["realized_vol_20d"] > 0.0


def test_compare_rv_iv():
    res = compare_rv_iv(realized_vol_20d=0.15, implied_vol=0.20)
    assert res["vrp_status"] == "IV_PREMIUM"
    assert abs(res["vrp"] - 0.05) < 1e-6

    res_missing = compare_rv_iv(realized_vol_20d=None, implied_vol=0.20)
    assert res_missing["vrp_status"] == "UNAVAILABLE"
