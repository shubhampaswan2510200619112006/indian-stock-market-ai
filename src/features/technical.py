"""
Technical analysis calculation engine.

CRITICAL DESIGN PRINCIPLES:
1. Probabilistic Interpretation: Indicators are features/evidence, NEVER deterministic buy/sell signals.
2. Time-series Safety: For any timestamp T, calculations strictly use data <= T. Zero future leakage.
3. Clean Handling of Missing Bars / NaNs: Early rows before lookback window return None/NaN cleanly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from src.ingestion.schemas import DataQualityStatus, TechnicalFeatures, TimeFrame


def calculate_sma(series: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=window, min_periods=window).mean()


def calculate_ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=span, adjust=False).mean()


def calculate_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder's smoothing)."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    # Wilder's smoothing
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi = rsi.fillna(50.0)  # Default neutral RSI if loss is 0
    return rsi


def calculate_macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """MACD Line, Signal Line, and Histogram."""
    ema_fast = calculate_ema(close, span=fast)
    ema_slow = calculate_ema(close, span=slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, span=signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def calculate_atr(
    high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14
) -> pd.Series:
    """Average True Range (ATR)."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()


def calculate_adx(
    high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14
) -> pd.Series:
    """Average Directional Index (ADX)."""
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr = calculate_atr(high, low, close, window=1)  # 1-period TR
    tr_smoothed = pd.Series(tr).ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    plus_di = 100.0 * pd.Series(plus_dm, index=high.index).ewm(
        alpha=1 / window, min_periods=window, adjust=False
    ).mean() / tr_smoothed.replace(0, np.nan)

    minus_di = 100.0 * pd.Series(minus_dm, index=high.index).ewm(
        alpha=1 / window, min_periods=window, adjust=False
    ).mean() / tr_smoothed.replace(0, np.nan)

    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan) * 100.0
    adx = dx.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    return adx.fillna(0.0)


