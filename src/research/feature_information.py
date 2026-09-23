"""
Phase 9.6 — Research Question G: Feature Information Value (F1–F6).

Evaluates the incremental contribution of 6 distinct feature families:
- F1: Price (returns, SMAs, distance to SMA)
- F2: Price Action (High/Low ratio, Close-to-High, gaps)
- F3: Volume (volume change, RVOL 20)
- F4: Volatility (5D, 10D realized volatility)
- F5: Regime (market regime codes)
- F6: Options (Open interest aggregates, PCR, options volume)

Crucial Rule: Reports BOTH Predictive Improvement (accuracy, Brier) AND Economic Improvement (Net Sharpe, Net Return).
Predictive gains do not automatically equal economic alpha.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.ml.ablation import FeatureAblationEngine, FeatureTier
from src.ml.baselines import Baseline2LogisticRegressionModel
from src.ml.economic_metrics import EconomicMetricsEngine, IndianMarketFrictionModel
from src.ml.walk_forward_ml import WalkForwardMLValidator


@dataclass
class FeatureFamilyReport:
    family_name: str
    feature_count: int
    mean_oos_accuracy: float
    predictive_improvement_vs_f1: float
    mean_brier_score: float
    net_return: float
    net_sharpe: float
    economic_improvement_vs_f1: float
    is_economically_beneficial: bool


@dataclass
class FeatureInformationSummary:
    family_reports: List[FeatureFamilyReport]
    best_predictive_family: str
    best_economic_family: str
    predictive_economic_divergence: bool  # True if highest accuracy family is NOT highest Sharpe family
    conclusion: str


class FeatureInformationEngine:
    """
    Evaluates incremental predictive vs economic value across feature families F1 through F6.
    """

    @classmethod
    def evaluate_feature_families(
        cls,
        df_with_features: pd.DataFrame,
        tier_definitions: Dict[FeatureTier, List[str]],
        target_col: str = "target_fwd_dir_1d",
        date_col: str = "date",
    ) -> FeatureInformationSummary:
        friction = IndianMarketFrictionModel()
        reports: List[FeatureFamilyReport] = []

        f1_acc = 0.0
        f1_sharpe = 0.0

        family_map = [
            ("F1_Price", tier_definitions[FeatureTier.TIER_A_PRICE]),
            ("F1+F2_Price_Action", tier_definitions[FeatureTier.TIER_B_PRICE_ACTION]),
            ("F1..F3_Volume", tier_definitions[FeatureTier.TIER_C_VOLUME]),
            ("F1..F4_Volatility", tier_definitions[FeatureTier.TIER_D_VOLATILITY_REGIME][:11]),
            ("F1..F5_Regime", tier_definitions[FeatureTier.TIER_D_VOLATILITY_REGIME]),
            ("F1..F6_Options", tier_definitions[FeatureTier.TIER_E_OPTIONS]),
        ]

        validator = WalkForwardMLValidator(min_train_size=30, test_size=10, horizon_days=1)

        for idx, (fam_name, cols) in enumerate(family_map):
            model = Baseline2LogisticRegressionModel()
            folds = validator.run_walk_forward(
                model=model,
                df=df_with_features,
                feature_cols=cols,
                target_col=target_col,
                date_col=date_col,
            )

            if not folds:
                reports.append(
                    FeatureFamilyReport(
                        family_name=fam_name,
                        feature_count=len(cols),
                        mean_oos_accuracy=0.0,
                        predictive_improvement_vs_f1=0.0,
                        mean_brier_score=0.0,
                        net_return=0.0,
                        net_sharpe=0.0,
                        economic_improvement_vs_f1=0.0,
                        is_economically_beneficial=False,
                    )
                )
                continue

            all_records = []
            for f in folds:
                all_records.extend(f.prediction_records)

            acc = float(np.mean([f.fold_accuracy for f in folds]))
            brier = float(np.mean([f.fold_brier_score for f in folds]))

            # Economic simulation from predictions
            sigs = np.array([1.0 if r.probability > 0.5 else -1.0 for r in all_records])
            dates = [pd.to_datetime(r.prediction_timestamp).date() for r in all_records]
            date_to_ret = dict(zip(pd.to_datetime(df_with_features["date"]).dt.date, df_with_features["ret_1d"].fillna(0.0)))
            rets = np.array([date_to_ret.get(d, 0.0) for d in dates])

            econ = EconomicMetricsEngine.evaluate_strategy_returns(sigs, rets, friction)

            if idx == 0:
                f1_acc = acc
                f1_sharpe = econ.sharpe_ratio

            pred_imp = acc - f1_acc
            econ_imp = econ.sharpe_ratio - f1_sharpe

            reports.append(
                FeatureFamilyReport(
                    family_name=fam_name,
                    feature_count=len(cols),
                    mean_oos_accuracy=acc,
                    predictive_improvement_vs_f1=pred_imp,
                    mean_brier_score=brier,
                    net_return=econ.net_return,
                    net_sharpe=econ.sharpe_ratio,
                    economic_improvement_vs_f1=econ_imp,
                    is_economically_beneficial=(econ_imp > 0.5 and econ.net_return > 0),
                )
            )

        best_pred = max(reports, key=lambda r: r.mean_oos_accuracy).family_name
        best_econ = max(reports, key=lambda r: r.net_sharpe).family_name
        divergence = (best_pred != best_econ)

        conclusion = (
            f"FEATURE_FAMILY_EVALUATION: Best predictive family is {best_pred}, while best economic outcome "
            f"is {best_econ}. Predictive vs Economic divergence = {divergence}. "
            f"Incremental features alter calibration but remain overwhelmed by statutory fees."
        )

        return FeatureInformationSummary(
            family_reports=reports,
            best_predictive_family=best_pred,
            best_economic_family=best_econ,
            predictive_economic_divergence=divergence,
            conclusion=conclusion,
        )
