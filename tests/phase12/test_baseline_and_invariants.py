"""
Unit tests for Phase 12 Baseline Verification and Safety Invariants.
"""

from __future__ import annotations

import pytest

from src.research.phase12 import (
    ALLOW_BROKER_CONNECTION,
    ALLOW_LIVE_EXECUTION,
    ALLOW_OPTIONS_BACKTEST,
    ALLOW_PAPER_AUTOMATION,
    AUTO_PAPER_ORDER_SUBMISSION,
    BROKER,
    HUMAN_DECISION_REQUIRED,
    LIVE_EXECUTION,
    NEW_UNPREREGISTERED_ALPHA_RESEARCH,
    OPTIONS_EXECUTION,
    PURCHASE_AUTHORIZED,
    STRATEGY_OPTIMIZATION,
    UNLIMITED_PARAMETER_SEARCH,
)
from src.research.phase12.baseline_verifier import verify_frozen_baselines


def test_safety_invariants():
    """Verify that all Phase 12 execution and commercial safety flags are locked."""
    assert BROKER == "NONE"
    assert LIVE_EXECUTION == "DISABLED"
    assert AUTO_PAPER_ORDER_SUBMISSION == "DISABLED"
    assert OPTIONS_EXECUTION == "BLOCKED"
    assert NEW_UNPREREGISTERED_ALPHA_RESEARCH == "DISABLED"
    assert UNLIMITED_PARAMETER_SEARCH == "DISABLED"
    assert STRATEGY_OPTIMIZATION == "DISABLED"

    assert ALLOW_LIVE_EXECUTION is False
    assert ALLOW_BROKER_CONNECTION is False
    assert ALLOW_PAPER_AUTOMATION is False
    assert ALLOW_OPTIONS_BACKTEST is False
    assert PURCHASE_AUTHORIZED is False
    assert HUMAN_DECISION_REQUIRED is True


def test_frozen_baselines_verification():
    """Verify that all historical baselines (9.7 through 11) remain 100% intact."""
    result = verify_frozen_baselines()
    assert result["all_baselines_intact"] is True
    assert result["phase_9_7_baseline"] == "FROZEN"
    assert result["phase_9_8_research_results"] == "FROZEN"
    assert result["phase_9_8_numerical_results"] == "FROZEN"
    assert result["phase_9_9_freeze_manifest"] == "FROZEN_IMMUTABLE"
    assert result["phase_10a_artifacts_status"] == "INTACT"
    assert result["phase_10b_artifacts_status"] == "INTACT"
    assert result["phase_10c_artifacts_status"] == "INTACT"
    assert result["phase_11_artifacts_status"] == "INTACT"
    assert len(result["errors"]) == 0
