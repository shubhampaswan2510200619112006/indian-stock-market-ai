"""
Test Hypothesis Evaluation Engine and Leakage Controls for Phase 11.
"""

import pytest
from src.research.phase11.hypothesis_engine import HypothesisEngine


def test_hypothesis_engine_evaluation_h001():
    engine = HypothesisEngine()
    res = engine.evaluate_hypothesis("H11-001")

    assert res.hypothesis_id == "H11-001"
    assert res.lookback == 20
    assert res.holding_period == 5
    assert res.total_rebalances > 100
    assert res.oos_rebalances > 0
    assert len(res.rebalance_history) == res.total_rebalances

    # Check non-overlapping rebalance dates
    dates = [p.rebalance_date for p in res.rebalance_history]
    assert len(dates) == len(set(dates))  # Strictly distinct dates


def test_h11_006_conditional_sample_size_reporting():
    engine = HypothesisEngine()
    res = engine.evaluate_hypothesis("H11-006")

    assert res.hypothesis_id == "H11-006"
    assert "TOTAL_ELIGIBLE_DATES" in res.additional_reporting
    assert "BREADTH_ABOVE_50_DATES" in res.additional_reporting
    assert "BREADTH_BELOW_OR_EQUAL_50_DATES" in res.additional_reporting
    assert "SIGNAL_OBSERVATIONS_AFTER_CONDITIONING" in res.additional_reporting

    # Verify conditioning counts sum to total
    total = res.additional_reporting["TOTAL_ELIGIBLE_DATES"]
    above = res.additional_reporting["BREADTH_ABOVE_50_DATES"]
    below = res.additional_reporting["BREADTH_BELOW_OR_EQUAL_50_DATES"]
    assert above + below == total


def test_zero_leakage_forward_timing():
    """Verify forward return uses strictly future dates after rebalance date."""
    engine = HypothesisEngine()
    res = engine.evaluate_hypothesis("H11-001")

    for p in res.rebalance_history:
        assert p.forward_end_date > p.rebalance_date
