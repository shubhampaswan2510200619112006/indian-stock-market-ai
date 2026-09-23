"""
Test Scoring Engine and Critical-Fail Overrides for Phase 10C.
"""

import pytest
from src.research.phase10c.vendor_catalog import get_vendor_catalog
from src.research.phase10c.scoring_engine import score_vendor, score_all_vendors


def test_scoring_dimensions_and_weights():
    """Verify exact 9 dimensions sum to 100 max points."""
    catalog = get_vendor_catalog()
    weights = {
        "intraday_historical_depth": 20,
        "intraday_granularity": 10,
        "options_bid_ask_quality": 25,
        "options_historical_depth": 15,
        "timestamp_execution_quality": 10,
        "data_completeness": 5,
        "provenance_documentation": 5,
        "access_practicality": 5,
        "cost_efficiency": 5,
    }
    assert sum(weights.values()) == 100

    for v in catalog:
        s = score_vendor(v)
        breakdown = s["score_breakdown"]
        assert len(breakdown) == 9
        for dim, max_pts in weights.items():
            assert dim in breakdown
            assert 0 <= breakdown[dim] <= max_pts, f"Vendor {v['provider_name']} dimension {dim} score out of range"
        assert s["total_score"] == sum(breakdown.values())
        assert 0 <= s["total_score"] <= 100


def test_critical_fail_overrides():
    """
    Test Section 16: The score cannot override a missing critical requirement.
    Even if overall score is > 0, missing critical requirement blocks that track.
    """
    catalog = {v["provider_name"]: v for v in get_vendor_catalog()}

    # Yahoo Finance fails intraday (7d / 59d < 250 sessions)
    yfin = score_vendor(catalog["Yahoo Finance"])
    assert yfin["intraday_track_status"] == "BLOCKED"
    assert "INTRADAY_BELOW_250_SESSIONS" in yfin["critical_flags"]

    # Zerodha Kite Connect has high intraday score but zero options bid/ask
    kite = score_vendor(catalog["Zerodha Kite Connect"])
    assert kite["intraday_track_status"] == "PASS"
    assert kite["options_track_status"] == "BLOCKED"
    assert "OPTIONS_BID_ASK_UNAVAILABLE" in kite["critical_flags"]

    # NSE Public Bhavcopy has zero intraday data
    bhav = score_vendor(catalog["NSE Public Bhavcopy"])
    assert bhav["intraday_track_status"] == "BLOCKED"
    assert bhav["options_track_status"] == "BLOCKED"
