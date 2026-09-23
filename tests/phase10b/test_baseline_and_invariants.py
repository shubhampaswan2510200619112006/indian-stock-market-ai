"""
Tests for Phase 10B Baseline Verification & Safety Invariants.
"""

import pytest
from src.research.phase10b.baseline_verifier import (
    verify_frozen_baselines,
    ALLOW_LIVE_EXECUTION,
    LIVE_EXECUTION,
    BROKER,
    AUTO_PAPER_ORDER_SUBMISSION,
    OPTIONS_EXECUTION,
    NO_ALPHA_RESEARCH,
)


def test_baselines_frozen_and_intact():
    """Verify Phase 9.7, 9.8, 9.9, and 10A baselines remain 100% frozen."""
    res = verify_frozen_baselines()
    assert res["all_baselines_intact"] is True, f"Baseline verification failed: {res['errors']}"
    assert res["phase_9_7_baseline"] == "FROZEN"
    assert res["phase_9_8_research_results"] == "FROZEN"
    assert res["phase_9_8_numerical_results"] == "FROZEN"
    assert res["phase_9_9_freeze_manifest"] == "FROZEN_IMMUTABLE"
    assert res["phase_10a_artifacts_status"] == "INTACT"


def test_safety_invariants_immutable():
    """Verify platform safety invariants remain strictly active and uncompromised."""
    assert ALLOW_LIVE_EXECUTION is False
    assert LIVE_EXECUTION == "DISABLED"
    assert BROKER == "NONE"
    assert AUTO_PAPER_ORDER_SUBMISSION == "DISABLED"
    assert OPTIONS_EXECUTION == "BLOCKED"
    assert NO_ALPHA_RESEARCH is True
