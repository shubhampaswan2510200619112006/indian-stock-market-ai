"""
Machine Learning & Predictive Modeling Research Engine (Phase 6 & 6.5).
"""

from src.ml.sufficiency import (
    MLDataCoverageStatus,
    MLStatisticalEvidenceStatus,
    evaluate_dual_sufficiency,
)
from src.ml.targets import TargetType, TargetDefinition, TargetObservation
from src.ml.feature_pipeline import MLFeaturePipeline
from src.ml.baselines import MLBaselineModelSuite
from src.ml.walk_forward_ml import WalkForwardMLValidator
from src.ml.metrics import evaluate_classification_metrics, evaluate_regression_metrics
from src.ml.options_prediction_layer import OptionsPredictionLayer
from src.ml.registry import ModelRegistry
from src.ml.backtest_integration import MLBacktestEvaluator
from src.ml.execution_timing import ExecutionAuditReport, ExecutionPriceSource, ModelAExecutionTimer
from src.ml.statistical_validation import compute_block_bootstrap_ci, compute_permutation_test

__all__ = [
    "MLDataCoverageStatus",
    "MLStatisticalEvidenceStatus",
    "evaluate_dual_sufficiency",
    "TargetType",
    "TargetDefinition",
    "TargetObservation",
    "MLFeaturePipeline",
    "MLBaselineModelSuite",
    "WalkForwardMLValidator",
    "evaluate_classification_metrics",
    "evaluate_regression_metrics",
    "OptionsPredictionLayer",
    "ModelRegistry",
    "MLBacktestEvaluator",
    "ExecutionAuditReport",
    "ExecutionPriceSource",
    "ModelAExecutionTimer",
    "compute_block_bootstrap_ci",
    "compute_permutation_test",
]
