"""
Phase 9.5 — Chronological Walk-Forward Validator with Dynamic Purging & Embargo.

Enforces strict out-of-sample isolation:
- Never randomly shuffles time series observations.
- Supports expanding and rolling window chronological folds: TRAIN -> VALIDATION -> OOS.
- Dynamically calculates purge window from prediction horizon h to prevent label overlap.
- Supports embargo window to eliminate serial correlation leakage.
- Holds the final untouched test partition completely isolated from feature selection,
  hyperparameter tuning, and threshold calibration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.ml.baselines import MLBaseModel
from src.ml.metrics import evaluate_classification_metrics


@dataclass
class PredictionRecord:
    prediction_timestamp: datetime
    target_timestamp: datetime
    actual_outcome: float
    prediction: float
    probability: float
    model_name: str
    model_version: str
    feature_version: str


@dataclass
class WalkForwardFoldResult:
    fold_index: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    train_count: int
    test_count: int
    fold_accuracy: float = 0.0
    fold_f1: float = 0.0
    fold_brier_score: float = 0.0
    fold_mae: float = 0.0
    fold_rmse: float = 0.0
    prediction_records: List[PredictionRecord] = field(default_factory=list)


@dataclass
class ChronologicalPartition:
    train_df: pd.DataFrame
    val_df: pd.DataFrame
    untouched_test_df: pd.DataFrame
    purge_size: int
    embargo_size: int


class WalkForwardMLValidator:
    """
    Chronological Walk-Forward Validator.
    Implements expanding or rolling window validation with dynamic purging and embargo.
    """

    def __init__(
        self,
        min_train_size: int = 10,
        test_size: int = 5,
        purge_window: Optional[int] = None,
        embargo_window: int = 0,
        expanding: bool = True,
        horizon_days: int = 1,
    ):
        self.min_train_size = min_train_size
        self.test_size = test_size
        # Dynamically calculate purge requirement from prediction horizon if not explicitly set
        self.horizon_days = horizon_days
        self.purge_window = purge_window if purge_window is not None else max(1, horizon_days)
        self.embargo_window = embargo_window
        self.expanding = expanding

    @staticmethod
    def calculate_purge_requirement(
        prediction_horizon: int,
        label_window: int = 1,
        feature_lookback: int = 1,
    ) -> int:
        """
        Dynamically calculates purge requirement based on horizon, label window, and lookback.
        Purge ensures that target spanning T..T+h does not leak into training or validation.
        """
        return max(1, prediction_horizon + label_window - 1)

    @classmethod
    def create_tripartite_partition(
        cls,
        df: pd.DataFrame,
        test_ratio: float = 0.2,
        val_ratio: float = 0.2,
        horizon_days: int = 1,
        embargo_days: int = 0,
        date_col: str = "date",
    ) -> ChronologicalPartition:
        """
        Splits dataset into:
        TRAIN (early) -> [PURGE] -> VALIDATION (middle) -> [PURGE/EMBARGO] -> UNTOUCHED TEST (latest)
        Strictly chronological. Zero shuffling.
        """
        df_sorted = df.sort_values(by=date_col).reset_index(drop=True)
        n = len(df_sorted)
        purge_size = max(1, horizon_days)

        test_count = max(5, int(n * test_ratio))
        val_count = max(5, int(n * val_ratio))

        # Test occupies the final slice
        test_start_idx = n - test_count
        test_df = df_sorted.iloc[test_start_idx:].copy()

        # Validation occupies slice before test minus purge/embargo
        val_end_idx = max(0, test_start_idx - purge_size - embargo_days)
        val_start_idx = max(0, val_end_idx - val_count)
        val_df = df_sorted.iloc[val_start_idx:val_end_idx].copy()

        # Train occupies slice before validation minus purge
        train_end_idx = max(0, val_start_idx - purge_size)
        train_df = df_sorted.iloc[0:train_end_idx].copy()

        return ChronologicalPartition(
            train_df=train_df,
            val_df=val_df,
            untouched_test_df=test_df,
            purge_size=purge_size,
            embargo_size=embargo_days,
        )

    def run_walk_forward(
        self,
        model: MLBaseModel,
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str,
        date_col: str = "date",
        feature_version: str = "v1.0",
        is_classification: bool = True,
    ) -> List[WalkForwardFoldResult]:
        """
        Executes chronological walk-forward cross-validation fold by fold.
        """
        df_sorted = df.sort_values(by=date_col).reset_index(drop=True)
        n = len(df_sorted)
        effective_purge = self.purge_window

        if n < self.min_train_size + self.test_size:
            return []

        fold_results: List[WalkForwardFoldResult] = []
        fold_idx = 0

        current_test_start = self.min_train_size

        while current_test_start + self.test_size <= n:
            test_end_idx = current_test_start + self.test_size

            # Determine Train indices with purge applied
            train_end_idx = current_test_start - effective_purge
            if train_end_idx <= 0:
                current_test_start += self.test_size
                continue

            if self.expanding:
                train_start_idx = 0
            else:
                train_start_idx = max(0, train_end_idx - self.min_train_size)

            train_df = df_sorted.iloc[train_start_idx:train_end_idx]
            test_df = df_sorted.iloc[current_test_start:test_end_idx]

            # Drop NaNs
            train_clean = train_df.dropna(subset=feature_cols + [target_col])
            test_clean = test_df.dropna(subset=feature_cols + [target_col])

            if len(train_clean) < 3 or len(test_clean) < 1:
                current_test_start += self.test_size
                continue

            X_train = train_clean[feature_cols].values
            y_train = train_clean[target_col].values

            X_test = test_clean[feature_cols].values
            y_test = test_clean[target_col].values

            # Fit model strictly on training fold
            model.fit(X_train, y_train)

            # Predict on out-of-sample test fold
            preds = model.predict(X_test)
            if is_classification:
                probas = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else preds
            else:
                probas = preds

            records: List[PredictionRecord] = []
            for i in range(len(test_clean)):
                row_date = pd.to_datetime(test_clean[date_col].iloc[i])
                records.append(
                    PredictionRecord(
                        prediction_timestamp=row_date,
                        target_timestamp=row_date,
                        actual_outcome=float(y_test[i]),
                        prediction=float(preds[i]),
                        probability=float(probas[i]),
                        model_name=model.name,
                        model_version=model.model_version,
                        feature_version=feature_version,
                    )
                )

            fold_acc = 0.0
            fold_f1 = 0.0
            fold_brier = 0.0
            fold_mae = float(np.mean(np.abs(preds - y_test)))
            fold_rmse = float(np.sqrt(np.mean((preds - y_test) ** 2)))

            if is_classification:
                metrics = evaluate_classification_metrics(y_test, preds, probas)
                fold_acc = metrics.accuracy
                fold_f1 = metrics.f1
                fold_brier = metrics.brier_score

            t_start = pd.to_datetime(test_clean[date_col].iloc[0])
            t_end = pd.to_datetime(test_clean[date_col].iloc[-1])
            tr_start = pd.to_datetime(train_clean[date_col].iloc[0])
            tr_end = pd.to_datetime(train_clean[date_col].iloc[-1])

            fold_results.append(
                WalkForwardFoldResult(
                    fold_index=fold_idx,
                    train_start=tr_start,
                    train_end=tr_end,
                    test_start=t_start,
                    test_end=t_end,
                    train_count=len(train_clean),
                    test_count=len(test_clean),
                    fold_accuracy=fold_acc,
                    fold_f1=fold_f1,
                    fold_brier_score=fold_brier,
                    fold_mae=fold_mae,
                    fold_rmse=fold_rmse,
                    prediction_records=records,
                )
            )

            fold_idx += 1
            current_test_start += self.test_size

        return fold_results
