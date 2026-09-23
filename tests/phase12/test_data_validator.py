"""
Unit tests for Phase 12 Data Onboarding & Validation Pipeline.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.research.phase12.data_validator import DataOnboardingValidator


def test_validator_empty_dataset():
    """Verify Stage 1 INGEST rejection on empty input."""
    res = DataOnboardingValidator.validate(None, dataset_type="INTRADAY_1M")
    assert res.data_ready is False
    assert "1. INGEST" in res.stages_failed
    assert res.rejection_reason is not None


def test_validator_schema_validation_failure():
    """Verify Stage 2 SCHEMA rejection when required columns are missing."""
    df = pd.DataFrame({"timestamp": ["2026-09-01 09:15:00"], "close": [25000.0]})
    res = DataOnboardingValidator.validate(df, dataset_type="INTRADAY_1M")
    assert res.data_ready is False
    assert "2. SCHEMA VALIDATION" in res.stages_failed
    assert res.diagnostics[1].failure_code == "SCHEMA_MISSING_COLUMNS"


def test_validator_ohlc_violation_failure():
    """Verify Stage 5 OHLC logical violation fails when High < Low."""
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-09-01 09:15", periods=5, freq="min"),
        "open": [100.0, 100.0, 100.0, 100.0, 100.0],
        "high": [105.0, 90.0, 105.0, 105.0, 105.0],  # row 1 has high < low
        "low": [95.0, 95.0, 95.0, 95.0, 95.0],
        "close": [102.0, 92.0, 102.0, 102.0, 102.0],
        "volume": [1000, 1000, 1000, 1000, 1000],
    })
    res = DataOnboardingValidator.validate(df, dataset_type="INTRADAY_1M")
    assert res.data_ready is False
    assert "5. OHLC VALIDATION" in res.stages_failed


def test_validator_options_quality_level_classification():
    """Verify Options Quality Hierarchy: L1 (fields exist), L2 (paired), L3 (continuous)."""
    # L1 only (bids/asks are 0 or null)
    df_l1 = pd.DataFrame({
        "timestamp": pd.date_range("2026-09-01 09:15:00", periods=10, freq="min").astype(str),
        "underlying": ["NIFTY"] * 10,
        "expiry": ["2026-09-25"] * 10,
        "strike": [25000.0] * 10,
        "option_type": ["CE"] * 10,
        "close": [150.0] * 10,
        "bid": [0.0] * 10,
        "ask": [0.0] * 10,
    })
    res_l1 = DataOnboardingValidator.validate(df_l1, dataset_type="OPTIONS_QUOTES")
    assert res_l1.options_quality_level == "LEVEL_1"
    assert res_l1.data_ready is False

    # L2 (isolated paired quotes)
    df_l2 = df_l1.copy()
    df_l2["bid"] = [149.0] * 10
    df_l2["ask"] = [151.0] * 10
    res_l2 = DataOnboardingValidator.validate(df_l2, dataset_type="OPTIONS_QUOTES")
    assert res_l2.options_quality_level == "LEVEL_2"
    assert res_l2.data_ready is False  # Level 2 is not execution ready


def test_validator_contract_validation_rejection():
    """Verify Stage 7 CONTRACT VALIDATION rejects invalid option types."""
    df_bad_type = pd.DataFrame({
        "timestamp": ["2026-09-01 09:15:00"],
        "underlying": ["NIFTY"],
        "expiry": ["2026-09-25"],
        "strike": [25000.0],
        "option_type": ["INVALID_TYPE"],
        "close": [150.0],
    })
    res = DataOnboardingValidator.validate(df_bad_type, dataset_type="OPTIONS_QUOTES")
    assert res.data_ready is False
    assert "7. CONTRACT VALIDATION" in res.stages_failed


def test_validator_coverage_sessions_rejection():
    """Verify Stage 9 COVERAGE rejects intraday datasets with fewer than 250 sessions."""
    df_short = pd.DataFrame({
        "timestamp": pd.date_range("2026-09-01 09:15:00", periods=50, freq="min"),
        "open": [25000.0] * 50,
        "high": [25050.0] * 50,
        "low": [24950.0] * 50,
        "close": [25010.0] * 50,
        "volume": [1000] * 50,
    })
    res = DataOnboardingValidator.validate(df_short, dataset_type="INTRADAY_1M")
    assert res.data_ready is False
    assert res.intraday_ready is False
    assert "9. COVERAGE ANALYSIS" in res.stages_failed


def test_validator_provenance_manifest_saving(tmp_path):
    """Verify provenance record creation and manifest serialization."""
    df = pd.DataFrame({
        "date": ["2026-09-01", "2026-09-02"],
        "open": [100.0, 101.0],
        "high": [105.0, 106.0],
        "low": [99.0, 100.0],
        "close": [102.0, 103.0],
        "volume": [5000, 6000],
    })
    res = DataOnboardingValidator.validate(
        df,
        dataset_type="DAILY",
        vendor="TestVendor",
        product="TestProduct",
        dataset_version="phase12_test_v1",
        license_status="TEST_LICENSE",
    )
    assert res.provenance is not None
    manifest_file = DataOnboardingValidator.save_provenance_manifest(res.provenance, str(tmp_path))
    assert manifest_file.endswith("phase12_test_v1_manifest.json")
    import os, json
    assert os.path.exists(manifest_file)
    with open(manifest_file, "r") as f:
        data = json.load(f)
    assert data["dataset_version"] == "phase12_test_v1"
    assert data["vendor"] == "TestVendor"

