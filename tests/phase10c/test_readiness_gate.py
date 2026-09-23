"""
Test Readiness Gate and Acquisition Decision for Phase 10C.
"""

import os
import json
import pytest
from src.research.phase10c.vendor_catalog import get_vendor_catalog
from src.research.phase10c.scoring_engine import score_all_vendors
from src.research.phase10c.readiness_gate import compute_phase10c_gate


def test_readiness_gate_computation():
    """
    Verify that readiness gate computes correct values:
    - INTRADAY_DATA_READY = BLOCKED (existing project data has 7/59 sessions < 250)
    - OPTIONS_EXECUTION_DATA_READY = BLOCKED (0 genuine exchange paired quotes)
    - CROSS_SECTIONAL_DATA_READY = PASS
    - PHASE_10C_DATA_READY = NO (data not yet acquired)
    - ACQUISITION_DECISION = COMMERCIAL_DATA_RECOMMENDED
    """
    catalog = get_vendor_catalog()
    evaluations = score_all_vendors(catalog)
    gate = compute_phase10c_gate(evaluations)

    assert gate["status"] == "COMPLETE"
    assert gate["intraday_data_ready"] == "BLOCKED"
    assert gate["options_execution_data_ready"] == "BLOCKED"
    assert gate["cross_sectional_data_ready"] == "PASS"
    assert gate["phase_10c_data_ready"] == "NO"
    assert gate["acquisition_decision"] == "COMMERCIAL_DATA_RECOMMENDED"

    # Invariants in gate
    inv = gate["invariants"]
    assert inv["ALLOW_LIVE_EXECUTION"] is False
    assert inv["LIVE_EXECUTION"] == "DISABLED"
    assert inv["BROKER"] == "NONE"
    assert inv["AUTO_PAPER_ORDER_SUBMISSION"] == "DISABLED"
    assert inv["OPTIONS_EXECUTION"] == "BLOCKED"
    assert inv["NO_ALPHA_RESEARCH"] is True

    # Recommendation structure
    rec = gate["recommendation_details"]
    assert "recommended_intraday_package" in rec
    assert "recommended_options_package" in rec
    assert rec["recommended_intraday_package"]["provider"] == "TrueData"
    assert rec["recommended_options_package"]["provider"] == "NSE Data & Analytics"
    assert "Human authorization required" in rec["recommended_intraday_package"]["human_action_required"]


def test_vendor_capability_does_not_preempt_readiness():
    """
    Test Section 18: A vendor being capable of supplying data does NOT mean
    the project's data is already ready.
    """
    catalog = get_vendor_catalog()
    evaluations = score_all_vendors(catalog)
    gate = compute_phase10c_gate(evaluations)

    # Even though TrueData has >10 years 1m/5m, project data readiness MUST remain BLOCKED
    assert gate["intraday_data_ready"] == "BLOCKED"
    assert gate["phase_10c_data_ready"] == "NO"
