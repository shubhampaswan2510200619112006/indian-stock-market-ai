"""
Tests for Phase 10A Authoritative Readiness Gate Engine.
"""

import json
from pathlib import Path
import pytest

from src.research.phase10a.readiness_gate import Phase10AReadinessGateEngine


def test_readiness_gate_evaluation():
    """Verify evaluation of all 10 gates and track-specific readiness."""
    res = Phase10AReadinessGateEngine.evaluate_all_gates()
    assert res["OVERALL_PHASE_10A_STATUS"] == "PHASE_10A_DATA_PARTIALLY_READY"
    assert res["track_readiness"]["INTRADAY_RESEARCH_READY"] == "BLOCKED / INSUFFICIENT_FOR_CONFIRMATORY"
    assert res["track_readiness"]["CROSS_SECTIONAL_RESEARCH_READY"] == "READY"
    assert res["track_readiness"]["OPTIONS_EXECUTION_RESEARCH_READY"] == "BLOCKED"

    assert res["gate_counts"]["total_gates"] == 10
    assert res["gate_counts"]["passed_gates"] == 8
    assert res["gate_counts"]["failed_gates"] == 0
    assert res["gate_counts"]["blocked_gates"] == 2


def test_final_gate_persisted_json():
    """Verify data/phase10a/final_gate.json confirms PARTIALLY_READY status."""
    path = Path("data/phase10a/final_gate.json")
    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["OVERALL_PHASE_10A_STATUS"] == "PHASE_10A_DATA_PARTIALLY_READY"
    assert data["safety_invariants"]["ALLOW_LIVE_EXECUTION"] is False
    assert data["safety_invariants"]["NO_ALPHA_RESEARCH"] is True
