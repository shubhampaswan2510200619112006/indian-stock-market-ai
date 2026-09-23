"""
Unit tests for Phase 12 Readiness Gate Engine.
"""

from __future__ import annotations

import pytest

from src.research.phase12.readiness_gate import Phase12ReadinessGate


def test_phase12_readiness_gate_evaluation():
    """Verify independent readiness gates and human decision constraint."""
    gate = Phase12ReadinessGate.evaluate()
    assert gate.phase_12_status == "COMPLETE"

    # Independent gates
    assert gate.intraday_1m_ready == "BLOCKED"
    assert gate.intraday_5m_ready == "BLOCKED"
    assert gate.options_ltp_ready == "PASS"
    assert gate.options_bid_ask_ready == "BLOCKED"
    assert gate.options_execution_ready == "BLOCKED"

    # Governance & Human Authorization
    assert gate.commercial_acquisition_required is True
    assert gate.purchase_authorized is False
    assert gate.human_decision_required is True

    # Safety
    assert gate.broker == "NONE"
    assert gate.live_execution == "DISABLED"
    assert gate.auto_paper_order_submission == "DISABLED"
    assert gate.new_alpha_research == "DISABLED"
    assert gate.frozen_baselines == "INTACT"

    # Decision Package
    pkg = gate.acquisition_decision_package
    assert "recommended_primary_source" in pkg
    assert "target_datasets" in pkg
    assert len(pkg["target_datasets"]) == 2
