"""
Phase 9.5 — Probability Calibration Suite.

Evaluates and refines model probability outputs:
- Measures Brier score, calibration curves, and Expected Calibration Error (ECE).
- Implements Platt Scaling (Sigmoid) and Isotonic Regression calibration.
- Enforces strict isolation: Calibration models are fitted ONLY on training / validation folds.
- Calibration is strictly prohibited from touching the final test set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

try:
    from sklearn.calibration import CalibratedClassifierCV, calibration_curve
    from sklearn.isotonic import IsotonicRegression
    from sklearn.linear_model import LogisticRegression
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class CalibrationReport:
    model_name: str
    uncalibrated_brier_score: float
    calibrated_brier_score: float
    uncalibrated_ece: float
    calibrated_ece: float
    calibration_method: str
    reliability_curve_uncalibrated: Dict[str, List[float]]
    reliability_curve_calibrated: Dict[str, List[float]]
    is_calibration_beneficial: bool


class ProbabilityCalibrator:
    """
    Fits and applies probability calibration methods (Platt Scaling or Isotonic Regression)
    strictly on training/validation observations.
    """

    def __init__(self, method: str = "sigmoid"):
        """
        method: 'sigmoid' (Platt scaling) or 'isotonic' (Isotonic regression)
        """
        self.method = method.lower()
        self.is_fitted = False
        self.calibrator = None

    def fit(self, y_prob_train: np.ndarray, y_true_train: np.ndarray) -> "ProbabilityCalibrator":
        """
        Fits calibration model on (y_prob_train, y_true_train).
        """
        probs = np.clip(y_prob_train, 1e-6, 1.0 - 1e-6)
        if len(np.unique(y_true_train)) < 2:
            self.is_fitted = False
            return self

        if self.method == "isotonic":
            if HAS_SKLEARN:
                self.calibrator = IsotonicRegression(out_of_bounds="clip")
                self.calibrator.fit(probs, y_true_train)
                self.is_fitted = True
            else:
                self.is_fitted = False
        else:  # Platt scaling via Logistic Regression on log-odds
            if HAS_SKLEARN:
                log_odds = np.log(probs / (1.0 - probs)).reshape(-1, 1)
                self.calibrator = LogisticRegression()
                self.calibrator.fit(log_odds, y_true_train)
                self.is_fitted = True
            else:
                self.is_fitted = False

        return self

    def transform(self, y_prob: np.ndarray) -> np.ndarray:
        """Applies calibration transformation."""
        if not self.is_fitted or self.calibrator is None:
            return y_prob

        probs = np.clip(y_prob, 1e-6, 1.0 - 1e-6)
        if self.method == "isotonic":
            return np.clip(self.calibrator.predict(probs), 0.0, 1.0)
        else:
            log_odds = np.log(probs / (1.0 - probs)).reshape(-1, 1)
            return self.calibrator.predict_proba(log_odds)[:, 1]

    @staticmethod
    def calculate_brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
        """Calculates mean squared probability error (Brier score). Lower is better."""
        if len(y_true) == 0:
            return 0.0
        return float(np.mean((y_prob - y_true) ** 2))

    @staticmethod
    def calculate_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 5) -> Tuple[float, Dict[str, List[float]]]:
        """
        Calculates Expected Calibration Error (ECE) and reliability diagram coordinates.
        ECE = sum_b (|B_m| / N) * |acc(B_m) - conf(B_m)|
        """
        if len(y_true) == 0:
            return 0.0, {"prob_pred": [], "prob_true": [], "counts": []}

        bins = np.linspace(0.0, 1.0, n_bins + 1)
        bin_indices = np.digitize(y_prob, bins) - 1
        bin_indices = np.clip(bin_indices, 0, n_bins - 1)

        total_samples = len(y_true)
        ece = 0.0
        prob_pred_list = []
        prob_true_list = []
        counts_list = []

        for b in range(n_bins):
            mask = bin_indices == b
            count_b = np.sum(mask)
            if count_b > 0:
                mean_prob = float(np.mean(y_prob[mask]))
                mean_true = float(np.mean(y_true[mask]))
                weight = count_b / total_samples
                ece += weight * abs(mean_prob - mean_true)
                prob_pred_list.append(mean_prob)
                prob_true_list.append(mean_true)
                counts_list.append(int(count_b))

        return float(ece), {
            "prob_pred": prob_pred_list,
            "prob_true": prob_true_list,
            "counts": counts_list,
        }

    @classmethod
    def evaluate_calibration(
        cls,
        model_name: str,
        y_prob_train: np.ndarray,
        y_true_train: np.ndarray,
        y_prob_test: np.ndarray,
        y_true_test: np.ndarray,
        method: str = "sigmoid",
    ) -> CalibrationReport:
        """
        Trains calibrator strictly on train fold and evaluates change in ECE and Brier score on test fold.
        """
        uncal_brier = cls.calculate_brier_score(y_true_test, y_prob_test)
        uncal_ece, uncal_curve = cls.calculate_ece(y_true_test, y_prob_test)

        calibrator = cls(method=method)
        calibrator.fit(y_prob_train, y_true_train)
        cal_probs_test = calibrator.transform(y_prob_test)

        cal_brier = cls.calculate_brier_score(y_true_test, cal_probs_test)
        cal_ece, cal_curve = cls.calculate_ece(y_true_test, cal_probs_test)

        is_beneficial = (cal_brier <= uncal_brier) and (cal_ece <= uncal_ece)

        return CalibrationReport(
            model_name=model_name,
            uncalibrated_brier_score=uncal_brier,
            calibrated_brier_score=cal_brier,
            uncalibrated_ece=uncal_ece,
            calibrated_ece=cal_ece,
            calibration_method=method,
            reliability_curve_uncalibrated=uncal_curve,
            reliability_curve_calibrated=cal_curve,
            is_calibration_beneficial=is_beneficial,
        )
