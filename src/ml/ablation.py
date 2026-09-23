"""
Phase 9.5 — 5-Tier Feature Ablation Suite.

Evaluates progressive feature complexity tiers:
- Tier A: Price Only (returns, moving averages, momentum, trend)
- Tier B: Price + Price Action (high/low ratios, close-to-high, gaps, candle ranges)
- Tier C: A + B + Volume (volume changes, RVOL, abnormal volume)
- Tier D: A + B + C + Volatility & Regime (realized volatility, regime codes, India VIX)
- Tier E: A + B + C + D + Options (OI, change in OI, option volume, PCR, IV, Greeks)

Reports incremental out-of-sample contribution across all tiers:
Mean, median, best, worst, and delta relative to baseline.
Determines objectively whether added feature complexity adds genuine predictive value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.features.market_regime import MarketRegimeEngine
from src.ml.baselines import MLBaseModel
from src.ml.walk_forward_ml import WalkForwardFoldResult, WalkForwardMLValidator


class FeatureTier(str, Enum):
    TIER_A_PRICE = "TIER_A_PRICE"
    TIER_B_PRICE_ACTION = "TIER_B_PRICE_ACTION"
    TIER_C_VOLUME = "TIER_C_VOLUME"
    TIER_D_VOLATILITY_REGIME = "TIER_D_VOLATILITY_REGIME"
    TIER_E_OPTIONS = "TIER_E_OPTIONS"


@dataclass
class TierEvaluationResult:
    tier: FeatureTier
    feature_count: int
    feature_names: List[str]
    mean_accuracy: float
    median_accuracy: float
    best_accuracy: float
    worst_accuracy: float
    mean_f1: float
    mean_brier: float
    incremental_accuracy_vs_tier_a: float
    fold_accuracies: List[float] = field(default_factory=list)


class FeatureAblationEngine:
    """
    Constructs the 5 predefined feature tiers and evaluates progressive OOS contribution.
    """

    @classmethod
    def generate_features_all_tiers(
        cls,
        df: pd.DataFrame,
        option_quotes_df: Optional[pd.DataFrame] = None,
        symbol: str = "NIFTY",
    ) -> Tuple[pd.DataFrame, Dict[FeatureTier, List[str]]]:
        """
        Builds unified feature matrix and partitions feature names into Tiers A, B, C, D, E.
        """
        df_out = df.sort_values(by="date").copy().reset_index(drop=True)

        # -----------------------------------------------------------------
        # Tier A: Price Only
        # -----------------------------------------------------------------
        df_out["ret_1d"] = df_out["close"].pct_change(1)
        df_out["ret_3d"] = df_out["close"].pct_change(3)
        df_out["ret_5d"] = df_out["close"].pct_change(5)
        df_out["sma_5"] = df_out["close"].rolling(5).mean()
        df_out["sma_20"] = df_out["close"].rolling(20).mean()
        df_out["dist_sma_20"] = (df_out["close"] - df_out["sma_20"]) / df_out["sma_20"]

        tier_a_cols = ["ret_1d", "ret_3d", "ret_5d", "dist_sma_20"]

        # -----------------------------------------------------------------
        # Tier B: Price Action
        # -----------------------------------------------------------------
        if "high" in df_out.columns and "low" in df_out.columns:
            df_out["high_low_ratio"] = (df_out["high"] - df_out["low"]) / df_out["close"]
            df_out["close_to_high"] = (df_out["high"] - df_out["close"]) / (df_out["high"] - df_out["low"] + 1e-6)
            df_out["gap_open"] = (df_out["open"] - df_out["close"].shift(1)) / df_out["close"].shift(1)
        else:
            df_out["high_low_ratio"] = 0.0
            df_out["close_to_high"] = 0.5
            df_out["gap_open"] = 0.0

        tier_b_cols = tier_a_cols + ["high_low_ratio", "close_to_high", "gap_open"]

        # -----------------------------------------------------------------
        # Tier C: Volume
        # -----------------------------------------------------------------
        if "volume" in df_out.columns:
            df_out["vol_change_1d"] = df_out["volume"].pct_change(1)
            vol_sma_20 = df_out["volume"].rolling(20).mean()
            df_out["rvol_20"] = df_out["volume"] / np.maximum(vol_sma_20, 1.0)
        else:
            df_out["vol_change_1d"] = 0.0
            df_out["rvol_20"] = 1.0

        tier_c_cols = tier_b_cols + ["vol_change_1d", "rvol_20"]

        # -----------------------------------------------------------------
        # Tier D: Volatility & Regime
        # -----------------------------------------------------------------
        log_rets = np.log(df_out["close"] / df_out["close"].shift(1))
        df_out["rv_5d"] = log_rets.rolling(5).std() * np.sqrt(252)
        df_out["rv_10d"] = log_rets.rolling(10).std() * np.sqrt(252)

        regime_engine = MarketRegimeEngine()
        regime_codes = []
        regime_names = []
        regime_map = {
            "STRONG_BULL": 2,
            "BULL": 1,
            "SIDEWAYS": 0,
            "BEAR": -1,
            "STRONG_BEAR": -2,
            "HIGH_VOLATILITY": 3,
            "UNKNOWN": 0,
        }
        for idx in range(len(df_out)):
            sub_df = df_out.iloc[: idx + 1]
            if len(sub_df) >= 5:
                reg = regime_engine.evaluate_regime(sub_df, symbol=symbol)
                regime_codes.append(regime_map.get(reg.regime.value, 0))
                regime_names.append(reg.regime.value)
            else:
                regime_codes.append(0)
                regime_names.append("SIDEWAYS")
        df_out["regime_code"] = regime_codes
        df_out["market_regime"] = regime_names

        tier_d_cols = tier_c_cols + ["rv_5d", "rv_10d", "regime_code"]

        # -----------------------------------------------------------------
        # Tier E: Options Aggregates (LTP research)
        # -----------------------------------------------------------------
        if option_quotes_df is not None and not option_quotes_df.empty:
            opt_df = option_quotes_df.copy()
            opt_df["date_val"] = pd.to_datetime(opt_df["timestamp"]).dt.date
            df_out["date_key"] = pd.to_datetime(df_out["date"]).dt.date

            agg_opt = (
                opt_df.groupby("date_val")
                .agg(
                    total_opt_volume=("volume", "sum"),
                    total_opt_oi=("open_interest", "sum"),
                    avg_opt_price=("last_price", "mean"),
                )
                .reset_index()
            )
            df_out = df_out.merge(agg_opt, left_on="date_key", right_on="date_val", how="left")
            df_out["total_opt_volume"] = df_out["total_opt_volume"].fillna(0.0)
            df_out["total_opt_oi"] = df_out["total_opt_oi"].fillna(0.0)
            df_out.drop(columns=["date_key", "date_val"], errors="ignore", inplace=True)
        else:
            df_out["total_opt_volume"] = 0.0
            df_out["total_opt_oi"] = 0.0

        tier_e_cols = tier_d_cols + ["total_opt_volume", "total_opt_oi"]

        # Clean NaNs by backward look only
        all_cols = list(set(tier_e_cols))
        df_out[all_cols] = df_out[all_cols].ffill().fillna(0.0)

        tier_definitions = {
            FeatureTier.TIER_A_PRICE: tier_a_cols,
            FeatureTier.TIER_B_PRICE_ACTION: tier_b_cols,
            FeatureTier.TIER_C_VOLUME: tier_c_cols,
            FeatureTier.TIER_D_VOLATILITY_REGIME: tier_d_cols,
            FeatureTier.TIER_E_OPTIONS: tier_e_cols,
        }

        return df_out, tier_definitions

    @classmethod
    def run_ablation_study(
        cls,
        model_factory: Callable[[], MLBaseModel],
        df: pd.DataFrame,
        tier_definitions: Dict[FeatureTier, List[str]],
        target_col: str,
        validator: WalkForwardMLValidator,
        date_col: str = "date",
    ) -> Dict[FeatureTier, TierEvaluationResult]:
        """
        Runs walk-forward validation across all 5 tiers sequentially.
        """
        results: Dict[FeatureTier, TierEvaluationResult] = {}
        tier_a_acc = 0.0

        for tier in [
            FeatureTier.TIER_A_PRICE,
            FeatureTier.TIER_B_PRICE_ACTION,
            FeatureTier.TIER_C_VOLUME,
            FeatureTier.TIER_D_VOLATILITY_REGIME,
            FeatureTier.TIER_E_OPTIONS,
        ]:
            cols = tier_definitions[tier]
            model = model_factory()
            folds = validator.run_walk_forward(
                model=model,
                df=df,
                feature_cols=cols,
                target_col=target_col,
                date_col=date_col,
            )

            if not folds:
                results[tier] = TierEvaluationResult(
                    tier=tier,
                    feature_count=len(cols),
                    feature_names=cols,
                    mean_accuracy=0.0,
                    median_accuracy=0.0,
                    best_accuracy=0.0,
                    worst_accuracy=0.0,
                    mean_f1=0.0,
                    mean_brier=0.0,
                    incremental_accuracy_vs_tier_a=0.0,
                    fold_accuracies=[],
                )
                continue

            accs = [f.fold_accuracy for f in folds]
            f1s = [f.fold_f1 for f in folds]
            briers = [f.fold_brier_score for f in folds]

            mean_acc = float(np.mean(accs))
            median_acc = float(np.median(accs))
            best_acc = float(np.max(accs))
            worst_acc = float(np.min(accs))
            mean_f1 = float(np.mean(f1s))
            mean_brier = float(np.mean(briers))

            if tier == FeatureTier.TIER_A_PRICE:
                tier_a_acc = mean_acc

            inc_acc = mean_acc - tier_a_acc

            results[tier] = TierEvaluationResult(
                tier=tier,
                feature_count=len(cols),
                feature_names=cols,
                mean_accuracy=mean_acc,
                median_accuracy=median_acc,
                best_accuracy=best_acc,
                worst_accuracy=worst_acc,
                mean_f1=mean_f1,
                mean_brier=mean_brier,
                incremental_accuracy_vs_tier_a=inc_acc,
                fold_accuracies=accs,
            )

        return results
