"""
Unit tests for Market Regime classification engine.
"""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.features.market_regime import MarketRegimeEngine
from src.ingestion.schemas import MarketRegimeType


def make_trending_df(trend_pct_per_bar: float, n_bars: int = 220):
    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(n_bars)]
    p = 20000.0
    prices = []
    for _ in range(n_bars):
        p *= 1.0 + (trend_pct_per_bar / 100.0)
        prices.append(p)

    df = pd.DataFrame({
        "timestamp": dates,
        "open": [x * 0.998 for x in prices],
        "high": [x * 1.002 for x in prices],
        "low": [x * 0.996 for x in prices],
        "close": prices,
        "volume": [150000] * n_bars,
    })
    return df


def test_market_regime_strong_bull():
    df = make_trending_df(trend_pct_per_bar=0.2, n_bars=220)  # Strong steady uptrend
    engine = MarketRegimeEngine()
    result = engine.evaluate_regime(nifty_df=df, vix_value=13.5, symbol="NIFTY")

    assert result.regime in [MarketRegimeType.STRONG_BULL, MarketRegimeType.BULL]
    assert result.confidence >= 0.70
    assert len(result.supporting_evidence) > 0
    assert len(result.invalidation_conditions) > 0


def test_market_regime_strong_bear():
    df = make_trending_df(trend_pct_per_bar=-0.25, n_bars=220)  # Strong downtrend
    engine = MarketRegimeEngine()
    result = engine.evaluate_regime(nifty_df=df, vix_value=18.0, symbol="NIFTY")

    assert result.regime in [MarketRegimeType.STRONG_BEAR, MarketRegimeType.BEAR]
    assert result.confidence >= 0.70
    assert len(result.supporting_evidence) > 0


def test_market_regime_high_volatility():
    df = make_trending_df(trend_pct_per_bar=0.01, n_bars=220)  # Flat
    engine = MarketRegimeEngine()
    result = engine.evaluate_regime(nifty_df=df, vix_value=26.5, symbol="NIFTY")  # High VIX!

    assert result.regime == MarketRegimeType.HIGH_VOLATILITY
    assert "India VIX" in "".join(result.conflicting_evidence)


def test_market_regime_insufficient_data():
    df = make_trending_df(trend_pct_per_bar=0.1, n_bars=10)  # Only 10 bars
    engine = MarketRegimeEngine()
    result = engine.evaluate_regime(nifty_df=df, symbol="NIFTY")

    assert result.regime == MarketRegimeType.UNKNOWN
    assert result.confidence == 0.0
