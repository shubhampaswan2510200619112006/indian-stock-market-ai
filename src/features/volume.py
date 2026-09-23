"""
Volume features and liquidity indicator calculations.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def calculate_volume_ratios(volume: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Computes Volume / 5-day SMA Volume and Volume / 20-day SMA Volume."""
    sma_5 = volume.rolling(5, min_periods=3).mean()
    sma_20 = volume.rolling(20, min_periods=5).mean()

    ratio_5 = volume / sma_5.replace(0, np.nan)
    ratio_20 = volume / sma_20.replace(0, np.nan)

    return ratio_5, ratio_20


def calculate_volume_trend(volume: pd.Series, window: int = 5) -> float | None:
    """Calculates linear slope or percentage change in volume over recent bars."""
    if len(volume) < window:
        return None
    recent = volume.tail(window)
    if recent.iloc[0] == 0:
        return None
    return float((recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0])
