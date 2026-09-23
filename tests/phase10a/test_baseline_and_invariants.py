"""
Tests for Phase 10A Baseline Verifier & Safety Invariants.
"""

import pytest
from src.research.phase10a.baseline_verifier import (
    verify_frozen_baselines,
    ALLOW_LIVE_EXECUTION,
    LIVE_EXECUTION,
    BROKER,
    AUTO_PAPER_ORDER_SUBMISSION,
    OPTIONS_EXECUTION,
)


def test_baseline_frozen_verification():
    """Verify Phase 9.7 and Phase 9.8/9.9 baselines remain 100% frozen."""
    res = verify_frozen_baselines()
    assert res["all_baselines_intact"] is True, f"Baselines compromised: {res['errors']}"
    assert res["phase_9_7_baseline"] == "FROZEN"
    assert res["phase_9_8_research_results"] == "FROZEN"
    assert res["phase_9_8_numerical_results"] == "FROZEN"
    assert res["phase_9_7_artifacts_verified"] == 8
    assert res["phase_9_8_artifacts_verified"] == 13


def test_safety_invariants_immutable():
    """Verify all safety invariants are strictly enforced and immutable."""
    assert ALLOW_LIVE_EXECUTION is False
    assert LIVE_EXECUTION == "DISABLED"
    assert BROKER == "NONE"
    assert AUTO_PAPER_ORDER_SUBMISSION == "DISABLED"
    assert OPTIONS_EXECUTION == "BLOCKED"
