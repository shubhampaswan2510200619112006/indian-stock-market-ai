"""
Test Data Arrival and Ingestion Validation Pipeline.
"""

import pytest
import pandas as pd
import numpy as np
from src.platform.onboarding.data_arrival_validator import (
    DataArrivalValidator,
    FutureDatasetConfiguration,
)


def test_validator_empty_dataset():
    res = DataArrivalValidator.validate_dataset(pd.DataFrame())
    assert res.data_ready is False
    assert "1. INGEST" in res.stages_failed


def test_validator_missing_schema():
    df = pd.DataFrame({"timestamp": ["2026-01-01"], "close": [100.0]})
    res = DataArrivalValidator.validate_dataset(df, dataset_type="INTRADAY")
    assert res.data_ready is False
    assert "2. SCHEMA VALIDATION" in res.stages_failed


def test_validator_ohlc_integrity_failure():
    # High < Low
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=10, freq="min"),
        "open": [100.0] * 10,
        "high": [90.0] * 10,  # Invalid
        "low": [95.0] * 10,
        "close": [92.0] * 10,
        "volume": [1000] * 10,
    })
    res = DataArrivalValidator.validate_dataset(df, dataset_type="INTRADAY")
    assert res.data_ready is False
    assert "5. OHLC VALIDATION" in res.stages_failed


def test_validator_intraday_coverage_threshold():
    # 50 sessions < 250 required
    dates = pd.date_range("2026-01-01", periods=50, freq="B").strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame({
        "timestamp": dates,
        "open": [100.0] * 50,
        "high": [105.0] * 50,
        "low": [95.0] * 50,
        "close": [102.0] * 50,
        "volume": [10000] * 50,
    })
    res = DataArrivalValidator.validate_dataset(df, dataset_type="INTRADAY")
    assert res.data_ready is False
    assert "9. COVERAGE ANALYSIS" in res.stages_failed
    assert "below required 250 sessions" in res.rejection_reason


def test_validator_qualifying_daily_dataset():
    dates = pd.date_range("2024-01-01", periods=300, freq="B").strftime("%Y-%m-%d")
    df = pd.DataFrame({
        "date": dates,
        "open": [100.0] * 300,
        "high": [105.0] * 300,
        "low": [95.0] * 300,
        "close": [102.0] * 300,
        "volume": [10000] * 300,
    })
    config = FutureDatasetConfiguration(
        provider="TrueData",
        product="Daily Equity",
        instrument_type="EQUITY",
        interval="1D",
        date_range_start="2024-01-01",
        date_range_end="2025-03-01",
        license_type="COMMERCIAL_VENDOR",
        credentials_required=True,
        dataset_path="/data/incoming/daily.parquet",
    )
    res = DataArrivalValidator.validate_dataset(df, dataset_type="DAILY", config=config)
    assert res.data_ready is True
    assert len(res.stages_failed) == 0
