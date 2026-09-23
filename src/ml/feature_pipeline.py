"""
Feature Engine Pipeline for ML Predictive Modeling Engine.
Extracts leakage-free, point-in-time features from technical, volatility, option chain, and regime data.
"""

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.features.market_regime import MarketRegimeEngine
from src.features.price_action import PriceActionEngine
from src.features.technical import compute_technical_features_df
from src.features.volatility import calculate_realized_volatility


@dataclass
class FeatureSetMetadata:
    feature_version: str
    dataset_hash: str
    feature_names: List[str] = field(default_factory=list)


class MLFeaturePipeline:
    """
    Leakage-Free Feature Engineering Pipeline.
    Calculates features strictly using data available on or before observation date T.
    """

    def __init__(self, feature_version: str = "v1.0"):
        self.feature_version = feature_version
        self.regime_engine = MarketRegimeEngine()

    def build_feature_matrix(
        self,
        equity_df: pd.DataFrame,
        option_quotes_df: Optional[pd.DataFrame] = None,
        symbol: str = "NIFTY",
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Constructs a complete point-in-time feature matrix from daily equity prices and option quotes.
        """
        df = equity_df.sort_values(by="date").copy()
        if len(df) < 5:
            return pd.DataFrame(), []

        # 1. Technical & Price Features
        df["ret_1d"] = df["close"].pct_change(1)
        df["ret_3d"] = df["close"].pct_change(3)
        df["ret_5d"] = df["close"].pct_change(5)
        df["vol_change_1d"] = df["volume"].pct_change(1)

        # 2. Moving Averages & Volatility
        df["sma_5"] = df["close"].rolling(5).mean()
        df["sma_20"] = df["close"].rolling(20).mean()
        df["dist_sma_20"] = (df["close"] - df["sma_20"]) / df["sma_20"]

        # Realized volatility (rolling 5d & 10d)
        log_rets = np.log(df["close"] / df["close"].shift(1))
        df["rv_5d"] = log_rets.rolling(5).std() * np.sqrt(252)
        df["rv_10d"] = log_rets.rolling(10).std() * np.sqrt(252)

        # 3. High-Low Price Action
        df["high_low_ratio"] = (df["high"] - df["low"]) / df["close"]
        df["close_to_high"] = (df["high"] - df["close"]) / (df["high"] - df["low"] + 1e-6)

        # 4. Market Regime Feature Mapping
        regimes = []
        for idx in range(len(df)):
            sub_df = df.iloc[: idx + 1]  # Strict PIT window
            if len(sub_df) >= 5:
                reg = self.regime_engine.evaluate_regime(sub_df, symbol=symbol)
                regimes.append(reg.regime.value)
            else:
                regimes.append("UNKNOWN")
        df["market_regime"] = regimes

        # Encode regime as numeric code
        regime_map = {
            "STRONG_BULL": 2,
            "BULL": 1,
            "SIDEWAYS": 0,
            "BEAR": -1,
            "STRONG_BEAR": -2,
            "HIGH_VOLATILITY": 3,
            "UNKNOWN": 0,
        }
        df["regime_code"] = df["market_regime"].map(regime_map).fillna(0)

        # 5. Options Aggregate Features (if option quotes provided)
        if option_quotes_df is not None and not option_quotes_df.empty:
            opt_df = option_quotes_df.copy()
            opt_df["date"] = pd.to_datetime(opt_df["timestamp"]).dt.date
            df["date_val"] = pd.to_datetime(df["date"]).dt.date

            # Daily aggregated options volume & OI
            agg_opt = (
                opt_df.groupby("date")
                .agg(
                    total_opt_volume=("volume", "sum"),
                    total_opt_oi=("open_interest", "sum"),
                    avg_opt_price=("last_price", "mean"),
                )
                .reset_index()
            )
            df = df.merge(agg_opt, left_on="date_val", right_on="date", how="left")
            df["total_opt_volume"] = df["total_opt_volume"].fillna(0)
            df["total_opt_oi"] = df["total_opt_oi"].fillna(0)
            df.drop(columns=["date_val"], inplace=True)
        else:
            df["total_opt_volume"] = 0
            df["total_opt_oi"] = 0

        # Define feature names
        feature_cols = [
            "ret_1d",
            "ret_3d",
            "ret_5d",
            "vol_change_1d",
            "dist_sma_20",
            "rv_5d",
            "rv_10d",
            "high_low_ratio",
            "close_to_high",
            "regime_code",
            "total_opt_volume",
            "total_opt_oi",
        ]

        # Fill NaN values using backward look only (forward fill then zero fill)
        df[feature_cols] = df[feature_cols].ffill().fillna(0.0)

        return df, feature_cols

    @staticmethod
    def compute_dataset_hash(df: pd.DataFrame) -> str:
        """Computes deterministic MD5 hash of feature dataset."""
        content = pd.util.hash_pandas_object(df, index=True).values.tobytes()
        return hashlib.md5(content).hexdigest()[:12]
