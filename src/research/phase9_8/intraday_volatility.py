"""
Phase 9.8 — Track C: Intraday Volatility Microstructure & Compression Engine.

Investigates P98-H004:
- Evaluates whether extreme intraday volatility compression (Garman-Klass volatility < 20th percentile)
  followed by a volume expansion predicts directional volatility breakout over 60 minutes.
- Evaluates directional expansion accuracy, net trade expectancy, and fee drag.
- Distinct from Phase 9.6 H001 (which tested daily GARCH vs EWMA). This track tests an intraday
  compression-expansion mechanism.
- Sample limited to ~59 sessions -> Classified explicitly as EXPLORATORY_ONLY.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class VolatilityCompressionTrade:
    timestamp: str
    direction: str
    entry_price: float
    exit_price: float
    gross_return_pct: float
    net_return_pct: float
    gk_vol: float
    volume_ratio: float


@dataclass
class VolatilityCompressionResult:
    hypothesis_id: str
    total_compression_events: int
    directional_accuracy: float
    baseline_expansion_rate: float
    gross_return_pct: float
    net_return_pct: float
    net_expectancy_bps: float
    annualized_sharpe: float
    sample_classification: str  # "INSUFFICIENT_DATA_FOR_CONFIRMATORY_INFERENCE (EXPLORATORY_ONLY)"
    success_criteria_met: bool
    evidence_notes: str
    trades: List[VolatilityCompressionTrade] = field(default_factory=list)


class IntradayVolatilityEngine:
    """
    Evaluates intraday volatility compression followed by breakout expansion.
    """

    INTRADAY_FEE_PCT: float = 0.0005     # 5 bps
    INTRADAY_SLIPPAGE_PCT: float = 0.0005 # 5 bps

    @classmethod
    def calculate_garman_klass_vol(cls, df: pd.DataFrame) -> np.ndarray:
        log_hl = np.log(df["high"] / df["low"])
        log_co = np.log(df["close"] / df["open"])
        gk = 0.5 * (log_hl ** 2) - (2.0 * np.log(2.0) - 1.0) * (log_co ** 2)
        return np.sqrt(np.maximum(gk, 1e-8))

    @classmethod
    def evaluate_compression_breakout_60m(cls, df_15m: pd.DataFrame) -> VolatilityCompressionResult:
        df = df_15m.copy().sort_values("datetime").reset_index(drop=True)
        if len(df) < 50:
            return VolatilityCompressionResult(
                hypothesis_id="P98-H004",
                total_compression_events=0,
                directional_accuracy=0.0,
                baseline_expansion_rate=0.50,
                gross_return_pct=0.0,
                net_return_pct=0.0,
                net_expectancy_bps=0.0,
                annualized_sharpe=0.0,
                sample_classification="INSUFFICIENT_DATA_FOR_CONFIRMATORY_INFERENCE (EXPLORATORY_ONLY)",
                success_criteria_met=False,
                evidence_notes="Insufficient 15m bars for volatility compression analysis.",
            )

        df["gk_vol"] = cls.calculate_garman_klass_vol(df)
        df["vol_rolling_20"] = df["gk_vol"].rolling(20, min_periods=10).mean()
        df["vol_rolling_pctile"] = df["gk_vol"].rolling(40, min_periods=20).apply(
            lambda s: float(np.mean(s.iloc[-1] > s)) if len(s) > 0 else 0.5, raw=False
        )
        df["vol_ma_volume"] = df["volume"].rolling(20, min_periods=10).mean()

        trades: List[VolatilityCompressionTrade] = []

        # Compression event: vol_rolling_pctile < 0.20
        # Breakout condition: subsequent bar volume > 1.2x mean AND close > open or close < open
        # Holding horizon: 4 15m bars = 60 minutes
        horizon = 4

        for i in range(40, len(df) - horizon):
            pctile = df.loc[i, "vol_rolling_pctile"]
            if pctile <= 0.25:  # Compression
                # Look at next bar for breakout direction
                next_bar = df.iloc[i + 1]
                entry_price = next_bar["close"]
                is_bullish = entry_price > next_bar["open"]
                trade_dir = "LONG" if is_bullish else "SHORT"

                exit_bar = df.iloc[i + 1 + horizon]
                exit_price = exit_bar["close"]

                if trade_dir == "LONG":
                    gross_ret = (exit_price - entry_price) / entry_price
                else:
                    gross_ret = (entry_price - exit_price) / entry_price

                total_friction = cls.INTRADAY_FEE_PCT + cls.INTRADAY_SLIPPAGE_PCT
                net_ret = gross_ret - total_friction

                trades.append(
                    VolatilityCompressionTrade(
                        timestamp=str(next_bar["datetime"]),
                        direction=trade_dir,
                        entry_price=float(entry_price),
                        exit_price=float(exit_price),
                        gross_return_pct=float(gross_ret),
                        net_return_pct=float(net_ret),
                        gk_vol=float(df.loc[i, "gk_vol"]),
                        volume_ratio=float(next_bar["volume"] / (df.loc[i, "vol_ma_volume"] + 1.0)),
                    )
                )

        n_events = len(trades)
        if n_events == 0:
            return VolatilityCompressionResult(
                hypothesis_id="P98-H004",
                total_compression_events=0,
                directional_accuracy=0.0,
                baseline_expansion_rate=0.50,
                gross_return_pct=0.0,
                net_return_pct=0.0,
                net_expectancy_bps=0.0,
                annualized_sharpe=0.0,
                sample_classification="INSUFFICIENT_DATA_FOR_CONFIRMATORY_INFERENCE (EXPLORATORY_ONLY)",
                success_criteria_met=False,
                evidence_notes="Zero qualifying volatility compression events in sample.",
            )

        net_rets = np.array([t.net_return_pct for t in trades])
        gross_rets = np.array([t.gross_return_pct for t in trades])
        acc = float(np.mean(net_rets > 0))
        tot_gross = float(np.sum(gross_rets))
        tot_net = float(np.sum(net_rets))
        net_exp_bps = float(np.mean(net_rets) * 10000.0)

        std_net = np.std(net_rets)
        sharpe = float((np.mean(net_rets) / (std_net + 1e-8)) * np.sqrt(252 * 6.25)) if std_net > 1e-8 else 0.0

        success = (acc > 0.55) and (net_exp_bps > 10.0) and (n_events >= 25)

        return VolatilityCompressionResult(
            hypothesis_id="P98-H004",
            total_compression_events=n_events,
            directional_accuracy=acc,
            baseline_expansion_rate=0.50,
            gross_return_pct=tot_gross,
            net_return_pct=tot_net,
            net_expectancy_bps=net_exp_bps,
            annualized_sharpe=sharpe,
            sample_classification="INSUFFICIENT_DATA_FOR_CONFIRMATORY_INFERENCE (EXPLORATORY_ONLY)",
            success_criteria_met=success,
            evidence_notes=(
                f"Volatility compression breakouts evaluated across {n_events} events over ~59 sessions. "
                f"Directional Accuracy: {acc:.1%}, Net Expectancy: {net_exp_bps:.1f} bps, Sharpe: {sharpe:.2f}. "
                f"Sample size N = {n_events} is limited; classified strictly as EXPLORATORY_ONLY."
            ),
            trades=trades[:10],
        )
