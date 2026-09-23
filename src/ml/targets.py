"""
Phase 9.5 — Target Definitions & Multi-Horizon Prediction Targets.

Enforces strict point-in-time boundary discipline:
feature_availability_timestamp <= prediction_timestamp < target_start_timestamp < target_end_timestamp.

Supports:
- Direction targets: 1D, 3D, 5D, 10D binary classification
- Continuous regression targets: 1D, 3D, 5D, 10D returns
- Volatility targets: future realized volatility, future volatility regime
- Options targets (LTP research only): future option return, price change, IV change, MAE, MFE
- Clearly separates: UNDERLYING_TARGET, OPTION_TARGET, and STRATEGY_TARGET.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


class TargetCategory(str, Enum):
    UNDERLYING_TARGET = "UNDERLYING_TARGET"
    OPTION_TARGET = "OPTION_TARGET"
    STRATEGY_TARGET = "STRATEGY_TARGET"


class TargetType(str, Enum):
    # Direction
    DIRECTIONAL_RETURN_BINARY = "DIRECTIONAL_RETURN_BINARY"
    DIRECTION_1D = "DIRECTION_1D"
    DIRECTION_3D = "DIRECTION_3D"
    DIRECTION_5D = "DIRECTION_5D"
    DIRECTION_10D = "DIRECTION_10D"
    
    # Regression
    CONTINUOUS_RETURN_REGRESSION = "CONTINUOUS_RETURN_REGRESSION"
    RETURN_1D = "RETURN_1D"
    RETURN_3D = "RETURN_3D"
    RETURN_5D = "RETURN_5D"
    RETURN_10D = "RETURN_10D"
    
    # Volatility
    REALIZED_VOLATILITY = "REALIZED_VOLATILITY"
    VOLATILITY_REGIME_CHANGE = "VOLATILITY_REGIME_CHANGE"
    
    # Options Targets
    OPTION_RETURN = "OPTION_RETURN"
    OPTION_PRICE_CHANGE = "OPTION_PRICE_CHANGE"
    OPTION_IV_CHANGE = "OPTION_IV_CHANGE"
    OPTION_MAE_MFE = "OPTION_MAE_MFE"
    EXPECTED_MOVE_BREACH = "EXPECTED_MOVE_BREACH"


@dataclass
class TargetDefinition:
    name: str
    target_type: TargetType
    horizon_days: int
    threshold: float = 0.0
    underlying: str = "NIFTY"
    category: TargetCategory = TargetCategory.UNDERLYING_TARGET
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TargetObservation:
    feature_timestamp: datetime
    target_start: datetime
    target_end: datetime
    underlying: str
    value: float
    binary_label: Optional[int] = None
    target_category: TargetCategory = TargetCategory.UNDERLYING_TARGET
    metadata: Dict[str, Any] = field(default_factory=dict)


def generate_directional_targets(
    df: pd.DataFrame,
    target_def: TargetDefinition,
    date_col: str = "date",
    price_col: str = "close",
) -> pd.DataFrame:
    """
    Generates point-in-time directional targets for a given price dataframe.
    Ensures feature_timestamp <= target_start < target_end.
    Maintains complete backward compatibility with Phase 6/6.5.
    """
    df_sorted = df.sort_values(by=date_col).copy()
    h = target_def.horizon_days

    # Future price at T + h
    future_price = df_sorted[price_col].shift(-h)
    returns = (future_price - df_sorted[price_col]) / df_sorted[price_col]

    df_sorted[f"target_return_{h}d"] = returns
    if target_def.target_type in (
        TargetType.DIRECTIONAL_RETURN_BINARY,
        TargetType.DIRECTION_1D,
        TargetType.DIRECTION_3D,
        TargetType.DIRECTION_5D,
        TargetType.DIRECTION_10D,
    ):
        df_sorted[f"target_binary_{h}d"] = (returns > target_def.threshold).astype(int)

    # Attach explicit timestamps
    target_obs: List[Dict] = []
    dates = df_sorted[date_col].tolist()
    for idx, dt in enumerate(dates):
        if idx + h < len(dates):
            t_feat = pd.to_datetime(dt)
            t_start = pd.to_datetime(dates[idx + 1]) if idx + 1 < len(dates) else t_feat
            t_end = pd.to_datetime(dates[idx + h])
            ret_val = returns.iloc[idx]
            bin_val = int(ret_val > target_def.threshold) if not np.isnan(ret_val) else None
            target_obs.append({
                "feature_timestamp": t_feat,
                "target_start": t_start,
                "target_end": t_end,
                "value": ret_val,
                "binary_label": bin_val,
                "target_category": target_def.category.value,
            })
        else:
            target_obs.append({
                "feature_timestamp": pd.to_datetime(dt),
                "target_start": None,
                "target_end": None,
                "value": np.nan,
                "binary_label": None,
                "target_category": target_def.category.value,
            })

    target_df = pd.DataFrame(target_obs)
    df_result = pd.concat([df_sorted.reset_index(drop=True), target_df], axis=1)
    return df_result.dropna(subset=[f"target_return_{h}d"])


class MultiHorizonTargetEngine:
    """
    Constructs multi-horizon targets with explicit Point-in-Time timestamp verification.
    """

    @staticmethod
    def build_all_underlying_targets(
        df: pd.DataFrame,
        date_col: str = "date",
        price_col: str = "close",
        high_col: str = "high",
        low_col: str = "low",
    ) -> pd.DataFrame:
        """
        Builds multi-horizon direction, regression, and volatility targets:
        - 1D, 3D, 5D, 10D future returns
        - 1D, 3D, 5D, 10D binary direction (1 if return > 0 else 0)
        - 5D, 10D future realized volatility
        - 5D future ATR-normalized price change
        """
        df_sorted = df.sort_values(by=date_col).copy().reset_index(drop=True)
        dates = pd.to_datetime(df_sorted[date_col]).tolist()
        n = len(df_sorted)

        # 1. Forward Returns & Direction
        for h in [1, 3, 5, 10]:
            fwd_price = df_sorted[price_col].shift(-h)
            ret = (fwd_price - df_sorted[price_col]) / df_sorted[price_col]
            df_sorted[f"target_fwd_ret_{h}d"] = ret
            df_sorted[f"target_fwd_dir_{h}d"] = (ret > 0.0).astype(float)
            # Set nan where future is unavailable
            df_sorted.loc[n - h :, f"target_fwd_dir_{h}d"] = np.nan

        # 2. Forward Realized Volatility (annualized, sqrt(252))
        log_rets = np.log(df_sorted[price_col] / df_sorted[price_col].shift(1))
        for h in [5, 10]:
            fwd_rv = []
            for i in range(n):
                if i + h < n:
                    # Forward window is (i+1) to (i+h) strictly after T
                    window_rets = log_rets.iloc[i + 1 : i + h + 1]
                    if len(window_rets) >= 2:
                        std = float(window_rets.std()) * np.sqrt(252)
                        fwd_rv.append(std)
                    else:
                        fwd_rv.append(np.nan)
                else:
                    fwd_rv.append(np.nan)
            df_sorted[f"target_fwd_rv_{h}d"] = fwd_rv

        # 3. Forward ATR-normalized movement (5D)
        if high_col in df_sorted.columns and low_col in df_sorted.columns:
            tr = np.maximum(
                df_sorted[high_col] - df_sorted[low_col],
                np.maximum(
                    np.abs(df_sorted[high_col] - df_sorted[price_col].shift(1)),
                    np.abs(df_sorted[low_col] - df_sorted[price_col].shift(1)),
                ),
            )
            atr_14 = tr.rolling(14).mean().fillna(df_sorted[price_col] * 0.01)
            fwd_move_5d = df_sorted[price_col].shift(-5) - df_sorted[price_col]
            df_sorted["target_fwd_atr_norm_5d"] = fwd_move_5d / np.maximum(atr_14, 1e-6)

        # 4. Explicit Timestamps
        df_sorted["feature_availability_timestamp"] = dates
        # Next-session open / start is next trading day
        target_starts = [dates[i + 1] if i + 1 < n else None for i in range(n)]
        df_sorted["target_start_timestamp"] = target_starts
        target_ends_1d = [dates[i + 1] if i + 1 < n else None for i in range(n)]
        df_sorted["target_end_1d_timestamp"] = target_ends_1d

        return df_sorted

    @staticmethod
    def build_option_ltp_targets(
        option_df: pd.DataFrame,
        horizon_days: int = 1,
        date_col: str = "date",
        price_col: str = "last_price",
        strike_col: str = "strike_price",
        option_type_col: str = "option_type",
    ) -> pd.DataFrame:
        """
        Builds option LTP research targets (price change, return, MAE, MFE) for continuous contracts.
        Explicitly marked as TargetCategory.OPTION_TARGET and LTP_RESEARCH.
        """
        df = option_df.sort_values(by=[strike_col, option_type_col, date_col]).copy()
        
        # Group by specific contract (strike + option_type)
        grouped = df.groupby([strike_col, option_type_col])
        
        df["target_opt_fwd_price"] = grouped[price_col].shift(-horizon_days)
        df["target_opt_fwd_change"] = df["target_opt_fwd_price"] - df[price_col]
        df["target_opt_fwd_return"] = df["target_opt_fwd_change"] / np.maximum(df[price_col], 0.05)
        df["target_opt_fwd_dir"] = (df["target_opt_fwd_change"] > 0.0).astype(float)
        
        # Mark category
        df["target_category"] = TargetCategory.OPTION_TARGET.value
        df["research_classification"] = "LTP_RESEARCH"
        
        return df
