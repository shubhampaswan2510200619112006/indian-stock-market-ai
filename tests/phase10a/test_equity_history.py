"""
Tests for Phase 10A Equity History & Corporate Actions Audit Engine.
"""

import json
from pathlib import Path
import pytest

from src.research.phase10a.ingestion.equity_history import EquityHistoryAuditEngine


def test_equity_panel_cached_audit():
    """Verify daily equity panel audit completes successfully using cached data."""
    rep = EquityHistoryAuditEngine.ingest_and_audit_equity_panel(download_if_missing=False)
    metrics = rep["summary_metrics"]
    assert metrics["verified_window_target_met"] is True
    assert metrics["verified_window_min_sessions"] >= 495
    assert metrics["verified_window_anomalies"] == 0
    assert rep["cross_sectional_research_ready"] == "READY"


def test_equity_no_artificial_capping():
    """Verify that full history is not artificially capped at 2 years."""
    rep = EquityHistoryAuditEngine.ingest_and_audit_equity_panel(download_if_missing=False)
    metrics = rep["summary_metrics"]
    # Maximum sessions observed should exceed 4,000 (15+ years)
    assert metrics["full_history_max_sessions"] > 4000
    assert metrics["full_history_total_observations"] > 50000


def test_persisted_equity_history_artifact():
    """Verify data/phase10a/equity_history_audit.json exists and is valid."""
    path = Path("data/phase10a/equity_history_audit.json")
    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["cross_sectional_research_ready"] == "READY"
