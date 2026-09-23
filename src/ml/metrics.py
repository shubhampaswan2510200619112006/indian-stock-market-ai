"""
ML Evaluation Metrics & Calibration Engine.
Calculates statistical performance metrics, probability calibration, and feature importances.
Includes pure Python / numpy fallback calculations if sklearn or scipy are missing.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np

try:
    from scipy.stats import spearmanr
    from sklearn.metrics import (
        accuracy_score,
        brier_score_loss,
        confusion_matrix,
        f1_score,
        mean_absolute_error,
        mean_squared_error,
        precision_score,
        r2_score,
        recall_score,
        roc_auc_score,
    )
    HAS_SKLEARN_METRICS = True
except ImportError:
    HAS_SKLEARN_METRICS = False


@dataclass
class ClassificationMetrics:
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: Optional[float]
    brier_score: float
    expected_calibration_error: float
    confusion_matrix: List[List[int]]


@dataclass
class RegressionMetrics:
    mae: float
    rmse: float
    r2: float
    spearman_correlation: float
    directional_accuracy: float


def compute_expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 5) -> float:
    """Calculates Expected Calibration Error (ECE)."""
    if len(y_true) == 0:
        return 0.0
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    total_samples = len(y_true)

    for i in range(n_bins):
        bin_lower, bin_upper = bins[i], bins[i + 1]
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
        bin_size = np.sum(in_bin)
        if bin_size > 0:
            bin_acc = np.mean(y_true[in_bin])
            bin_conf = np.mean(y_prob[in_bin])
            ece += (bin_size / total_samples) * np.abs(bin_acc - bin_conf)
    return float(ece)


def evaluate_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: Optional[np.ndarray] = None) -> ClassificationMetrics:
    """Evaluates full classification metric suite."""
    if len(y_true) == 0:
        return ClassificationMetrics(
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1=0.0,
            roc_auc=None,
            brier_score=0.0,
            expected_calibration_error=0.0,
            confusion_matrix=[[0, 0], [0, 0]],
        )

    if HAS_SKLEARN_METRICS:
        acc = float(accuracy_score(y_true, y_pred))
        avg = "binary" if len(np.unique(y_true)) <= 2 else "weighted"
        prec = float(precision_score(y_true, y_pred, average=avg, zero_division=0))
        rec = float(recall_score(y_true, y_pred, average=avg, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, average=avg, zero_division=0))
        probs = y_prob if y_prob is not None else y_pred
        probs = np.clip(probs, 0.0, 1.0)
        try:
            roc = float(roc_auc_score(y_true, probs)) if len(np.unique(y_true)) == 2 else None
        except Exception:
            roc = None
        try:
            brier = float(brier_score_loss(y_true, probs)) if len(np.unique(y_true)) <= 2 else 0.0
        except Exception:
            brier = 0.0
        cm = confusion_matrix(y_true, y_pred).tolist()
    else:
        acc = float(np.mean(y_true == y_pred))
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        fn = np.sum((y_true == 1) & (y_pred == 0))
        tn = np.sum((y_true == 0) & (y_pred == 0))

        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        roc = None
        probs = y_prob if y_prob is not None else y_pred
        brier = float(np.mean((probs - y_true) ** 2))
        cm = [[int(tn), int(fp)], [int(fn), int(tp)]]

    ece = compute_expected_calibration_error(y_true, probs)

    return ClassificationMetrics(
        accuracy=acc,
        precision=prec,
        recall=rec,
        f1=f1,
        roc_auc=roc,
        brier_score=brier,
        expected_calibration_error=ece,
        confusion_matrix=cm,
    )


def evaluate_regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> RegressionMetrics:
    """Evaluates full regression metric suite."""
    if len(y_true) == 0:
        return RegressionMetrics(mae=0.0, rmse=0.0, r2=0.0, spearman_correlation=0.0, directional_accuracy=0.0)

    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    if HAS_SKLEARN_METRICS:
        r2 = float(r2_score(y_true, y_pred)) if len(np.unique(y_true)) > 1 else 0.0
        try:
            corr, _ = spearmanr(y_true, y_pred)
            spearman = float(corr) if not np.isnan(corr) else 0.0
        except Exception:
            spearman = 0.0
    else:
        var_y = np.var(y_true)
        r2 = float(1.0 - (np.sum((y_true - y_pred) ** 2) / (np.sum((y_true - np.mean(y_true)) ** 2) + 1e-8)))
        spearman = 0.0

    same_sign = (y_true * y_pred) > 0
    dir_acc = float(np.mean(same_sign))

    return RegressionMetrics(
        mae=mae,
        rmse=rmse,
        r2=r2,
        spearman_correlation=spearman,
        directional_accuracy=dir_acc,
    )
