"""
Leakage Prevention & Point-in-Time Temporal Isolation Tests for ML Engine.
"""

from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import pytest

from src.ml.feature_pipeline import MLFeaturePipeline
from src.ml.targets import TargetDefinition, TargetType, generate_directional_targets


def test_future_data_leakage_prevention():
    """
    Verifies that feature vectors calculated at time T depend strictly on prices <= T.
    Mutating future prices (T+1, T+2) MUST NOT alter the feature values at time T.
    """
    dates = pd.date_range("2026-08-01", periods=15, freq="D")
    prices = [100.0 + i * 2.0 for i in range(15)]
    volumes = [1000 + i * 10 for i in range(15)]

    df1 = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": volumes})

    pipeline = MLFeaturePipeline(feature_version="v1.0")
    feat_df1, feature_cols = pipeline.build_feature_matrix(df1, symbol="NIFTY")

    # Capture features at index 5 (T=5)
    t5_features_before = feat_df1.iloc[5][feature_cols].to_dict()

    # Mutate FUTURE prices at T=10..14 drastically
    df2 = df1.copy()
    df2.loc[10:14, "close"] = 9999.0
    df2.loc[10:14, "high"] = 9999.0

    feat_df2, _ = pipeline.build_feature_matrix(df2, symbol="NIFTY")
    t5_features_after = feat_df2.iloc[5][feature_cols].to_dict()

    # Features at T=5 MUST BE IDENTICAL before and after future mutation
    for col in feature_cols:
        assert t5_features_before[col] == pytest.approx(t5_features_after[col]), f"Leakage detected in feature {col} at T=5!"


def test_target_timestamp_isolation():
    """
    Verifies that target_start and target_end timestamps strictly occur AFTER feature_timestamp.
    """
    dates = pd.date_range("2026-08-01", periods=10, freq="D")
    prices = [100.0 + i for i in range(10)]
    df = pd.DataFrame({"date": dates, "open": prices, "high": prices, "low": prices, "close": prices, "volume": 1000})

    target_def = TargetDefinition(
        name="dir_ret_2d",
        target_type=TargetType.DIRECTIONAL_RETURN_BINARY,
        horizon_days=2,
    )

    df_target = generate_directional_targets(df, target_def, date_col="date", price_col="close")

    for idx, row in df_target.iterrows():
        t_feat = row["feature_timestamp"]
        t_start = row["target_start"]
        t_end = row["target_end"]

        assert t_feat <= t_start, f"Feature timestamp {t_feat} is after target start {t_start}!"
        assert t_start <= t_end, f"Target start {t_start} is after target end {t_end}!"
