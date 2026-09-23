"""
Test Baseline Integrity and Platform Safety Invariants for Phase 10C.
"""

import pytest
from src.research.phase10c.baseline_verifier import (
    verify_frozen_baselines,
    ALLOW_LIVE_EXECUTION,
    LIVE_EXECUTION,
    BROKER,
    AUTO_PAPER_ORDER_SUBMISSION,
    OPTIONS_EXECUTION,
    NO_ALPHA_RESEARCH,
)


def test_safety_invariants():
    """Verify all 6 absolute safety invariants."""
    assert ALLOW_LIVE_EXECUTION is False
    assert LIVE_EXECUTION == "DISABLED"
    assert BROKER == "NONE"
    assert AUTO_PAPER_ORDER_SUBMISSION == "DISABLED"
    assert OPTIONS_EXECUTION == "BLOCKED"
    assert NO_ALPHA_RESEARCH is True


def test_frozen_baselines_verification():
    """Verify that Phase 9.7, 9.8, 9.9, 10A, and 10B remain frozen and intact."""
    result = verify_frozen_baselines()
    assert result["all_baselines_intact"] is True
    assert result["phase_9_7_baseline"] == "FROZEN"
    assert result["phase_9_8_research_results"] == "FROZEN"
    assert result["phase_9_8_numerical_results"] == "FROZEN"
    assert result["phase_9_9_freeze_manifest"] == "FROZEN_IMMUTABLE"
    assert result["phase_10a_artifacts_status"] == "INTACT"
    assert result["phase_10b_artifacts_status"] == "INTACT"
    assert result["phase_9_7_artifacts_verified"] == 8
    assert result["phase_9_8_artifacts_verified"] == 13
    assert result["phase_10a_artifacts_verified"] == 9
    assert result["phase_10b_artifacts_verified"] == 6
    assert len(result["errors"]) == 0
