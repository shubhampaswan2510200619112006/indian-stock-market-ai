"""
Test Multiplicity Control for Phase 11.
"""

import pytest
from src.research.phase11.multiplicity_controller import MultiplicityController


def test_multiplicity_controller_logic():
    mock_results = [
        {"hypothesis_id": "H11-001", "oos_net_expectancy_bps": -20.0, "statistical_evaluation": {"p_value": 0.85}},
        {"hypothesis_id": "H11-002", "oos_net_expectancy_bps": -10.0, "statistical_evaluation": {"p_value": 0.65}},
        {"hypothesis_id": "H11-003", "oos_net_expectancy_bps": -15.0, "statistical_evaluation": {"p_value": 0.75}},
        {"hypothesis_id": "H11-004", "oos_net_expectancy_bps": -40.0, "statistical_evaluation": {"p_value": 0.95}},
        {"hypothesis_id": "H11-005", "oos_net_expectancy_bps": -5.0, "statistical_evaluation": {"p_value": 0.55}},
        {"hypothesis_id": "H11-006", "oos_net_expectancy_bps": -12.0, "statistical_evaluation": {"p_value": 0.70}},
    ]

    res = MultiplicityController.apply_multiplicity_corrections(mock_results)

    assert res["total_primary_hypotheses"] == 6
    assert res["nominal_alpha"] == 0.05
    assert res["bonferroni_alpha"] == round(0.05 / 6.0, 5)
    assert res["bonferroni_survivors_count"] == 0
    assert res["bh_survivors_count"] == 0
    assert res["verdict_statement"] == "NO_STATISTICAL_CLAIM_SURVIVED_MULTIPLICITY_ADJUSTMENT"
