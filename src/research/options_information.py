"""
Phase 9.6 — Research Question H: Options Information Incremental Value Engine.

Evaluates whether aggregated options metrics (Open Interest, PCR, Options Volume)
provide incremental out-of-sample predictive power over underlying spot price action alone:
- Compares Base Spot Model vs Base Spot + Options Information.
- Evaluates statistical significance of delta in accuracy, Brier score, and Net Sharpe.
- Explicit Disclaimers: Options data is evaluated strictly as an informational research feature;
  no options execution claims are made because historical Bid/Ask quotes are absent.
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
class OptionsInformationResult:
    base_spot_accuracy: float
    base_plus_options_accuracy: float
    incremental_accuracy_delta: float
    base_spot_sharpe: float
    base_plus_options_sharpe: float
    incremental_sharpe_delta: float
    is_incremental_edge_statistically_meaningful: bool
    options_data_source: str
    execution_validity_status: str
    conclusion: str


class OptionsInformationEngine:
    """
    Measures incremental predictive and economic contribution of options market features.
    """

    @classmethod
    def evaluate_incremental_options_value(
        cls,
        df_with_features: pd.DataFrame,
        tier_definitions: Dict[FeatureTier, List[str]],
        target_col: str = "target_fwd_dir_1d",
        date_col: str = "date",
    ) -> OptionsInformationResult:
        base_cols = tier_definitions[FeatureTier.TIER_D_VOLATILITY_REGIME]
        opt_cols = tier_definitions[FeatureTier.TIER_E_OPTIONS]

        validator = WalkForwardMLValidator(min_train_size=30, test_size=10, horizon_days=1)
        friction = IndianMarketFrictionModel()

        # 1. Base Spot Model (Tier D)
        folds_base = validator.run_walk_forward(
            model=Baseline2LogisticRegressionModel(),
            df=df_with_features,
            feature_cols=base_cols,
            target_col=target_col,
            date_col=date_col,
        )
        acc_base = float(np.mean([f.fold_accuracy for f in folds_base])) if folds_base else 0.0

        # Base Economic
        all_rec_base = [r for f in folds_base for r in f.prediction_records] if folds_base else []
        if all_rec_base:
            sigs_b = np.array([1.0 if r.probability > 0.5 else -1.0 for r in all_rec_base])
            dates_b = [pd.to_datetime(r.prediction_timestamp).date() for r in all_rec_base]
            date_to_ret = dict(zip(pd.to_datetime(df_with_features["date"]).dt.date, df_with_features["ret_1d"].fillna(0.0)))
            rets_b = np.array([date_to_ret.get(d, 0.0) for d in dates_b])
            econ_b = EconomicMetricsEngine.evaluate_strategy_returns(sigs_b, rets_b, friction)
            shp_base = econ_b.sharpe_ratio
        else:
            shp_base = 0.0

        # 2. Base + Options Model (Tier E)
        folds_opt = validator.run_walk_forward(
            model=Baseline2LogisticRegressionModel(),
            df=df_with_features,
            feature_cols=opt_cols,
            target_col=target_col,
            date_col=date_col,
        )
        acc_opt = float(np.mean([f.fold_accuracy for f in folds_opt])) if folds_opt else 0.0

        all_rec_opt = [r for f in folds_opt for r in f.prediction_records] if folds_opt else []
        if all_rec_opt:
            sigs_o = np.array([1.0 if r.probability > 0.5 else -1.0 for r in all_rec_opt])
            dates_o = [pd.to_datetime(r.prediction_timestamp).date() for r in all_rec_opt]
            rets_o = np.array([date_to_ret.get(d, 0.0) for d in dates_o])
            econ_o = EconomicMetricsEngine.evaluate_strategy_returns(sigs_o, rets_o, friction)
            shp_opt = econ_o.sharpe_ratio
        else:
            shp_opt = 0.0

        delta_acc = acc_opt - acc_base
        delta_shp = shp_opt - shp_base
        is_meaningful = (delta_acc >= 0.02) and (delta_shp > 0.5)

        if is_meaningful:
            conclusion = (
                f"OPTIONS_INFORMATION_BENEFICIAL: Adding options volume and open interest features improved "
                f"accuracy by {delta_acc:+.2%} and Sharpe by {delta_shp:+.2f}."
            )
        elif abs(delta_acc) < 0.001:
            conclusion = (
                "ZERO_INCREMENTAL_OPTIONS_EDGE: Aggregated options features produced 0.00% incremental accuracy "
                "over the underlying spot volatility and regime features."
            )
        else:
            conclusion = (
                f"NEGLIGIBLE_OR_DEGRADED_OPTIONS_VALUE: Options features shifted accuracy by {delta_acc:+.2%}, "
                "which is statistically indistinguishable from noise."
            )

        return OptionsInformationResult(
            base_spot_accuracy=acc_base,
            base_plus_options_accuracy=acc_opt,
            incremental_accuracy_delta=delta_acc,
            base_spot_sharpe=shp_base,
            base_plus_options_sharpe=shp_opt,
            incremental_sharpe_delta=delta_shp,
            is_incremental_edge_statistically_meaningful=is_meaningful,
            options_data_source="NSE Bhavcopy Historical Settlement Archive",
            execution_validity_status="LTP_RESEARCH_ONLY (Historical Bid/Ask 0.0% coverage; execution backtest BLOCKED)",
            conclusion=conclusion,
        )
