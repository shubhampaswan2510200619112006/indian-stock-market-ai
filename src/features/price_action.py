"""
Price Action Engine.

Detects candlestick patterns and structural price formations.
CRITICAL DESIGN REQUIREMENT:
Every detected pattern MUST carry:
- timestamp
- timeframe
- pattern
- context
- historical_relevance (probabilistic)
- confidence (0.0 to 1.0)
- invalidation_conditions (exact rule when pattern fails)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from src.ingestion.schemas import CandlestickPattern, TimeFrame


class PriceActionEngine:
    """
    Engine to identify price action patterns, swing structures (HH/HL, LH/LL),
    gaps, breakouts, and support/resistance interactions.
    """

    def __init__(self, timeframe: TimeFrame = TimeFrame.DAILY):
        self.timeframe = timeframe

    def detect_patterns(self, df: pd.DataFrame) -> list[CandlestickPattern]:
        """
        Scans OHLCV DataFrame for price action patterns on the latest bars.
        Expects df columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
        Returns list of CandlestickPattern Pydantic models.
        """
        if len(df) < 5:
            return []

        df = df.copy()
        if "date" in df.columns:
            df["timestamp"] = pd.to_datetime(df["date"])
        else:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        patterns: list[CandlestickPattern] = []

        curr = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]

        curr_ts = curr["timestamp"].to_pydatetime() if isinstance(curr["timestamp"], pd.Timestamp) else curr["timestamp"]

        c_open, c_high, c_low, c_close = float(curr["open"]), float(curr["high"]), float(curr["low"]), float(curr["close"])
        p_open, p_high, p_low, p_close = float(prev["open"]), float(prev["high"]), float(prev["low"]), float(prev["close"])

        c_range = c_high - c_low
        c_body = abs(c_close - c_open)

        # 1. Doji
        if c_range > 0 and (c_body / c_range) <= 0.10:
            patterns.append(CandlestickPattern(
                timestamp=curr_ts,
                timeframe=self.timeframe,
                pattern="Doji",
                context=f"Indecision candle near price {c_close:.2f}. Open/Close difference is only {c_body:.2f} pts.",
                historical_relevance="Dojis indicate temporary market equilibrium with potential for continuation or reversal depending on next bar confirmation.",
                confidence=0.60,
                invalidation_conditions=f"Break of candle high ({c_high:.2f}) or low ({c_low:.2f}) with sustained volume.",
            ))

        # 2. Hammer
        lower_shadow = min(c_open, c_close) - c_low
        upper_shadow = c_high - max(c_open, c_close)
        if c_range > 0 and (c_body / c_range) <= 0.35 and (lower_shadow / c_range) >= 0.55 and (upper_shadow / c_range) <= 0.15:
            patterns.append(CandlestickPattern(
                timestamp=curr_ts,
                timeframe=self.timeframe,
                pattern="Hammer",
                context=f"Rejection of lower prices at {c_low:.2f} with strong buying response before close.",
                historical_relevance="Bullish reversal tendency when appearing after a downtrend or near support.",
                confidence=0.70,
                invalidation_conditions=f"Price closing below the hammer's low of {c_low:.2f}.",
            ))

        # 3. Shooting Star
        if c_range > 0 and (c_body / c_range) <= 0.35 and (upper_shadow / c_range) >= 0.55 and (lower_shadow / c_range) <= 0.15:
            patterns.append(CandlestickPattern(
                timestamp=curr_ts,
                timeframe=self.timeframe,
                pattern="Shooting Star",
                context=f"Rejection of higher prices at {c_high:.2f} with selling pressure before close.",
                historical_relevance="Bearish reversal tendency when appearing after an uptrend or near resistance.",
                confidence=0.70,
                invalidation_conditions=f"Price closing above the shooting star's high of {c_high:.2f}.",
            ))

        # 4. Bullish Engulfing
        if p_close < p_open and c_close > c_open and c_open <= p_close and c_close >= p_open:
            patterns.append(CandlestickPattern(
                timestamp=curr_ts,
                timeframe=self.timeframe,
                pattern="Bullish Engulfing",
                context=f"Bullish real body ({c_open:.2f} -> {c_close:.2f}) completely engulfs previous bearish body ({p_open:.2f} -> {p_close:.2f}).",
                historical_relevance="High-probability bullish momentum evidence when supported by above-average volume.",
                confidence=0.75,
                invalidation_conditions=f"Price falling below the engulfing candle low of {c_low:.2f}.",
            ))

        # 5. Bearish Engulfing
        if p_close > p_open and c_close < c_open and c_open >= p_close and c_close <= p_open:
            patterns.append(CandlestickPattern(
                timestamp=curr_ts,
                timeframe=self.timeframe,
                pattern="Bearish Engulfing",
                context=f"Bearish real body ({c_open:.2f} -> {c_close:.2f}) completely engulfs previous bullish body ({p_open:.2f} -> {p_close:.2f}).",
                historical_relevance="High-probability bearish momentum evidence when supported by elevated volume.",
                confidence=0.75,
                invalidation_conditions=f"Price rising above the engulfing candle high of {c_high:.2f}.",
            ))

        # 6. Inside Bar
        if c_high <= p_high and c_low >= p_low:
            patterns.append(CandlestickPattern(
                timestamp=curr_ts,
                timeframe=self.timeframe,
                pattern="Inside Bar",
                context=f"Contraction pattern: Current range ({c_low:.2f} - {c_high:.2f}) fits within mother bar ({p_low:.2f} - {p_high:.2f}).",
                historical_relevance="Indicates volatility compression; precedes explosive expansion breaks.",
                confidence=0.65,
                invalidation_conditions=f"Failure of breakout above {p_high:.2f} or breakdown below {p_low:.2f}.",
            ))

        # 7. Breakout / Breakdown (vs 20-bar High/Low)
        if len(df) >= 20:
            rolling_20_high = float(df["high"].iloc[-21:-1].max())
            rolling_20_low = float(df["low"].iloc[-21:-1].min())

            if c_close > rolling_20_high:
                patterns.append(CandlestickPattern(
                    timestamp=curr_ts,
                    timeframe=self.timeframe,
                    pattern="Breakout",
                    context=f"Close ({c_close:.2f}) cleared 20-bar resistance level of {rolling_20_high:.2f}.",
                    historical_relevance="Strong trend continuation feature if supported by expanding volume.",
                    confidence=0.80,
                    invalidation_conditions=f"Price falling back below breakout level of {rolling_20_high:.2f} (False Breakout).",
                ))
            elif c_close < rolling_20_low:
                patterns.append(CandlestickPattern(
                    timestamp=curr_ts,
                    timeframe=self.timeframe,
                    pattern="Breakdown",
                    context=f"Close ({c_close:.2f}) fell below 20-bar support level of {rolling_20_low:.2f}.",
                    historical_relevance="Bearish momentum continuation signal.",
                    confidence=0.80,
                    invalidation_conditions=f"Price reclaiming breakdown level of {rolling_20_low:.2f} (False Breakdown).",
                ))

        # 8. Higher High / Higher Low Structure (HH/HL)
        if c_high > p_high and c_low > p_low:
            patterns.append(CandlestickPattern(
                timestamp=curr_ts,
                timeframe=self.timeframe,
                pattern="HH/HL",
                context=f"Uptrend structure intact: Higher High ({c_high:.2f} > {p_high:.2f}) and Higher Low ({c_low:.2f} > {p_low:.2f}).",
                historical_relevance="Fundamental building block of a healthy bullish trend.",
                confidence=0.70,
                invalidation_conditions=f"Price dropping below prior low of {p_low:.2f}.",
            ))

        # 9. Lower High / Lower Low Structure (LH/LL)
        if c_high < p_high and c_low < p_low:
            patterns.append(CandlestickPattern(
                timestamp=curr_ts,
                timeframe=self.timeframe,
                pattern="LH/LL",
                context=f"Downtrend structure intact: Lower High ({c_high:.2f} < {p_high:.2f}) and Lower Low ({c_low:.2f} < {p_low:.2f}).",
                historical_relevance="Fundamental building block of an active bearish trend.",
                confidence=0.70,
                invalidation_conditions=f"Price crossing above prior high of {p_high:.2f}.",
            ))

        # 10. Gap Detection
        if c_low > p_high:
            gap_size = c_low - p_high
            gap_pct = (gap_size / p_high) * 100.0
            patterns.append(CandlestickPattern(
                timestamp=curr_ts,
                timeframe=self.timeframe,
                pattern="Gap Up",
                context=f"Bullish gap open of {gap_pct:.2f}% between previous high ({p_high:.2f}) and current low ({c_low:.2f}).",
                historical_relevance="Gaps act as institutional momentum zones and prospective support levels.",
                confidence=0.75,
                invalidation_conditions=f"Gap fill condition: Price closing below {p_high:.2f}.",
            ))
        elif c_high < p_low:
            gap_size = p_low - c_high
            gap_pct = (gap_size / p_low) * 100.0
            patterns.append(CandlestickPattern(
                timestamp=curr_ts,
                timeframe=self.timeframe,
                pattern="Gap Down",
                context=f"Bearish gap open of {gap_pct:.2f}% between previous low ({p_low:.2f}) and current high ({c_high:.2f}).",
                historical_relevance="Bearish momentum zone and potential resistance area.",
                confidence=0.75,
                invalidation_conditions=f"Gap fill condition: Price closing above {p_low:.2f}.",
            ))

        # 11. Support / Resistance Interaction
        if len(df) >= 20:
            swings = df["close"].iloc[-20:]
            res_level = swings.max()
            sup_level = swings.min()

            dist_to_res = abs(c_close - res_level) / res_level
            dist_to_sup = abs(c_close - sup_level) / sup_level

            if dist_to_res <= 0.005:
                patterns.append(CandlestickPattern(
                    timestamp=curr_ts,
                    timeframe=self.timeframe,
                    pattern="Resistance Interaction",
                    context=f"Price ({c_close:.2f}) testing key 20-bar resistance at {res_level:.2f} (within 0.5%).",
                    historical_relevance="Expect elevated volatility; watch for rejection or strong breakout.",
                    confidence=0.65,
                    invalidation_conditions=f"Decisive close above {res_level * 1.005:.2f} confirms breakout.",
                ))
            elif dist_to_sup <= 0.005:
                patterns.append(CandlestickPattern(
                    timestamp=curr_ts,
                    timeframe=self.timeframe,
                    pattern="Support Interaction",
                    context=f"Price ({c_close:.2f}) testing key 20-bar support at {sup_level:.2f} (within 0.5%).",
                    historical_relevance="Expect demand zone reaction or breakdown.",
                    confidence=0.65,
                    invalidation_conditions=f"Decisive close below {sup_level * 0.995:.2f} confirms breakdown.",
                ))

        return patterns

    def scan_all_patterns(self, df: pd.DataFrame, max_bars: int = 50) -> list[dict]:
        """
        Scans across historical candles to detect pattern locations for chart overlays.
        Returns a list of pattern marker records with exact coordinates and directional bias.
        """
        if len(df) < 5:
            return []

        df = df.copy()
        if "date" in df.columns:
            df["timestamp"] = pd.to_datetime(df["date"])
        else:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        start_idx = max(2, len(df) - max_bars)
        results: list[dict] = []

        for i in range(start_idx, len(df)):
            curr = df.iloc[i]
            prev = df.iloc[i - 1]

            ts = curr["timestamp"]
            c_open, c_high, c_low, c_close = float(curr["open"]), float(curr["high"]), float(curr["low"]), float(curr["close"])
            p_open, p_high, p_low, p_close = float(prev["open"]), float(prev["high"]), float(prev["low"]), float(prev["close"])

            c_range = c_high - c_low
            c_body = abs(c_close - c_open)
            if c_range <= 0:
                continue

            lower_shadow = min(c_open, c_close) - c_low
            upper_shadow = c_high - max(c_open, c_close)

            # 1. Hammer (Bullish Reversal)
            if (c_body / c_range) <= 0.35 and (lower_shadow / c_range) >= 0.55 and (upper_shadow / c_range) <= 0.15:
                results.append({
                    "timestamp": ts,
                    "pattern": "Hammer",
                    "type": "BULLISH",
                    "price": c_low,
                    "confidence": 0.70,
                    "marker": "triangle-up",
                    "color": "#10b981",
                    "context": f"Lower shadow rejection at ₹{c_low:,.2f}",
                })

            # 2. Shooting Star (Bearish Reversal)
            elif (c_body / c_range) <= 0.35 and (upper_shadow / c_range) >= 0.55 and (lower_shadow / c_range) <= 0.15:
                results.append({
                    "timestamp": ts,
                    "pattern": "Shooting Star",
                    "type": "BEARISH",
                    "price": c_high,
                    "confidence": 0.70,
                    "marker": "triangle-down",
                    "color": "#ef4444",
                    "context": f"Upper shadow rejection at ₹{c_high:,.2f}",
                })

            # 3. Bullish Engulfing
            elif p_close < p_open and c_close > c_open and c_open <= p_close and c_close >= p_open:
                results.append({
                    "timestamp": ts,
                    "pattern": "Bullish Engulfing",
                    "type": "BULLISH",
                    "price": c_low,
                    "confidence": 0.75,
                    "marker": "triangle-up",
                    "color": "#10b981",
                    "context": f"Bullish body engulfed previous bearish candle ({c_open:.2f} -> {c_close:.2f})",
                })

            # 4. Bearish Engulfing
            elif p_close > p_open and c_close < c_open and c_open >= p_close and c_close <= p_open:
                results.append({
                    "timestamp": ts,
                    "pattern": "Bearish Engulfing",
                    "type": "BEARISH",
                    "price": c_high,
                    "confidence": 0.75,
                    "marker": "triangle-down",
                    "color": "#ef4444",
                    "context": f"Bearish body engulfed previous bullish candle ({c_open:.2f} -> {c_close:.2f})",
                })

            # 5. Doji
            elif (c_body / c_range) <= 0.10:
                results.append({
                    "timestamp": ts,
                    "pattern": "Doji",
                    "type": "NEUTRAL",
                    "price": (c_high + c_low) / 2.0,
                    "confidence": 0.60,
                    "marker": "diamond",
                    "color": "#f59e0b",
                    "context": f"Indecision bar near ₹{c_close:,.2f}",
                })

        return results

    def get_key_levels(self, df: pd.DataFrame) -> dict:
        """
        Extracts key institutional support and resistance levels, recent breakouts,
        and market structure trend.
        """
        if len(df) < 10:
            return {
                "support_20": 0.0,
                "resistance_20": 0.0,
                "market_structure": "INSUFFICIENT_DATA",
                "current_price": 0.0,
            }

        curr_close = float(df["close"].iloc[-1])
        lookback_window = min(20, len(df))
        recent_df = df.iloc[-lookback_window:]

        res_20 = float(recent_df["high"].max())
        sup_20 = float(recent_df["low"].min())

        # Determine structural trend
        if len(df) >= 3:
            c_high = float(df["high"].iloc[-1])
            c_low = float(df["low"].iloc[-1])
            p_high = float(df["high"].iloc[-2])
            p_low = float(df["low"].iloc[-2])

            if c_high > p_high and c_low > p_low:
                structure = "BULLISH (Higher Highs & Higher Lows)"
            elif c_high < p_high and c_low < p_low:
                structure = "BEARISH (Lower Highs & Lower Lows)"
            else:
                structure = "RANGE-BOUND (Consolidation)"
        else:
            structure = "RANGE-BOUND"

        dist_to_res = (res_20 - curr_close)
        dist_to_res_pct = (dist_to_res / curr_close) * 100.0 if curr_close > 0 else 0.0

        dist_to_sup = (curr_close - sup_20)
        dist_to_sup_pct = (dist_to_sup / curr_close) * 100.0 if curr_close > 0 else 0.0

        return {
            "current_price": curr_close,
            "resistance_20": res_20,
            "support_20": sup_20,
            "distance_to_resistance_pts": round(dist_to_res, 2),
            "distance_to_resistance_pct": round(dist_to_res_pct, 2),
            "distance_to_support_pts": round(dist_to_sup, 2),
            "distance_to_support_pct": round(dist_to_sup_pct, 2),
            "market_structure": structure,
        }
