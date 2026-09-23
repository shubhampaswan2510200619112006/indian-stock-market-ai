"""
Unit tests for Technical Analysis calculations and time-series safety.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from src.features.technical import (
    calculate_adx,
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
    compute_technical_features_df,
    extract_latest_features,
)
from src.ingestion.schemas import TimeFrame


@pytest.fixture
def sample_ohlcv_data():
    """Generates 100 bars of deterministic synthetic OHLCV data."""
    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(100)]
    np.random.seed(42)
    base_price = 20000.0
    prices = []
    for i in range(100):
        base_price += np.sin(i / 5) * 50 + (i * 2) + np.random.normal(0, 10)
        prices.append(base_price)

    df = pd.DataFrame({
        "timestamp": dates,
        "open": [p - 15 for p in prices],
        "high": [p + 25 for p in prices],
        "low": [p - 30 for p in prices],
        "close": prices,
        "volume": [100000 + int(i * 500) for i in range(100)],
    })
    return df


def test_calculate_sma(sample_ohlcv_data):
    close = sample_ohlcv_data["close"]
    sma_20 = calculate_sma(close, window=20)
    assert len(sma_20) == 100
    assert np.isnan(sma_20.iloc[18])
    assert not np.isnan(sma_20.iloc[19])
    assert abs(sma_20.iloc[19] - close.iloc[0:20].mean()) < 1e-5


def test_calculate_ema(sample_ohlcv_data):
    close = sample_ohlcv_data["close"]
    ema_12 = calculate_ema(close, span=12)
    assert len(ema_12) == 100
    assert not np.isnan(ema_12.iloc[0])


def test_calculate_rsi(sample_ohlcv_data):
    close = sample_ohlcv_data["close"]
    rsi = calculate_rsi(close, window=14)
    assert len(rsi) == 100
    # RSI bounded between 0 and 100
    assert (rsi.dropna() >= 0.0).all()
    assert (rsi.dropna() <= 100.0).all()


def test_calculate_macd(sample_ohlcv_data):
    close = sample_ohlcv_data["close"]
    macd, signal, hist = calculate_macd(close, fast=12, slow=26, signal=9)
    assert len(macd) == 100
    assert len(signal) == 100
    assert len(hist) == 100
    assert abs((macd.iloc[-1] - signal.iloc[-1]) - hist.iloc[-1]) < 1e-5


def test_calculate_atr(sample_ohlcv_data):
    high = sample_ohlcv_data["high"]
    low = sample_ohlcv_data["low"]
    close = sample_ohlcv_data["close"]
    atr = calculate_atr(high, low, close, window=14)
    assert len(atr) == 100
    assert (atr.dropna() > 0).all()


def test_calculate_adx(sample_ohlcv_data):
    high = sample_ohlcv_data["high"]
    low = sample_ohlcv_data["low"]
    close = sample_ohlcv_data["close"]
    adx = calculate_adx(high, low, close, window=14)
    assert len(adx) == 100
    assert (adx.dropna() >= 0.0).all()


def test_calculate_bollinger_bands(sample_ohlcv_data):
    close = sample_ohlcv_data["close"]
    upper, middle, lower = calculate_bollinger_bands(close, window=20, num_std=2.0)
    assert len(upper) == 100
    valid_idx = 20
    assert (upper.iloc[valid_idx:] >= middle.iloc[valid_idx:]).all()
    assert (middle.iloc[valid_idx:] >= lower.iloc[valid_idx:]).all()


def test_time_series_leakage_prevention(sample_ohlcv_data):
    """
    CRITICAL SAFETY TEST:
    Modifying future row T+1 MUST NOT change feature computed at row T.
    """
    df1 = sample_ohlcv_data.copy()
    feat1 = compute_technical_features_df(df1, symbol="NIFTY", timeframe=TimeFrame.DAILY)
    row50_t1 = feat1.iloc[50]["sma_20"]

    # Mutate row 70 (future relative to row 50)
    df2 = sample_ohlcv_data.copy()
    df2.loc[70, "close"] = df2.loc[70, "close"] * 5.0
    feat2 = compute_technical_features_df(df2, symbol="NIFTY", timeframe=TimeFrame.DAILY)
    row50_t2 = feat2.iloc[50]["sma_20"]

    assert abs(row50_t1 - row50_t2) < 1e-9, "DATA LEAKAGE DETECTED! Future mutation altered historical feature!"


def test_extract_latest_features(sample_ohlcv_data):
    feat = extract_latest_features(sample_ohlcv_data, symbol="NIFTY", timeframe=TimeFrame.DAILY)
    assert feat.symbol == "NIFTY"
    assert feat.close == float(sample_ohlcv_data["close"].iloc[-1])
    assert feat.rsi_14 is not None
    assert feat.sma_20 is not None
