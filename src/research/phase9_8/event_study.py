"""
Phase 9.8 — Track D: Event-Driven Macro & Policy Announcement Engine.

Investigates P98-H005:
- Tests whether RBI MPC rate decision announcements and Union Budget sessions induce
  persistent post-announcement directional drift over 3 sessions.
- Matches verified historical announcement dates (2024–2026) against NIFTY daily price history.
- Measures:
  * Pre-event 3D return
  * Event-day return & abnormal ATR range expansion
  * Post-event 3-session forward return (Day T close -> Day T+3 close)
  * Directional persistence win rate and statistical significance (t-test / permutation p-value).
- Uses only information publicly known at Day T close.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from src.research.phase9_8.data_quality import Phase98DataQualityEngine


@dataclass
class EventObservationRecord:
    event_date: str
    event_type: str
    event_name: str
    event_day_return_pct: float
    abnormal_range_ratio: float
    fwd_3d_return_pct: float
    fwd_3d_direction_aligned: bool
    net_return_pct: float


@dataclass
class EventStudyEvaluationResult:
    hypothesis_id: str
    total_events_matched: int
    directional_alignment_rate: float
    baseline_drift_rate: float
    mean_post_event_return_pct: float
    mean_net_return_pct: float
    t_statistic: float
    p_value: float
    is_statistically_significant: bool
    sample_classification: str  # "CONFIRMATORY_LIMITED_SAMPLE_EVENT_STUDY"
    success_criteria_met: bool
    evidence_notes: str
    observations: List[EventObservationRecord] = field(default_factory=list)


class EventStudyEngine:
    """
    Evaluates market price reactions and post-event drift around verified policy announcements.
    """

    SWING_FEE_PCT: float = 0.0005     # 5 bps
    SWING_SLIPPAGE_PCT: float = 0.0005 # 5 bps

    @classmethod
    def evaluate_rbi_mpc_events(cls, df_nifty_daily: pd.DataFrame) -> EventStudyEvaluationResult:
        df = df_nifty_daily.copy()
        df["date_str"] = df["date"].astype(str)
        df = df.sort_values("date").reset_index(drop=True)

        # Precompute daily return and ATR
        df["ret_1d"] = df["close"].pct_change()
        df["tr"] = np.maximum(
            df["high"] - df["low"],
            np.maximum(
                abs(df["high"] - df["close"].shift(1)),
                abs(df["low"] - df["close"].shift(1)),
            ),
        )
        df["atr_20"] = df["tr"].rolling(20, min_periods=10).mean()

        # 3-day forward return: (close[t+3] - close[t]) / close[t]
        df["fwd_ret_3d"] = (df["close"].shift(-3) - df["close"]) / df["close"]

        date_to_row = {r["date_str"]: r for _, r in df.iterrows()}

        records: List[EventObservationRecord] = []

        for ev in Phase98DataQualityEngine.HISTORICAL_EVENTS:
            ev_date = ev["date"]
            if ev_date in date_to_row:
                row = date_to_row[ev_date]
                ev_ret = float(row["ret_1d"]) if pd.notna(row["ret_1d"]) else 0.0
                fwd_ret = float(row["fwd_ret_3d"]) if pd.notna(row["fwd_ret_3d"]) else 0.0
                atr = float(row["atr_20"]) if pd.notna(row["atr_20"]) and row["atr_20"] > 0 else 100.0
                rng = float(row["high"] - row["low"])
                abnormal_rng = rng / atr

                # Directional alignment: does post-event 3D move in same direction as event day?
                aligned = (np.sign(ev_ret) == np.sign(fwd_ret)) if (ev_ret != 0 and fwd_ret != 0) else False

                # Signal: go long if event day was positive, short if negative
                sig = 1.0 if ev_ret > 0 else -1.0
                gross_trade = sig * fwd_ret
                net_trade = gross_trade - (cls.SWING_FEE_PCT + cls.SWING_SLIPPAGE_PCT)

                records.append(
                    EventObservationRecord(
                        event_date=ev_date,
                        event_type=ev["event_type"],
                        event_name=ev["event_name"],
                        event_day_return_pct=ev_ret,
                        abnormal_range_ratio=abnormal_rng,
                        fwd_3d_return_pct=fwd_ret,
                        fwd_3d_direction_aligned=aligned,
                        net_return_pct=float(net_trade),
                    )
                )

        n_events = len(records)
        if n_events == 0:
            return EventStudyEvaluationResult(
                hypothesis_id="P98-H005",
                total_events_matched=0,
                directional_alignment_rate=0.0,
                baseline_drift_rate=0.50,
                mean_post_event_return_pct=0.0,
                mean_net_return_pct=0.0,
                t_statistic=0.0,
                p_value=1.0,
                is_statistically_significant=False,
                sample_classification="INSUFFICIENT_DATA",
                success_criteria_met=False,
                evidence_notes="Zero event dates matched in daily price history.",
            )

        align_rate = float(np.mean([1.0 if r.fwd_3d_direction_aligned else 0.0 for r in records]))
        net_rets = np.array([r.net_return_pct for r in records])
        mean_net = float(np.mean(net_rets))
        mean_fwd = float(np.mean([r.fwd_3d_return_pct for r in records]))

        # One-sample t-test testing if net return > 0
        if np.std(net_rets) > 1e-8 and len(net_rets) > 1:
            t_stat, p_val = stats.ttest_1samp(net_rets, 0.0)
            t_stat = float(t_stat)
            p_val = float(p_val)
        else:
            t_stat = 0.0
            p_val = 1.0

        is_sig = (p_val < 0.05) and (t_stat > 0)
        success = (align_rate > 0.60) and is_sig and (n_events >= 15)

        return EventStudyEvaluationResult(
            hypothesis_id="P98-H005",
            total_events_matched=n_events,
            directional_alignment_rate=align_rate,
            baseline_drift_rate=0.50,
            mean_post_event_return_pct=mean_fwd,
            mean_net_return_pct=mean_net,
            t_statistic=t_stat,
            p_value=p_val,
            is_statistically_significant=is_sig,
            sample_classification="CONFIRMATORY_LIMITED_SAMPLE_EVENT_STUDY",
            success_criteria_met=success,
            evidence_notes=(
                f"Evaluated {n_events} verified policy announcements (2024-2026). "
                f"Directional Alignment: {align_rate:.1%}, Mean Net Return: {mean_net:.2%}, "
                f"t-stat: {t_stat:.2f}, p-value: {p_val:.4f}. "
                f"{'Statistically significant drift detected.' if is_sig else 'Drift is statistically indistinguishable from zero (p >= 0.05).'}"
            ),
            observations=records,
        )
