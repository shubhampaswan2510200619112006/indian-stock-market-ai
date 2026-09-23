"""
Test Preregistration Manifest and Pre-Execution Gate for Phase 11.
"""

import pytest
from src.research.phase11.preregistration import get_preregistered_hypotheses, lock_preregistration
from src.research.phase11.execution_gate import verify_phase11_pre_execution_gate

REQUIRED_PREREG_FIELDS = [
    "hypothesis_id",
    "hypothesis_name",
    "economic_rationale",
    "feature_formula",
    "lookback",
    "holding_period",
    "rebalance_rule",
    "ranking_rule",
    "portfolio_rule",
    "eligibility_rule",
    "cost_model",
    "missing_data_rule",
    "tie_break_rule",
    "timestamp_rule",
    "status",
]


def test_preregistration_structure():
    hypotheses = get_preregistered_hypotheses()
    assert len(hypotheses) == 6

    expected_ids = ["H11-001", "H11-002", "H11-003", "H11-004", "H11-005", "H11-006"]
    actual_ids = [h["hypothesis_id"] for h in hypotheses]
    assert actual_ids == expected_ids

    for h in hypotheses:
        for f in REQUIRED_PREREG_FIELDS:
            assert f in h, f"Missing field {f} in hypothesis {h['hypothesis_id']}"
            assert h[f] is not None
        assert h["status"] == "PREREGISTERED_LOCKED"


def test_h11_004_operational_definition():
    hypotheses = {h["hypothesis_id"]: h for h in get_preregistered_hypotheses()}
    h004 = hypotheses["H11-004"]
    assert "VolumeRatio" in h004["feature_formula"]
    assert "strictly excludes Volume_i_t" in h004["feature_formula"]
    assert "VolumeRatio_i > 1.2" in h004["ranking_rule"]


def test_pre_execution_gate():
    gate = verify_phase11_pre_execution_gate()
    assert gate["PHASE_11_PREREGISTRATION_LOCKED"] is True
    assert gate["PHASE_11_COST_MODEL_LOCKED"] is True
    assert gate["PHASE_11_UNIVERSE_VERIFIED"] is True
    assert gate["PHASE_11_DATA_AUDIT_PASS"] is True
    assert gate["PHASE_11_BASELINES_INTACT"] is True
    assert gate["PHASE_11_EXECUTION"] == "PERMITTED"
    assert len(gate["errors"]) == 0
