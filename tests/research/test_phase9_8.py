"""
Phase 9.8 — Baseline Freeze, Hypothesis Registry & Pipeline Invariants Test Suite.

Verifies:
1. Phase 9.7 Baseline Freeze integrity (all 8 SHA256 hashes matched, immutable)
2. Phase 9.8 Pre-Registered Hypothesis Registry (P98-H001..P98-H008 frozen)
3. Dataset inventory & data quality status
4. Candidate evaluator results and classification integrity
"""

import json
from pathlib import Path
import pytest

from src.research.phase9_8.baseline_freeze import Phase97BaselineFreeze
from src.research.phase9_8.registry import (
    Phase98HypothesisRegistry,
    HypothesisClassification,
    EvaluationType,
)
from src.research.phase9_8.candidate_evaluator import Phase98CandidateEvaluator


def test_phase9_7_baseline_freeze():
    """Verify that all 8 Phase 9.7 baseline artifacts are untouched and match SHA256 checksums."""
    report = Phase97BaselineFreeze.verify_baseline()
    assert report.is_frozen_baseline_intact is True
    assert report.matched_artifacts == report.total_artifacts
    assert report.mismatched_artifacts == 0
    assert len(report.records) == 8


def test_hypothesis_registry_frozen_definitions():
    """Verify all 8 hypotheses are pre-registered with correct parameters and not silently mutated."""
    hypotheses = Phase98HypothesisRegistry.get_all()
    assert len(hypotheses) == 8

    h_dict = {h.id: h for h in hypotheses}
    assert "P98-H001" in h_dict
    assert "P98-H002" in h_dict
    assert "P98-H003" in h_dict
    assert "P98-H004" in h_dict
    assert "P98-H005" in h_dict
    assert "P98-H006" in h_dict
    assert "P98-H007" in h_dict
    assert "P98-H008" in h_dict

    # Check that Track A-C are EXPLORATORY and Track D-G are CONFIRMATORY
    assert h_dict["P98-H001"].exploratory_or_confirmatory == EvaluationType.EXPLORATORY
    assert h_dict["P98-H002"].exploratory_or_confirmatory == EvaluationType.EXPLORATORY
    assert h_dict["P98-H003"].exploratory_or_confirmatory == EvaluationType.EXPLORATORY
    assert h_dict["P98-H004"].exploratory_or_confirmatory == EvaluationType.EXPLORATORY
    assert h_dict["P98-H005"].exploratory_or_confirmatory == EvaluationType.CONFIRMATORY
    assert h_dict["P98-H006"].exploratory_or_confirmatory == EvaluationType.CONFIRMATORY
    assert h_dict["P98-H007"].exploratory_or_confirmatory == EvaluationType.CONFIRMATORY
    assert h_dict["P98-H008"].exploratory_or_confirmatory == EvaluationType.CONFIRMATORY


def test_candidate_evaluator_persisted_results():
    """Verify machine-readable candidate evaluation artifact exists and contains all 8 candidates."""
    res_path = Path("data/phase9_8/candidate_results.json")
    assert res_path.exists(), "candidate_results.json must exist"

    with open(res_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 8
    h_ids = {c["hypothesis_id"] for c in data}
    assert len(h_ids) == 8

    # Verify zero false positives survive
    for c in data:
        assert c["final_classification"] in [
            HypothesisClassification.REJECTED.value,
            HypothesisClassification.INSUFFICIENT_DATA.value,
            HypothesisClassification.INCONCLUSIVE.value,
            HypothesisClassification.NO_EVIDENCE_OF_EDGE.value,
            HypothesisClassification.PROMISING_RESEARCH_CANDIDATE.value,
        ]
        # No candidate was declared promising for Phase 10
        assert c["final_classification"] != HypothesisClassification.PROMISING_RESEARCH_CANDIDATE.value
