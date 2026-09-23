"""
Comprehensive Integration & Unit Tests for Phase 6 & 6.5 Machine Learning Framework.
"""

from datetime import datetime
import numpy as np
import pandas as pd
import pytest

from src.ml.backtest_integration import MLBacktestEvaluator
from src.ml.baselines import MLBaselineModelSuite
from src.ml.feature_pipeline import MLFeaturePipeline
from src.ml.metrics import evaluate_classification_metrics, evaluate_regression_metrics
from src.ml.options_prediction_layer import OptionsPredictionLayer, SignalDirection
from src.ml.registry import ModelRegistry, ModelRegistryRecord
from src.ml.sufficiency import MLDataCoverageStatus, MLStatisticalEvidenceStatus, evaluate_dual_sufficiency
from src.ml.targets import TargetDefinition, TargetType, generate_directional_targets
from src.ml.walk_forward_ml import PredictionRecord, WalkForwardMLValidator


def test_data_sufficiency_evaluation():
    """Verifies that datasets are correctly classified under Dual Status evaluation."""
    res = evaluate_dual_sufficiency(
        total_observations=1240,
        trading_days_count=20,
        contracts_count=62,
        underlyings_count=1,
        expiries_count=1,
        independent_oos_trades=3,
        total_walk_forward_folds=3,
        fold_consistency_ratio=0.66,
    )
    assert res.data_coverage_status == MLDataCoverageStatus.LIMITED
    assert res.statistical_evidence_status == MLStatisticalEvidenceStatus.INSUFFICIENT
    assert "CRITICAL DISCLAIMER" in res.disclaimer


def test_baselines_suite_execution():
    """Verifies all baselines fit and predict cleanly on sample data."""
    X = np.random.randn(20, 5)
    y = np.random.choice([0, 1], size=20)

    baselines = MLBaselineModelSuite.get_all_baselines(is_classification=True)
    assert len(baselines) >= 5

    for key, model in baselines.items():
        model.fit(X, y)
        preds = model.predict(X)
        probs = model.predict_proba(X)
        assert len(preds) == 20
        assert probs.shape == (20, 2)


def test_walk_forward_validator_chronological():
    """Verifies walk-forward validator produces non-overlapping chronological test folds."""
    dates = pd.date_range("2026-08-01", periods=20, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "feat_1": np.random.randn(20),
        "feat_2": np.random.randn(20),
        "target": np.random.choice([0, 1], size=20),
    })

    model = MLBaselineModelSuite.get_all_baselines(is_classification=True)["Baseline_2_LogisticRegression"]
    validator = WalkForwardMLValidator(min_train_size=8, test_size=3, purge_window=1)

    folds = validator.run_walk_forward(model, df, feature_cols=["feat_1", "feat_2"], target_col="target", date_col="date")

    assert len(folds) > 0
    for fold in folds:
        assert fold.train_end < fold.test_start, "Train end must strictly precede test start!"


def test_metrics_and_calibration():
    """Verifies classification and regression metrics evaluation."""
    y_true = np.array([1, 0, 1, 1, 0, 1, 0, 0])
    y_pred = np.array([1, 0, 1, 0, 0, 1, 0, 1])
    y_prob = np.array([0.9, 0.1, 0.8, 0.4, 0.2, 0.85, 0.15, 0.6])

    metrics = evaluate_classification_metrics(y_true, y_pred, y_prob)
    assert 0.0 <= metrics.accuracy <= 1.0
    assert 0.0 <= metrics.expected_calibration_error <= 1.0
    assert metrics.brier_score >= 0.0


def test_options_prediction_layer_no_trade():
    """Verifies that prediction layer outputs NO_TRADE on INSUFFICIENT status or low confidence."""
    layer = OptionsPredictionLayer()

    # Case 1: INSUFFICIENT data coverage status
    sig1 = layer.generate_signal("NIFTY", "2026-08-15", 0.85, MLDataCoverageStatus.INSUFFICIENT)
    assert sig1.direction == SignalDirection.NO_TRADE
    assert not sig1.is_trade_allowed

    # Case 2: Neutral probability on LIMITED dataset
    sig2 = layer.generate_signal("NIFTY", "2026-08-15", 0.51, MLDataCoverageStatus.LIMITED)
    assert sig2.direction == SignalDirection.NO_TRADE
    assert not sig2.is_trade_allowed

    # Case 3: High bullish probability on LIMITED dataset
    sig3 = layer.generate_signal("NIFTY", "2026-08-15", 0.75, MLDataCoverageStatus.LIMITED)
    assert sig3.direction == SignalDirection.BULLISH
    assert sig3.is_trade_allowed


def test_model_registry_persistence(tmp_path):
    """Verifies model registration and retrieval in ModelRegistry."""
    filepath = str(tmp_path / "test_registry.json")
    registry = ModelRegistry(registry_filepath=filepath)

    record = ModelRegistryRecord(
        model_name="Baseline 2: Logistic Regression",
        model_version="v1.0",
        target_name="dir_return_1d",
        feature_version="v1.0",
        dataset_hash="abc123hash",
        training_period_start="2026-08-01",
        training_period_end="2026-08-15",
        hyperparameters={"max_iter": 1000},
        data_sufficiency_status="LIMITED",
        validation_accuracy=0.65,
        oos_accuracy=0.60,
        oos_brier_score=0.22,
    )

    registry.register_model(record)
    models = registry.list_models()
    assert len(models) == 1
    assert models[0]["model_name"] == "Baseline 2: Logistic Regression"
