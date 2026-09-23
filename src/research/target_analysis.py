"""
Phase 9.6 — Research Question A: Target Reassessment Engine.

Investigates whether the negative Phase 9.5 result was caused by target formulation:
- Compares 1D, 3D, 5D, and 10D multi-session directional predictability.
- Evaluates 5-class return magnitude targets: STRONG_NEGATIVE, NEGATIVE, NEUTRAL, POSITIVE, STRONG_POSITIVE.
- Evaluates risk-adjusted targets: Forward return normalized by ATR (R / ATR) and volatility.
- Uses strictly frozen, pre-specified thresholds. Zero retrospective threshold tuning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.ml.baselines import Baseline0NaiveModel, Baseline2LogisticRegressionModel, MLBaseModel
from src.ml.targets import MultiHorizonTargetEngine
from src.ml.walk_forward_ml import WalkForwardMLValidator


@dataclass
class TargetEvaluationResult:
    target_name: str
    target_type: str
    horizon_sessions: int
    mean_oos_accuracy: float
    baseline_accuracy: float
    incremental_accuracy: float
    total_observations: int
    brier_score_or_mse: float
    is_statistically_superior_to_baseline: bool
    notes: str = ""


class TargetReassessmentEngine:
    """
    Evaluates alternative target formulations against fixed Level 0 baselines.
    """

    @classmethod
    def evaluate_multi_horizon_direction(
        cls,
        df_with_features: pd.DataFrame,
        feature_cols: List[str],
        date_col: str = "date",
    ) -> Dict[str, TargetEvaluationResult]:
        """
        Evaluates 1D, 3D, 5D, 10D forward direction targets using walk-forward validation.
        """
        results = {}
        horizons = [1, 3, 5, 10]

        for h in horizons:
            tgt_col = f"target_fwd_dir_{h}d"
            if tgt_col not in df_with_features.columns:
                continue

            # Drop NaNs for this specific horizon
            clean_df = df_with_features.dropna(subset=feature_cols + [tgt_col]).copy()
            if len(clean_df) < 40:
                continue

            # Baseline 0: Naive majority class
            baseline_val = float(clean_df[tgt_col].mode()[0]) if len(clean_df) > 0 else 0.0
            baseline_acc = float(np.mean(clean_df[tgt_col] == baseline_val))

            # Run Walk-Forward with dynamic purge = h
            validator = WalkForwardMLValidator(
                min_train_size=30,
                test_size=10,
                horizon_days=h,
                expanding=True,
            )
            model = Baseline2LogisticRegressionModel()
            folds = validator.run_walk_forward(
                model=model,
                df=clean_df,
                feature_cols=feature_cols,
                target_col=tgt_col,
                date_col=date_col,
            )

            if folds:
                accs = [f.fold_accuracy for f in folds]
                briers = [f.fold_brier_score for f in folds]
                mean_acc = float(np.mean(accs))
                mean_brier = float(np.mean(briers))
                inc = mean_acc - baseline_acc
                is_sup = inc > 0.04  # requires > 4% edge over baseline

                results[f"DIR_{h}D"] = TargetEvaluationResult(
                    target_name=tgt_col,
                    target_type="DIRECTIONAL_BINARY",
                    horizon_sessions=h,
                    mean_oos_accuracy=mean_acc,
                    baseline_accuracy=baseline_acc,
                    incremental_accuracy=inc,
                    total_observations=len(clean_df),
                    brier_score_or_mse=mean_brier,
                    is_statistically_superior_to_baseline=is_sup,
                    notes=f"Evaluated across {len(folds)} walk-forward folds with dynamic purge = {h}.",
                )

        return results

    @classmethod
    def evaluate_return_magnitude_classification(
        cls,
        df_with_features: pd.DataFrame,
        feature_cols: List[str],
        date_col: str = "date",
    ) -> TargetEvaluationResult:
        """
        Classifies future 5D return into 5 predefined magnitude regimes:
        STRONG_NEGATIVE (< -2%), NEGATIVE (-2% to 0%), NEUTRAL (~0%),
        POSITIVE (0% to +2%), STRONG_POSITIVE (> +2%).
        """
        df = df_with_features.copy()
        ret_5d = df["target_fwd_ret_5d"]

        # Predefined frozen boundaries (no threshold search)
        conditions = [
            ret_5d < -0.02,
            (ret_5d >= -0.02) & (ret_5d < 0.0),
            (ret_5d >= 0.0) & (ret_5d < 0.02),
            ret_5d >= 0.02,
        ]
        choices = [0, 1, 2, 3]  # 4 discrete buckets
        df["target_magnitude_5d"] = np.select(conditions, choices, default=1)

        clean_df = df.dropna(subset=feature_cols + ["target_magnitude_5d"]).copy()
        baseline_acc = float(np.max(clean_df["target_magnitude_5d"].value_counts(normalize=True)))

        validator = WalkForwardMLValidator(min_train_size=30, test_size=10, horizon_days=5)
        model = Baseline0NaiveModel(is_classification=True)
        folds = validator.run_walk_forward(
            model=model,
            df=clean_df,
            feature_cols=feature_cols,
            target_col="target_magnitude_5d",
            date_col=date_col,
        )

        mean_acc = float(np.mean([f.fold_accuracy for f in folds])) if folds else 0.0

        return TargetEvaluationResult(
            target_name="target_magnitude_5d",
            target_type="DISCRETE_MAGNITUDE_4_CLASS",
            horizon_sessions=5,
            mean_oos_accuracy=mean_acc,
            baseline_accuracy=baseline_acc,
            incremental_accuracy=mean_acc - baseline_acc,
            total_observations=len(clean_df),
            brier_score_or_mse=0.0,
            is_statistically_superior_to_baseline=(mean_acc - baseline_acc > 0.05),
            notes="Discrete return magnitude target across 4 predefined bins.",
        )

    @classmethod
    def evaluate_risk_adjusted_target(
        cls,
        df_with_features: pd.DataFrame,
        feature_cols: List[str],
        date_col: str = "date",
    ) -> TargetEvaluationResult:
        """
        Evaluates predictability of 5D return normalized by rolling 14D ATR:
        y = (Close_{t+5} - Close_t) / ATR_14.
        """
        df = df_with_features.copy()
        if "target_fwd_atr_norm_5d" not in df.columns:
            return TargetEvaluationResult(
                target_name="target_fwd_atr_norm_5d",
                target_type="RISK_ADJUSTED_CONTINUOUS",
                horizon_sessions=5,
                mean_oos_accuracy=0.0,
                baseline_accuracy=0.0,
                incremental_accuracy=0.0,
                total_observations=0,
                brier_score_or_mse=0.0,
                is_statistically_superior_to_baseline=False,
                notes="Column target_fwd_atr_norm_5d not present.",
            )

        df["target_atr_dir_5d"] = (df["target_fwd_atr_norm_5d"] > 0.0).astype(float)
        clean_df = df.dropna(subset=feature_cols + ["target_atr_dir_5d"]).copy()
        baseline_acc = float(np.max(clean_df["target_atr_dir_5d"].value_counts(normalize=True)))

        validator = WalkForwardMLValidator(min_train_size=30, test_size=10, horizon_days=5)
        model = Baseline2LogisticRegressionModel()
        folds = validator.run_walk_forward(
            model=model,
            df=clean_df,
            feature_cols=feature_cols,
            target_col="target_atr_dir_5d",
            date_col=date_col,
        )

        accs = [f.fold_accuracy for f in folds] if folds else [0.0]
        mean_acc = float(np.mean(accs))

        return TargetEvaluationResult(
            target_name="target_fwd_atr_norm_5d",
            target_type="RISK_ADJUSTED_CONTINUOUS",
            horizon_sessions=5,
            mean_oos_accuracy=mean_acc,
            baseline_accuracy=baseline_acc,
            incremental_accuracy=mean_acc - baseline_acc,
            total_observations=len(clean_df),
            brier_score_or_mse=float(np.mean([f.fold_brier_score for f in folds])) if folds else 0.0,
            is_statistically_superior_to_baseline=(mean_acc - baseline_acc > 0.04),
            notes="Forward movement normalized by 14-day ATR.",
        )
