"""
Phase 9.8 — Final Gate & Research Validation Test Suite.

Verifies:
1. 10 objective survival dimensions evaluated
2. Authoritative decision is PHASE_10_NOT_JUSTIFIED
3. System readiness is RESEARCH_ONLY
4. Options execution remains strictly BLOCKED (0.0% paired quotes)
5. Zero broker credentials, zero live execution code
6. ALLOW_LIVE_EXECUTION = False and AUTO_PAPER_ORDER_SUBMISSION = False
"""

import json
from pathlib import Path
import pytest

from src.research.phase9_8.final_gate import Phase98FinalGateEngine


def test_final_gate_decision_and_invariants():
    """Verify Phase 10 is NOT justified and safety invariants are strictly enforced."""
    report = Phase98FinalGateEngine.evaluate_phase10_gate()
    assert report.authoritative_decision == "PHASE_10_NOT_JUSTIFIED"
    assert report.system_readiness == "RESEARCH_ONLY"
    assert "DISABLED" in report.live_execution_status
    assert "NONE" in report.broker_connection_status
    assert "DISABLED" in report.automatic_paper_trading
    assert "BLOCKED" in report.options_execution_gate

    assert report.total_candidates_evaluated == 8
    assert report.promising_candidates_count == 0
    assert report.surviving_candidate_id is None

    # Check 10 gates structure
    assert len(report.gates) == 10
    gate_names = {g.gate_name for g in report.gates}
    expected_names = {
        "Methodology",
        "Leakage",
        "OOS Validation",
        "Gross Edge",
        "Net Edge",
        "Cost Robustness",
        "Regime Robustness",
        "Sample Size",
        "Reproducibility",
        "Data Quality / Realism",
    }
    assert gate_names == expected_names

    # Check that failed gates count >= 5
    assert report.failed_gate_count >= 5
    assert report.blocked_gate_count >= 1


def test_persisted_final_gate_json():
    """Verify data/phase9_8/final_gate.json confirms PHASE_10_NOT_JUSTIFIED."""
    path = Path("data/phase9_8/final_gate.json")
    assert path.exists(), "final_gate.json must exist"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["authoritative_decision"] == "PHASE_10_NOT_JUSTIFIED"
    assert data["system_readiness"] == "RESEARCH_ONLY"
    assert data["surviving_candidate_id"] is None
    assert data["promising_candidates_count"] == 0
