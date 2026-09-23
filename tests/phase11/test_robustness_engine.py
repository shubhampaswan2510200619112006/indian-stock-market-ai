"""
Test Robustness Engine for Phase 11.
"""

import pytest
from src.research.phase11.hypothesis_engine import HypothesisEngine
from src.research.phase11.robustness_engine import RobustnessEngine


def test_robustness_engine_execution():
    engine = HypothesisEngine()
    rob = RobustnessEngine(engine)
    res = rob.run_all_robustness_checks()

    assert len(res) == 6
    for hid in ["H11-001", "H11-002", "H11-003", "H11-004", "H11-005", "H11-006"]:
        assert hid in res
        item = res[hid]
        assert "cost_stress" in item
        assert "1.0x_baseline" in item["cost_stress"]
        assert "1.5x_stress" in item["cost_stress"]
        assert "2.0x_stress" in item["cost_stress"]
        assert "partition_stability" in item
        assert "survives_cost_stress" in item
