"""
Tests for Phase 10B Options Dataset Versioning & Execution Block.
"""

import json
from pathlib import Path
import pytest

from src.research.phase10b.acquisition.options_dataset_version import OptionsDatasetVersionManager
from src.research.phase10b.validation.options_quality_engine import OptionsQualityEngine


def test_frozen_baseline_vs_new_versions():
    """Verify Correction 2: Strict dataset versioning preserves frozen baseline and reconciles deltas."""
    audit = OptionsDatasetVersionManager.audit_current_phase10b_dataset()
    versions = audit["versions_tracked"]

    # Frozen baseline must match Phase 9.8 exactly
    f_base = versions["FROZEN_BASELINE"]
    assert f_base["total_records"] == 15106
    assert f_base["paired_bid_ask_count"] == 102
    assert f_base["paired_bid_ask_percentage"] == 0.68
    assert f_base["continuous_executable_surface_coverage"] == "0.0%"

    # Phase 10A snapshot
    p10a = versions["PHASE_10A_DATASET"]
    assert p10a["total_records"] == 17098
    assert p10a["paired_bid_ask_count"] == 114

    # Phase 10B resident version
    p10b = versions["PHASE_10B_DATASET"]
    assert p10b["total_records"] >= 17098
    assert p10b["continuous_executable_surface_coverage"] == "0.0%"


def test_provenance_discrepancy_reconciliation():
    """Verify provenance discrepancy is fully explained by Bhavcopy additions and test fixtures."""
    audit = OptionsDatasetVersionManager.audit_current_phase10b_dataset()
    p_rec = audit["provenance_reconciliation"]
    assert p_rec["is_frozen_baseline_reinterpreted"] is False
    assert p_rec["classification"] == "EXPLAINED_AND_VERIFIED_DATASET_VERSION_DISCREPANCY"
    assert "PIT_LEAK_TEST" in p_rec["critical_provenance_finding"]


def test_options_quality_and_execution_blocks():
    """Verify continuous surface coverage is 0.0% and execution backtest remains blocked."""
    qual = OptionsQualityEngine.audit_options_quality()
    metrics = qual["metrics"]
    assert metrics["continuous_executable_surface_coverage"] == "0.0%"
    assert qual["readiness_gate"]["OPTIONS_EXECUTION_RESEARCH_READY"] == "BLOCKED"
    assert qual["readiness_gate"]["OPTIONS_EXECUTION_BACKTEST"] == "BLOCKED"
    assert qual["readiness_gate"]["OPTIONS_PAPER_EXECUTION"] == "BLOCKED"
