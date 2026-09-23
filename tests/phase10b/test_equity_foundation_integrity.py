"""
Tests for Phase 10B Carried-Forward Equity Foundation & Constituent Registry Integrity.
"""

import json
from pathlib import Path
import pytest


def test_phase10a_equity_panels_intact():
    """Verify carried-forward Phase 10A equity panels exist and match verified coverage."""
    p10a_eq = Path("data/phase10a/equity_history_audit.json")
    assert p10a_eq.exists()
    with open(p10a_eq, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["cross_sectional_research_ready"] == "READY"
    assert data["summary_metrics"]["verified_window_target_met"] is True
    assert data["summary_metrics"]["verified_window_anomalies"] == 0


def test_constituent_registry_intact():
    """Verify carried-forward Point-in-Time constituent registry remains verified."""
    p10a_pit = Path("data/phase10a/constituent_integrity.json")
    assert p10a_pit.exists()
    with open(p10a_pit, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["POINT_IN_TIME_REGISTRY_STATUS"] == "VERIFIED_POINT_IN_TIME"
    assert data["UNRESOLVED_EVENTS"] == 0
    assert data["CONSTITUENT_EVENTS_FOUND"] >= 7
