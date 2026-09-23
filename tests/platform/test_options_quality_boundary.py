"""
Test Options Quality Boundary Hierarchy (L0 to L4).
"""

import pytest
import pandas as pd
from src.platform.onboarding.data_arrival_validator import DataArrivalValidator


def test_options_level_0_no_bid_ask():
    # Only close and settle_price
    df = pd.DataFrame({
        "timestamp": ["2026-01-01 09:15:00"],
        "underlying": ["NIFTY"],
        "expiry": ["2026-01-29"],
        "strike": [22000.0],
        "option_type": ["CE"],
        "close": [150.0],
    })
    res = DataArrivalValidator.validate_dataset(df, dataset_type="OPTIONS")
    assert res.options_quality_level == "LEVEL_0"
    assert res.data_ready is False  # Options execution data not ready


def test_options_level_1_fields_exist_invalid_values():
    # Bid/Ask columns exist, but zero or inverted
    df = pd.DataFrame({
        "timestamp": ["2026-01-01 09:15:00"],
        "underlying": ["NIFTY"],
        "expiry": ["2026-01-29"],
        "strike": [22000.0],
        "option_type": ["CE"],
        "close": [150.0],
        "bid": [0.0],
        "ask": [0.0],
    })
    res = DataArrivalValidator.validate_dataset(df, dataset_type="OPTIONS")
    assert res.options_quality_level == "LEVEL_1"
    assert res.data_ready is False


def test_options_level_2_paired_quotes():
    # Valid paired quote (Bid > 0, Ask >= Bid)
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=100, freq="min"),
        "underlying": ["NIFTY"] * 100,
        "expiry": ["2026-01-29"] * 100,
        "strike": [22000.0] * 100,
        "option_type": ["CE"] * 100,
        "close": [150.0] * 100,
        "bid": [149.0] * 100,
        "ask": [151.0] * 100,
    })
    res = DataArrivalValidator.validate_dataset(df, dataset_type="OPTIONS")
    assert res.options_quality_level == "LEVEL_2"
    assert res.metrics["paired_quote_count"] == 100
    assert res.metrics["paired_quote_coverage_pct"] == 100.0
    # Level 2 is still not enough for continuous surface (sample size < 10000)
    assert res.data_ready is False


def test_options_level_3_continuous_surface():
    # 10,000 continuous quotes with valid paired bid/ask
    n = 10000
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=n, freq="s"),
        "underlying": ["NIFTY"] * n,
        "expiry": ["2026-01-29"] * n,
        "strike": [22000.0] * n,
        "option_type": ["CE"] * n,
        "close": [150.0] * n,
        "bid": [149.5] * n,
        "ask": [150.5] * n,
    })
    res = DataArrivalValidator.validate_dataset(df, dataset_type="OPTIONS")
    assert res.options_quality_level == "LEVEL_3"
    assert res.data_ready is True
