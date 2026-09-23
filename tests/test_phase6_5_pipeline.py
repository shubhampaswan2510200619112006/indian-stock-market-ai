"""
Comprehensive Integration & Unit Tests for Phase 6.5 Extensions.
Verifies Dual Status evaluation, Block Bootstrap CIs, Permutation Testing, and Per-Fold Walk-Forward Reporting.
"""

import numpy as np
import pandas as pd
import pytest

from src.ml.statistical_validation import compute_block_bootstrap_ci, compute_permutation_test
from src.ml.sufficiency import (
    DualSufficiencyResult,
    MLDataCoverageStatus,
    MLStatisticalEvidenceStatus,
    evaluate_dual_sufficiency,
)
from src.ml.walk_forward_ml import WalkForwardMLValidator
from src.ml.baselines import MLBaselineModelSuite


def test_dual_sufficiency_evaluation():
    """
    Verifies that Data Coverage Status and Statistical Evidence Status are evaluated separately.
    High quote volume does NOT automatically yield STRONG statistical evidence.
    """
    # High quote count (55k), but few OOS trades (3 trades)
    res = evaluate_dual_sufficiency(
        total_observations=55000,
        trading_days_count=600,
        contracts_count=100,
        underlyings_count=2,
        expiries_count=5,
        independent_oos_trades=3,  # Few trades!
        total_walk_forward_folds=3,
        fold_consistency_ratio=0.50,
    )
    assert res.data_coverage_status == MLDataCoverageStatus.STRONG
    assert res.statistical_evidence_status == MLStatisticalEvidenceStatus.INSUFFICIENT


def test_block_bootstrap_confidence_intervals():
    """Verifies Block Bootstrap 95% CI computation and dependence disclaimers."""
    values = np.array([1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1])
    boot = compute_block_bootstrap_ci(values, n_iterations=200, confidence_level=0.95, block_size=3)

    assert 0.0 <= boot.ci_lower <= boot.ci_upper <= 1.0
    assert boot.bootstrap_iterations == 200
    assert "BOOTSTRAP LIMITATION" in boot.dependence_disclaimer


def test_permutation_test():
    """Verifies permutation test for null hypothesis evaluation."""
    y_true = np.array([1, 0, 1, 0, 1, 0, 1, 0])
    y_pred = np.array([1, 0, 1, 0, 1, 0, 1, 0])

    perm = compute_permutation_test(y_true, y_pred, n_permutations=200)
    assert perm.observed_value == 1.0
    assert perm.p_value <= 0.05
    assert "H0" in perm.null_hypothesis


def test_walk_forward_per_fold_metrics():
    """Verifies per-fold metric computation in WalkForwardMLValidator."""
    dates = pd.date_range("2026-08-01", periods=20, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "feat_1": np.random.randn(20),
        "target": np.random.choice([0, 1], size=20),
    })

    model = MLBaselineModelSuite.get_all_baselines(is_classification=True)["Baseline_2_LogisticRegression"]
    validator = WalkForwardMLValidator(min_train_size=8, test_size=3, purge_window=1)

    folds = validator.run_walk_forward(model, df, feature_cols=["feat_1"], target_col="target", date_col="date")

    assert len(folds) > 0
    for fold in folds:
        assert hasattr(fold, "fold_accuracy")
        assert hasattr(fold, "fold_f1")
        assert hasattr(fold, "fold_brier_score")
