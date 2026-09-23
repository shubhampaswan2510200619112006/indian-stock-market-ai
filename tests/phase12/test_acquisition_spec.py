"""
Unit tests for Phase 12 Acquisition Specification Engine.
"""

from __future__ import annotations

import pytest

from src.research.phase12.acquisition_spec import AcquisitionSpecEngine


def test_acquisition_specification_structure():
    """Verify specification contains explicit governance and thresholds."""
    spec = AcquisitionSpecEngine.get_full_specification()
    assert spec["specification_version"] == "phase12_v1"

    # Governance
    gov = spec["governance"]
    assert gov["purchase_authorized"] is False
    assert gov["human_decision_required"] is True
    assert gov["broker_connection_allowed"] is False
    assert gov["live_execution_allowed"] is False

    # Intraday
    intra = spec["intraday_requirements"]
    assert "NIFTY 50" in intra["target_symbols"]
    assert "NIFTY BANK" in intra["target_symbols"]
    assert "1m" in intra["target_intervals"]
    assert "5m" in intra["target_intervals"]
    assert intra["minimum_sessions_threshold"] == 250
    assert intra["substitutions_permitted"] is False

    # Options
    opt = spec["options_requirements"]
    assert "NIFTY" in opt["target_underlyings"]
    assert "BANKNIFTY" in opt["target_underlyings"]
    assert "bid" in opt["required_columns"]
    assert "ask" in opt["required_columns"]
    assert opt["paired_quote_continuity_threshold_pct"] == 70.0
    assert opt["contract_validation_method"] == "EXCHANGE_SPEC_AND_CALENDAR_DRIVEN"
    assert "LEVEL_0" in opt["options_quality_hierarchy"]
    assert "LEVEL_3" in opt["options_quality_hierarchy"]
