"""
Test Baseline Integrity and Safety Invariants for Phase 11.
"""

import pytest
from src.research.phase11.baseline_verifier import (
    verify_frozen_baselines,
    ALLOW_LIVE_EXECUTION,
    LIVE_EXECUTION,
    BROKER,
    AUTO_PAPER_ORDER_SUBMISSION,
    OPTIONS_EXECUTION,
)


def test_safety_invariants():
    """Verify all platform safety invariants remain strictly active."""
    assert ALLOW_LIVE_EXECUTION is False
    assert LIVE_EXECUTION == "DISABLED"
    assert BROKER == "NONE"
    assert AUTO_PAPER_ORDER_SUBMISSION == "DISABLED"
    assert OPTIONS_EXECUTION == "BLOCKED"


def test_frozen_baselines_verification():
    """Verify all frozen phases (9.7, 9.8, 9.9, 10A, 10B, 10C) remain 100% intact."""
    result = verify_frozen_baselines()
    assert result["all_baselines_intact"] is True
    assert result["phase_9_7_baseline"] == "FROZEN"
    assert result["phase_9_8_research_results"] == "FROZEN"
    assert result["phase_9_8_numerical_results"] == "FROZEN"
    assert result["phase_9_9_freeze_manifest"] == "FROZEN_IMMUTABLE"
    assert result["phase_10a_artifacts_status"] == "INTACT"
    assert result["phase_10b_artifacts_status"] == "INTACT"
    assert result["phase_10c_artifacts_status"] == "INTACT"
    assert len(result["errors"]) == 0
