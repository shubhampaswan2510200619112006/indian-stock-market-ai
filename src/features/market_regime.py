"""
Market Regime Classification Engine.

CRITICAL DESIGN REQUIREMENTS:
1. Multi-signal engine: Uses NIFTY, BANK NIFTY, MA structures, ADX, Realized Vol,
   India VIX, and drawdowns.
2. Returns MarketRegimeResult with:
   - regime
   - confidence
   - supporting_evidence
   - conflicting_evidence
   - invalidation_conditions
   - timestamp
   - data_quality
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd

from src.features.technical import compute_technical_features_df
from src.ingestion.schemas import (
    DataQualityStatus,
    MarketRegimeResult,
    MarketRegimeType,
    TimeFrame,
)


class MarketRegimeEngine:
    """
    Multi-signal market regime classifier.
    Combines trend structure, momentum, volatility, drawdowns, and VIX.
    """

    def evaluate_regime(
        self,
        nifty_df: pd.DataFrame,
        banknifty_df: Optional[pd.DataFrame] = None,
        vix_value: Optional[float] = None,
        symbol: str = "NIFTY",
    ) -> MarketRegimeResult:
        """
        Evaluates current market regime using multi-signal evidence.
        """
        if nifty_df is None or len(nifty_df) < 20:
            return MarketRegimeResult(
                symbol=symbol,
                timestamp=datetime.now(),
                source="market_regime_engine",
                data_quality=DataQualityStatus.UNAVAILABLE,
                regime=MarketRegimeType.UNKNOWN,
                confidence=0.0,
                supporting_evidence=["Insufficient price history (< 20 bars) for regime assessment."],
                conflicting_evidence=[],
                invalidation_conditions=["Provide at least 20 daily bars of underlying history."],
                vix_value=vix_value,
            )

        nifty_feat = compute_technical_features_df(nifty_df, symbol="NIFTY", timeframe=TimeFrame.DAILY)
        latest = nifty_feat.iloc[-1]
        timestamp = latest["timestamp"].to_pydatetime() if isinstance(latest["timestamp"], pd.Timestamp) else latest["timestamp"]

        close = float(latest["close"])
        sma_20 = float(latest["sma_20"]) if not pd.isna(latest.get("sma_20")) else None
        sma_50 = float(latest["sma_50"]) if not pd.isna(latest.get("sma_50")) else None
        sma_200 = float(latest["sma_200"]) if not pd.isna(latest.get("sma_200")) else None
        adx_14 = float(latest["adx_14"]) if not pd.isna(latest.get("adx_14")) else None
        rsi_14 = float(latest["rsi_14"]) if not pd.isna(latest.get("rsi_14")) else None
        rv_20d = float(latest["realized_vol_20d"]) if not pd.isna(latest.get("realized_vol_20d")) else None

        # Calculate drawdown from recent 60-bar high
        peak_60 = float(nifty_df["high"].tail(60).max())
        drawdown_pct = float((close - peak_60) / peak_60) * 100.0

        # BANK NIFTY trend assessment if available
        banknifty_trend = None
        if banknifty_df is not None and len(banknifty_df) >= 20:
            bn_feat = compute_technical_features_df(banknifty_df, symbol="BANKNIFTY", timeframe=TimeFrame.DAILY)
            bn_latest = bn_feat.iloc[-1]
            bn_close = float(bn_latest["close"])
            bn_sma20 = float(bn_latest["sma_20"]) if not pd.isna(bn_latest.get("sma_20")) else None
            if bn_sma20:
                banknifty_trend = "BULLISH" if bn_close > bn_sma20 else "BEARISH"

        supporting: list[str] = []
        conflicting: list[str] = []
        invalidation: list[str] = []

        bull_score = 0
        bear_score = 0
        total_signals = 0

        # Signal 1: Price vs SMA 20
        if sma_20:
            total_signals += 1
            diff_pct = (close - sma_20) / sma_20 * 100.0
            if close > sma_20:
                bull_score += 1
                supporting.append(f"Price ({close:.2f}) is trading above 20D SMA ({sma_20:.2f}) by +{diff_pct:.2f}%.")
            else:
                bear_score += 1
                conflicting.append(f"Price ({close:.2f}) is trading below 20D SMA ({sma_20:.2f}) by {diff_pct:.2f}%.")

        # Signal 2: Price vs SMA 50
        if sma_50:
            total_signals += 1
            diff_pct = (close - sma_50) / sma_50 * 100.0
            if close > sma_50:
                bull_score += 1
                supporting.append(f"Price is trading above 50D SMA ({sma_50:.2f}) by +{diff_pct:.2f}%.")
            else:
                bear_score += 1
                conflicting.append(f"Price is trading below 50D SMA ({sma_50:.2f}) by {diff_pct:.2f}%.")

        # Signal 3: Price vs SMA 200
        if sma_200:
            total_signals += 1
            diff_pct = (close - sma_200) / sma_200 * 100.0
            if close > sma_200:
                bull_score += 1
                supporting.append(f"Long-term structure: Price is above 200D SMA ({sma_200:.2f}) by +{diff_pct:.2f}%.")
            else:
                bear_score += 1
                conflicting.append(f"Long-term structure: Price is below 200D SMA ({sma_200:.2f}) by {diff_pct:.2f}%.")

        # Signal 4: RSI Momentum
        if rsi_14:
            total_signals += 1
            if rsi_14 > 55:
                bull_score += 1
                supporting.append(f"14-period RSI is in bullish regime ({rsi_14:.1f} > 55).")
            elif rsi_14 < 45:
                bear_score += 1
                conflicting.append(f"14-period RSI is in bearish regime ({rsi_14:.1f} < 45).")
            else:
                supporting.append(f"RSI is neutral at {rsi_14:.1f}.")

        # Signal 5: ADX Trend Strength
        if adx_14:
            if adx_14 >= 25:
                supporting.append(f"ADX confirms strong trend presence ({adx_14:.1f} >= 25).")
            else:
                conflicting.append(f"ADX indicates weak trend / consolidation ({adx_14:.1f} < 25).")

        # Signal 6: BANK NIFTY confirmation
        if banknifty_trend:
            total_signals += 1
            if banknifty_trend == "BULLISH":
                bull_score += 1
                supporting.append("BANK NIFTY inter-market confirmation is BULLISH.")
            else:
                bear_score += 1
                conflicting.append("BANK NIFTY inter-market divergence is BEARISH.")

        # Signal 7: Drawdown
        if drawdown_pct < -8.0:
            bear_score += 2
            conflicting.append(f"Significant drawdown from 60D peak: {drawdown_pct:.1f}%.")

        # Signal 8: India VIX / High Volatility Check
        is_high_vol = False
        if vix_value is not None:
            if vix_value >= 22.0:
                is_high_vol = True
                conflicting.append(f"India VIX elevated at {vix_value:.1f} (High Volatility Environment).")
            else:
                supporting.append(f"India VIX normal at {vix_value:.1f}.")
        elif rv_20d is not None and rv_20d >= 0.28:
            is_high_vol = True
            conflicting.append(f"20D Realized Volatility high at {rv_20d*100:.1f}%.")

        # Determine Regime Classification
        net_score = bull_score - bear_score
        max_possible = max(total_signals, 1)

        if is_high_vol and (abs(net_score) <= 3 or (vix_value and vix_value >= 25.0)):
            regime = MarketRegimeType.HIGH_VOLATILITY
            confidence = min(0.85, 0.50 + ((vix_value or 22.0) / 100.0))
            invalidation.append("India VIX dropping below 20.0 or 20D Realized Vol falling below 20%.")
        elif net_score >= 4:
            regime = MarketRegimeType.STRONG_BULL
            confidence = min(0.95, 0.60 + (net_score / (max_possible * 2)))
            invalidation.append(f"Price breaking below 20D SMA ({sma_20:.2f} if present).")
            invalidation.append("ADX dropping below 20.")
        elif net_score >= 1:
            regime = MarketRegimeType.BULL
            confidence = min(0.80, 0.50 + (net_score / (max_possible * 2)))
            invalidation.append("Price falling below 50D SMA.")
        elif net_score <= -4:
            regime = MarketRegimeType.STRONG_BEAR
            confidence = min(0.95, 0.60 + (abs(net_score) / (max_possible * 2)))
            invalidation.append(f"Price reclaiming 20D SMA ({sma_20:.2f} if present).")
        elif net_score <= -1:
            regime = MarketRegimeType.BEAR
            confidence = min(0.80, 0.50 + (abs(net_score) / (max_possible * 2)))
            invalidation.append("Price breaking back above 50D SMA.")
        else:
            regime = MarketRegimeType.SIDEWAYS
            confidence = 0.65
            invalidation.append(f"Breakout above 20D high or breakdown below 20D low.")


        nifty_trend_str = "BULLISH" if bull_score > bear_score else ("BEARISH" if bear_score > bull_score else "SIDEWAYS")

        return MarketRegimeResult(
            symbol=symbol,
            timestamp=timestamp,
            source="market_regime_engine",
            data_quality=DataQualityStatus.GOOD,
            regime=regime,
            confidence=round(confidence, 2),
            supporting_evidence=supporting,
            conflicting_evidence=conflicting,
            invalidation_conditions=invalidation,
            vix_value=vix_value,
            nifty_trend=nifty_trend_str,
            banknifty_trend=banknifty_trend,
            breadth_ratio=round(bull_score / max_possible, 2) if max_possible > 0 else None,
        )
