"""
Tests for Phase 10B Intraday Source Acquisition & Quality Validation.
"""

import json
from pathlib import Path
import pytest

from src.research.phase10b.acquisition.intraday_source_auditor import Phase10BIntradayAuditor
from src.research.phase10b.validation.intraday_quality_engine import IntradayQualityEngine


def test_dynamic_gate_computation_not_hardcoded():
    """Verify Correction 1: Intraday gate is computed from observed evidence, not pre-decided."""
    res = Phase10BIntradayAuditor.audit_all_intraday()
    crit = res["confirmatory_criteria_evaluation"]
    # Evidence shows observed sessions are below confirmatory target (250)
    assert crit["nifty_5m_sessions_observed"] < 250
    assert crit["criteria_met"] is False
    assert res["INTRADAY_RESEARCH_READY"] == "BLOCKED"


def test_auxiliary_1h_policy_notice():
    """Verify Correction 3: 1-hour data cannot substitute for 1m/5m confirmatory target."""
    res = Phase10BIntradayAuditor.audit_all_intraday()
    policy = res["auxiliary_1h_policy_statement"]
    assert "cannot satisfy the 1m/5m confirmatory intraday readiness criterion" in policy
    assert "auxiliary research dataset" in policy


def test_intraday_bar_quality_invariants():
    """Verify acquired intraday series have 0 OHLC violations and monotonic timestamps."""
    qual = IntradayQualityEngine.validate_all_acquired_series()
    assert qual["all_series_clean"] is True
    assert qual["total_series_validated"] >= 6
    for s_name, s_res in qual["series"].items():
        assert s_res["is_monotonic"] is True
        assert s_res["duplicate_count"] == 0
        assert s_res["ohlc_violations"] == 0
        assert s_res["session_boundary_violations"] == 0
        assert s_res["quality_verdict"] == "CLEAN"


def test_persisted_intraday_quality_json():
    """Verify data/phase10b/intraday_quality.json artifact exists and contains full schema."""
    p = Path("data/phase10b/intraday_quality.json")
    assert p.exists()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "sources_investigated" in data
    assert "confirmatory_criteria_evaluation" in data
    assert data["INTRADAY_RESEARCH_READY"] == "BLOCKED"
