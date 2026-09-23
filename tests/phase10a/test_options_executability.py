"""
Tests for Phase 10A Options Executability & Bid/Ask Engine.
"""

import json
from pathlib import Path
import pytest

from src.research.phase10a.options.options_executability import OptionsExecutabilityAuditEngine


def test_options_repository_audit():
    """Verify options repository audit detects paired Bid/Ask quote scarcity."""
    rep = OptionsExecutabilityAuditEngine.audit_options_repository()
    assert rep["total_options_records"] > 10000
    assert rep["paired_bid_ask_percentage"] < 5.0
    assert rep["continuous_executable_surface_coverage"] == "0.0%"
    assert rep["OPTIONS_EXECUTION_BACKTEST"] == "BLOCKED"
    assert rep["OPTIONS_PAPER_EXECUTION"] == "BLOCKED"
    assert rep["OPTIONS_EXECUTION_RESEARCH_READY"] == "BLOCKED"


def test_options_conditionality_statement():
    """Verify authoritative conditionality statement replaces legacy permanent block phrasing."""
    rep = OptionsExecutabilityAuditEngine.audit_options_repository()
    stmt = rep["options_conditionality_statement"]
    assert "remains blocked until genuine timestamped executable Bid/Ask data" in stmt
    assert "Phase 10A execution-data readiness requirements" in stmt
    assert "permanently blocked" not in stmt.lower()


def test_persisted_options_artifact():
    """Verify data/phase10a/options_executability.json exists and is valid."""
    path = Path("data/phase10a/options_executability.json")
    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["OPTIONS_EXECUTION_BACKTEST"] == "BLOCKED"
    assert data["OPTIONS_PAPER_EXECUTION"] == "BLOCKED"
