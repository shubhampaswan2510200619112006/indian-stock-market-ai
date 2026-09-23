"""
Unit tests for Phase 12 Source Evaluator.
"""

from __future__ import annotations

import pytest

from src.research.phase12.source_evaluator import SourceEvaluator


def test_candidate_sources_count():
    """Verify that all major data candidate categories are evaluated."""
    records = SourceEvaluator.get_candidate_evaluations()
    assert len(records) >= 5
    vendor_names = [r.vendor_name for r in records]
    assert any("NSE Data & Analytics" in v for v in vendor_names)
    assert any("TrueData" in v for v in vendor_names)
    assert any("Global DataFeeds" in v for v in vendor_names)
    assert any("Broker APIs" in v for v in vendor_names)
    assert any("Public / Free" in v for v in vendor_names)


def test_source_status_and_pricing_labels():
    """Verify that all criteria are classified strictly using approved vocabulary."""
    allowed_field_statuses = {
        "VERIFIED",
        "UNVERIFIED",
        "NOT_AVAILABLE",
        "REQUIRES_VENDOR_CONFIRMATION",
    }
    allowed_pricing_statuses = {
        "VERIFIED_QUOTE",
        "ESTIMATE",
        "NOT_PUBLISHED",
        "REQUIRES_VENDOR_QUOTE",
    }

    records = SourceEvaluator.get_candidate_evaluations()
    for r in records:
        assert r.pricing_status in allowed_pricing_statuses
        for field_dict in [r.instrument_coverage, r.options_coverage]:
            for k, status_str in field_dict.items():
                primary_status = status_str.split(" ")[0].strip()
                assert primary_status in allowed_field_statuses, f"Invalid status: {status_str} in {r.vendor_name}"


def test_observed_provider_limitations():
    """Verify that public endpoints contain verified observed provider limitations."""
    records = SourceEvaluator.get_candidate_evaluations()
    free_source = next(r for r in records if r.vendor_tier == "PUBLIC_FREE")
    assert len(free_source.observed_limitations) > 0
    lim = free_source.observed_limitations[0]
    assert "verification_date" in lim
    assert lim.get("limitation_type") == "OBSERVED_PROVIDER_LIMITATION"
