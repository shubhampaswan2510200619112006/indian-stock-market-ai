"""
Test Statistical Evaluator and Block Bootstrap for Phase 11.
"""

import pytest
import numpy as np
from src.research.phase11.statistical_evaluator import StatisticalEvaluator, BOOTSTRAP_RESAMPLES, SEED


def test_bootstrap_configuration():
    assert BOOTSTRAP_RESAMPLES == 1000
    assert SEED == 42


def test_bootstrap_execution_and_reproducibility():
    sample_data = [-25.0, 10.0, -15.0, -30.0, 5.0, -10.0, -40.0, 2.0, -18.0, -22.0]
    res1 = StatisticalEvaluator.run_stationary_block_bootstrap(sample_data, block_length=5, resamples=1000, seed=42)
    res2 = StatisticalEvaluator.run_stationary_block_bootstrap(sample_data, block_length=5, resamples=1000, seed=42)

    assert res1.mean_bps == res2.mean_bps
    assert res1.ci_lower_bps == res2.ci_lower_bps
    assert res1.ci_upper_bps == res2.ci_upper_bps
    assert res1.p_value == res2.p_value
    assert res1.resamples == 1000
    assert res1.seed == 42


def test_block_length_sensitivity_checks():
    sample_data = [-25.0, 10.0, -15.0, -30.0, 5.0, -10.0, -40.0, 2.0, -18.0, -22.0]
    res = StatisticalEvaluator.run_stationary_block_bootstrap(sample_data, block_length=5, resamples=1000, seed=42)

    sens = res.sensitivity_checks
    assert "block_length_3" in sens
    assert "block_length_10" in sens
    assert "ci_lower_bps" in sens["block_length_3"]
    assert "ci_upper_bps" in sens["block_length_10"]
