"""
Tests for Phase 10A Intraday Coverage & Granularity Audit Engine.
"""

import json
from pathlib import Path
import pytest

from src.research.phase10a.coverage.intraday_audit import IntradayCoverageAuditEngine


def test_intraday_audit_execution():
    """Verify intraday audit completes and generates coverage metrics from cache."""
    res = IntradayCoverageAuditEngine.audit_all_intraday_instruments()
    assert "instruments" in res
    assert "NIFTY_50" in res["instruments"]
    assert "BANK_NIFTY" in res["instruments"]
    assert res["intraday_research_ready"] == "BLOCKED / INSUFFICIENT_FOR_CONFIRMATORY"


def test_intraday_provider_limits_and_notice():
    """Verify provider constraint notice is present and limits are not framed as universal facts."""
    res = IntradayCoverageAuditEngine.audit_all_intraday_instruments()
    nifty = res["instruments"]["NIFTY_50"]
    notice = nifty["provider_constraint_notice"]
    assert "provider-specific limitations" in notice
    assert "selected public endpoint" in notice
    assert "NOT a universal statement" in notice


def test_intraday_persisted_coverage_json():
    """Verify data/phase10a/coverage.json artifact exists and has valid structure."""
    path = Path("data/phase10a/coverage.json")
    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["intraday_research_ready"] == "BLOCKED / INSUFFICIENT_FOR_CONFIRMATORY"
    assert "NIFTY_50" in data["instruments"]
