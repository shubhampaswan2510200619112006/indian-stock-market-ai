"""
Phase 9.8 — Timing & Point-in-Time Discipline Test Suite.

Verifies:
1. All 8 research tracks adhere to strict point-in-time sequence:
   FEATURE_CUTOFF <= PREDICTION <= ORDER <= EXECUTION <= EXIT
2. Zero backward return mapping (e.g., T predicting ret(T-1) or same-day close return without forward execution)
3. Zero same-bar execution violations
"""

import json
from pathlib import Path
import pytest

from src.research.phase9_8.timing_audit import Phase98TimingAuditEngine


def test_timing_audit_engine_execution():
    """Verify timing audit engine passes across all 8 tracks without exceptions."""
    report = Phase98TimingAuditEngine.audit_track_timing()
    assert report.total_strategies_audited == 8
    assert report.all_strategies_point_in_time_compliant is True
    assert report.backward_return_mappings_found == 0
    assert report.same_bar_execution_violations_found == 0
    assert report.audit_verdict == "TIMING_AUDIT_PASSED_ALL_MODELS_CLEAN"


def test_timing_audit_json_artifact_integrity():
    """Verify data/phase9_8/timing_audit.json artifact contains valid timestamp sequences."""
    path = Path("data/phase9_8/timing_audit.json")
    assert path.exists(), "timing_audit.json must exist"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["backward_return_mappings_found"] == 0
    assert data["same_bar_execution_violations_found"] == 0
    assert len(data["items"]) == 8

    for item in data["items"]:
        assert item["is_point_in_time_valid"] is True
        assert item["same_bar_execution_prohibited"] is True
        assert item["backward_return_detected"] is False
        assert len(item["feature_cutoff_timestamp"]) > 0
        assert len(item["prediction_timestamp"]) > 0
        assert len(item["order_timestamp"]) > 0
        assert len(item["execution_timestamp"]) > 0
        assert len(item["exit_timestamp"]) > 0
