"""
Tests for Phase 10B Readiness Gate Decision Logic.
"""

import json
from pathlib import Path
import pytest

from src.research.phase10b.readiness_gate import Phase10BReadinessGateEngine


def test_phase10b_gate_evaluation():
    """Verify evaluation of all 8 Phase 10B gates and final Phase 10C readiness."""
    res = Phase10BReadinessGateEngine.evaluate_gates()

    # Track-level readiness
    assert res["track_readiness"]["INTRADAY_RESEARCH_READY"] == "BLOCKED"
    assert res["track_readiness"]["CROSS_SECTIONAL_RESEARCH_READY"] == "PASS"
    assert res["track_readiness"]["OPTIONS_EXECUTION_RESEARCH_READY"] == "BLOCKED"

    # Overall outcome
    assert res["OVERALL_PHASE_10B_STATUS"] == "PHASE_10C_NOT_READY"
    assert res["PHASE_10C_ALPHA_RESEARCH_READY"] == "NO"

    # Gate counts
    counts = res["gate_counts"]
    assert counts["total_gates"] == 8
    assert counts["passed_gates"] == 6
    assert counts["failed_gates"] == 0
    assert counts["blocked_gates"] == 2


def test_final_gate_persisted_artifact():
    """Verify data/phase10b/final_gate.json confirms PHASE_10C_NOT_READY."""
    p = Path("data/phase10b/final_gate.json")
    assert p.exists()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["OVERALL_PHASE_10B_STATUS"] == "PHASE_10C_NOT_READY"
    assert data["PHASE_10C_ALPHA_RESEARCH_READY"] == "NO"
    assert data["safety_invariants"]["ALLOW_LIVE_EXECUTION"] is False
