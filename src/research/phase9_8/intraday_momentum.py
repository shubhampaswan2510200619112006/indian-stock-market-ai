"""
Phase 9.8 — Track B: Short-Horizon Intraday Momentum vs Reversal Engine.

Investigates P98-H003:
- Tests whether 30-minute intraday return momentum predicts next-30-minute return continuation.
- Uses rolling 30-minute windows resampled from 5-minute/15-minute bars.
- Compares simple sign-momentum against an AR(1) autoregressive statistical baseline.
- Evaluates directional accuracy, gross return, statutory fees, slippage, and net return.
- Sample limited to ~59 sessions -> Classified explicitly as EXPLORATORY_ONLY.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class MomentumEvaluationResult:
    hypothesis_id: str
    total_bars_evaluated: int
    directional_accuracy: float
    baseline_accuracy: float  # AR(1) or Random Walk 50%
    incremental_accuracy_delta: float
    gross_return_pct: float
    total_fees_pct: float
    total_slippage_pct: float
    net_return_pct: float
    annualized_sharpe: float
    net_expectancy_bps: float
    sample_classification: str  # "INSUFFICIENT_DATA_FOR_CONFIRMATORY_INFERENCE (EXPLORATORY_ONLY)"
    success_criteria_met: bool
    evidence_notes: str


class IntradayMomentumEngine:
    """
    Evaluates short-horizon (30-minute) momentum vs mean-reversion.
    """

    INTRADAY_FEE_PCT: float = 0.0005     # 5 bps
    INTRADAY_SLIPPAGE_PCT: float = 0.0005 # 5 bps

    @classmethod
    def evaluate_momentum_30m(cls, df_5m: pd.DataFrame) -> MomentumEvaluationResult:
        """
        Resamples 5m bars to 30m bars and evaluates momentum continuation.
        """
        df = df_5m.copy()
        df = df.set_index("datetime")
        # Resample to 30m
        resampled = df.resample("30min").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna().reset_index()

        # Compute return
        resampled["ret_30m"] = resampled["close"].pct_change()
        resampled["fwd_ret_30m"] = resampled["ret_30m"].shift(-1)
        clean = resampled.dropna().copy()

        n_bars = len(clean)
        if n_bars < 20:
            return MomentumEvaluationResult(
                hypothesis_id="P98-H003",
                total_bars_evaluated=n_bars,
                directional_accuracy=0.0,
                baseline_accuracy=0.50,
                incremental_accuracy_delta=0.0,
                gross_return_pct=0.0,
                total_fees_pct=0.0,
                total_slippage_pct=0.0,
                net_return_pct=0.0,
                annualized_sharpe=0.0,
                net_expectancy_bps=0.0,
                sample_classification="INSUFFICIENT_DATA_FOR_CONFIRMATORY_INFERENCE (EXPLORATORY_ONLY)",
                success_criteria_met=False,
                evidence_notes="Insufficient 30m bars for evaluation.",
            )

        past_ret = clean["ret_30m"].values
        fwd_ret = clean["fwd_ret_30m"].values

        # Signal: follow prior 30m return
        signals = np.sign(past_ret)
        signals[signals == 0] = 1.0

        # Accuracy
        actual_dir = np.sign(fwd_ret)
        actual_dir[actual_dir == 0] = 1.0
        acc = float(np.mean(signals == actual_dir))

        # Baseline: AR(1) prediction
        if np.std(past_ret[:-1]) > 1e-8:
            phi = float(np.corrcoef(past_ret[:-1], past_ret[1:])[0, 1])
        else:
            phi = 0.0
        ar1_signals = np.sign(past_ret * phi)
        ar1_signals[ar1_signals == 0] = 1.0
        base_acc = float(np.mean(ar1_signals == actual_dir))

        # Returns
        gross_bar = signals * fwd_ret
        # Position changes
        pos_changes = np.abs(np.diff(signals, prepend=0.0))
        fees = pos_changes * cls.INTRADAY_FEE_PCT
        slip = pos_changes * cls.INTRADAY_SLIPPAGE_PCT
        net_bar = gross_bar - (fees + slip)

        tot_gross = float(np.sum(gross_bar))
        tot_fees = float(np.sum(fees))
        tot_slip = float(np.sum(slip))
        tot_net = float(np.sum(net_bar))
        net_exp_bps = float(np.mean(net_bar) * 10000.0)

        std_net = np.std(net_bar)
        # Annualization: ~13 30m bars per day, 252 days = 3276 bars/year
        bars_per_year = 3276
        sharpe = float((np.mean(net_bar) / (std_net + 1e-8)) * np.sqrt(bars_per_year)) if std_net > 1e-8 else 0.0

        success = (acc > 0.54) and (sharpe > 0.50)

        return MomentumEvaluationResult(
            hypothesis_id="P98-H003",
            total_bars_evaluated=n_bars,
            directional_accuracy=acc,
            baseline_accuracy=base_acc,
            incremental_accuracy_delta=acc - base_acc,
            gross_return_pct=tot_gross,
            total_fees_pct=tot_fees,
            total_slippage_pct=tot_slip,
            net_return_pct=tot_net,
            annualized_sharpe=sharpe,
            net_expectancy_bps=net_exp_bps,
            sample_classification="INSUFFICIENT_DATA_FOR_CONFIRMATORY_INFERENCE (EXPLORATORY_ONLY)",
            success_criteria_met=success,
            evidence_notes=(
                f"30m Intraday Momentum evaluated over {n_bars} bars across ~59 sessions. "
                f"Directional Accuracy: {acc:.1%} (AR(1) Baseline: {base_acc:.1%}). "
                f"Gross: {tot_gross:.1%}, Frictions: {(tot_fees + tot_slip):.1%}, Net: {tot_net:.1%}, Sharpe: {sharpe:.2f}. "
                f"Turnover friction creates substantial drag; classified strictly as EXPLORATORY_ONLY."
            ),
        )
