"""
Test Data Audit and Dataset Integrity for Phase 11.
"""

import pytest
from src.research.phase11.data_auditor import DataAuditor, EQUITY_SYMBOLS, BENCHMARK_SYMBOLS


def test_data_auditor_universe_classification():
    auditor = DataAuditor()
    res = auditor.audit_dataset()

    assert res["universe_classification"] == "VERIFIED_NIFTY_CONSTITUENT_SUBSET"
    assert res["number_of_equity_symbols"] == 10
    assert res["number_of_index_series"] == 2
    assert len(res["equity_symbols"]) == 10
    assert len(res["benchmark_symbols"]) == 2


def test_data_auditor_cleanliness():
    auditor = DataAuditor()
    res = auditor.audit_dataset()

    assert res["all_symbols_clean"] is True
    assert res["total_invalid_ohlc_bars"] == 0
    assert res["total_duplicate_rows"] == 0
    assert res["total_missing_values"] == 0
    assert res["common_sessions_count"] >= 250
    assert res["pit_membership_status"] == "VERIFIED_POINT_IN_TIME"


def test_load_aligned_data():
    auditor = DataAuditor()
    equity_df, bench_df = auditor.load_aligned_data()

    assert not equity_df.empty
    assert not bench_df.empty
    assert set(equity_df["symbol"].unique()) == set(EQUITY_SYMBOLS)
    assert "date" in equity_df.columns
    assert "close" in equity_df.columns
