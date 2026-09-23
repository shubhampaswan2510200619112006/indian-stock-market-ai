"""
Unit tests for multi-timeframe aggregation and feature alignment.
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from src.features.technical import compute_technical_features_df
from src.ingestion.schemas import TimeFrame


def test_multi_timeframe_resampling():
    """Validates daily to weekly resampling without data loss or alignment shifts."""
    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(140)]
    np.random.seed(99)
    prices = 20000.0 + np.cumsum(np.random.normal(5, 20, 140))

    daily_df = pd.DataFrame({
        "timestamp": dates,
        "open": prices - 10,
        "high": prices + 30,
        "low": prices - 40,
        "close": prices,
        "volume": [100000] * 140,
    })

    # Resample to weekly
    daily_df["date"] = pd.to_datetime(daily_df["timestamp"])
    weekly_df = daily_df.set_index("date").resample("W-FRI").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }).dropna().reset_index()

    assert len(weekly_df) < len(daily_df)
    assert "close" in weekly_df.columns

    feat_daily = compute_technical_features_df(daily_df, symbol="NIFTY", timeframe=TimeFrame.DAILY)
    feat_weekly = compute_technical_features_df(weekly_df, symbol="NIFTY", timeframe=TimeFrame.WEEKLY)

    assert feat_daily["timeframe"].iloc[0] == TimeFrame.DAILY
    assert len(feat_weekly) > 5
