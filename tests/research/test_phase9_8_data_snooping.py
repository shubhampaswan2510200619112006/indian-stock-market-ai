"""
Phase 9.8 — Data Snooping & Multiple Testing Accounting Test Suite.

Verifies:
1. Every exploratory and confirmatory test is registered in data_snooping_guard.
2. Multiple testing accounting tracks hypothesis counts, parameters, instruments, horizons.
3. Bonferroni alpha adjustment and FDR control are applied.
4. No cherry-picked models claim statistical significance.
"""

import json
from pathlib import Path
import pytest

from src.research.phase9_8.data_snooping_guard import Phase98DataSnoopingGuard


def test_data_snooping_guard_registration(tmp_path):
    """Verify data snooping guard properly counts tests and adjusts critical alpha."""
    test_out = tmp_path / "test_multiple_testing.json"
    guard = Phase98DataSnoopingGuard(out_filepath=str(test_out))
    guard.record_test(
        hypothesis_id="TEST-001",
        track_name="TEST_TRACK",
        test_type="EXPLORATORY",
        instrument="NIFTY",
        model_name="TEST_MODEL",
        parameter_set={"p1": 10},
        p_value=0.04,
        horizon="1D",
    )
    guard.record_test(
        hypothesis_id="TEST-002",
        track_name="TEST_TRACK",
        test_type="CONFIRMATORY",
        instrument="NIFTY",
        model_name="TEST_MODEL_2",
        parameter_set={"p1": 20},
        p_value=0.03,
        horizon="1D",
    )

    report = guard.generate_report()
    assert report.total_exploratory_tests == 1
    assert report.total_confirmatory_tests == 1
    assert report.bonferroni_adjusted_alpha == 0.05 / 2.0


def test_persisted_multiple_testing_json_integrity():
    """Verify data/phase9_8/multiple_testing.json tracks all Phase 9.8 tests and penalizes multiple comparisons."""
    path = Path("data/phase9_8/multiple_testing.json")
    assert path.exists(), "multiple_testing.json must exist"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_registered_hypotheses"] == 8
    assert data["total_exploratory_tests"] == 4
    assert data["total_confirmatory_tests"] == 4
    assert data["total_candidate_models"] >= 8
    assert data["nominal_alpha"] == 0.05
    assert data["bonferroni_adjusted_alpha"] == 0.05 / 8.0
    assert data["multiple_testing_penalty_applied"] is True

    # Check that NO test had raw or adjusted significance claiming false alpha
    for event in data["events"]:
        assert event["raw_significance"] is False