def calculate_bollinger_bands(
    close: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands (Upper, Middle, Lower)."""
    middle = calculate_sma(close, window=window)
    std = close.rolling(window=window, min_periods=window).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    return upper, middle, lower


def compute_technical_features_df(
    df: pd.DataFrame, symbol: str, timeframe: TimeFrame = TimeFrame.DAILY
) -> pd.DataFrame:
    """
    Computes all technical features on an OHLCV DataFrame in a timestamp-safe manner.
    Expects df columns: ['date' or 'timestamp', 'open', 'high', 'low', 'close', 'volume'].
    """
    df = df.copy()
    df["timeframe"] = timeframe.value if isinstance(timeframe, TimeFrame) else timeframe
    if "date" in df.columns:
        df["timestamp"] = pd.to_datetime(df["date"])
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # Moving averages
    df["sma_20"] = calculate_sma(close, 20)
    df["sma_50"] = calculate_sma(close, 50)
    df["sma_200"] = calculate_sma(close, 200)
    df["ema_12"] = calculate_ema(close, 12)
    df["ema_26"] = calculate_ema(close, 26)

    # Momentum / Oscillators
    df["rsi_14"] = calculate_rsi(close, 14)
    macd_line, macd_sig, macd_h = calculate_macd(close, 12, 26, 9)
    df["macd"] = macd_line
    df["macd_signal"] = macd_sig
    df["macd_hist"] = macd_h

    # Volatility / Range
    df["atr_14"] = calculate_atr(high, low, close, 14)
    df["adx_14"] = calculate_adx(high, low, close, 14)
    bb_u, bb_m, bb_l = calculate_bollinger_bands(close, 20, 2.0)
    df["bb_upper"] = bb_u
    df["bb_middle"] = bb_m
    df["bb_lower"] = bb_l

    # Returns
    df["returns_1d"] = close.pct_change(1)
    df["returns_5d"] = close.pct_change(5)
    df["returns_20d"] = close.pct_change(20)

    # Moving Average Relatives
    df["price_to_sma20"] = close / df["sma_20"] - 1.0
    df["price_to_sma50"] = close / df["sma_50"] - 1.0
    df["price_to_sma200"] = close / df["sma_200"] - 1.0

    # Trend Strength (Composite: ADX + MA Alignment)
    ma_aligned = (
        (close > df["sma_20"]).astype(int)
        + (df["sma_20"] > df["sma_50"]).astype(int)
        + (df["sma_50"] > df["sma_200"]).astype(int)
    )
    df["trend_strength"] = (df["adx_14"].clip(0, 50) * 1.2) + (ma_aligned * 13.3)
    df["trend_strength"] = df["trend_strength"].clip(0, 100)

    # Momentum (Rate of change over 10 bars)
    df["momentum"] = close.pct_change(10) * 100.0

    # Realized Volatility (Annualized log returns std dev * sqrt(252))
    log_ret = np.log(close / close.shift(1))
    df["realized_vol_5d"] = log_ret.rolling(5, min_periods=3).std() * np.sqrt(252)
    df["realized_vol_10d"] = log_ret.rolling(10, min_periods=5).std() * np.sqrt(252)
    df["realized_vol_20d"] = log_ret.rolling(20, min_periods=10).std() * np.sqrt(252)
    df["realized_vol_30d"] = log_ret.rolling(30, min_periods=15).std() * np.sqrt(252)
    df["realized_vol_60d"] = log_ret.rolling(60, min_periods=30).std() * np.sqrt(252)

    # Volume features
    vol_sma_5 = volume.rolling(5, min_periods=3).mean()
    vol_sma_20 = volume.rolling(20, min_periods=5).mean()
    df["volume_ratio_5d"] = volume / vol_sma_5.replace(0, np.nan)
    df["volume_ratio_20d"] = volume / vol_sma_20.replace(0, np.nan)

    return df


def extract_latest_features(
    df: pd.DataFrame, symbol: str, timeframe: TimeFrame = TimeFrame.DAILY
) -> TechnicalFeatures:
    """Extracts the latest row of computed features into a Pydantic TechnicalFeatures model."""
    df_feat = compute_technical_features_df(df, symbol, timeframe)
    latest = df_feat.iloc[-1]

    def _val(val):
        if pd.isna(val):
            return None
        return float(val)

    return TechnicalFeatures(
        timestamp=latest["timestamp"].to_pydatetime() if isinstance(latest["timestamp"], pd.Timestamp) else latest["timestamp"],
        source="technical_engine",
        data_quality=DataQualityStatus.GOOD,
        symbol=symbol,
        timeframe=timeframe,
        close=float(latest["close"]),
        sma_20=_val(latest.get("sma_20")),
        sma_50=_val(latest.get("sma_50")),
        sma_200=_val(latest.get("sma_200")),
        ema_12=_val(latest.get("ema_12")),
        ema_26=_val(latest.get("ema_26")),
        rsi_14=_val(latest.get("rsi_14")),
        macd=_val(latest.get("macd")),
        macd_signal=_val(latest.get("macd_signal")),
        macd_hist=_val(latest.get("macd_hist")),
        atr_14=_val(latest.get("atr_14")),
        adx_14=_val(latest.get("adx_14")),
        bb_upper=_val(latest.get("bb_upper")),
        bb_middle=_val(latest.get("bb_middle")),
        bb_lower=_val(latest.get("bb_lower")),
        returns_1d=_val(latest.get("returns_1d")),
        returns_5d=_val(latest.get("returns_5d")),
        returns_20d=_val(latest.get("returns_20d")),
        price_to_sma20=_val(latest.get("price_to_sma20")),
        price_to_sma50=_val(latest.get("price_to_sma50")),
        price_to_sma200=_val(latest.get("price_to_sma200")),
        trend_strength=_val(latest.get("trend_strength")),
        momentum=_val(latest.get("momentum")),
        realized_vol_5d=_val(latest.get("realized_vol_5d")),
        realized_vol_10d=_val(latest.get("realized_vol_10d")),
        realized_vol_20d=_val(latest.get("realized_vol_20d")),
        realized_vol_30d=_val(latest.get("realized_vol_30d")),
        realized_vol_60d=_val(latest.get("realized_vol_60d")),
        volume=int(latest["volume"]) if not pd.isna(latest.get("volume")) else None,
        volume_ratio_5d=_val(latest.get("volume_ratio_5d")),
        volume_ratio_20d=_val(latest.get("volume_ratio_20d")),
        patterns=[],  # Will be populated by price_action engine
    )
