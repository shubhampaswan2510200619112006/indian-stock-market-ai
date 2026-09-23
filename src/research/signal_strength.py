"""
Phase 9.6 — Research Question D: Signal Strength & Conviction Bucketing Engine.

Investigates whether weak binary predictions hide useful high-conviction alpha:
- Partitions model probabilities into fixed, predefined confidence buckets:
  50–55%, 55–60%, 60–65%, 65–70%, 70%+.
- Mandatory Sample-Size Guards: If a bucket contains fewer than 10 observations,
  it is explicitly marked INSUFFICIENT_SAMPLE.
- Strictly prohibits post-hoc bucket merging or threshold hunting on test partitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class ConvictionBucketReport:
    bucket_label: str
    prob_min: float
    prob_max: float
    observation_count: int
    trade_count: int
    win_rate: float
    gross_return: float
    net_return: float
    expectancy_per_trade: float
    sample_status: str  # "RELIABLE" or "INSUFFICIENT_SAMPLE"
    notes: str = ""


@dataclass
class SignalStrengthSummary:
    bucket_reports: List[ConvictionBucketReport]
    monotonic_conviction_alpha: bool  # True if higher conviction monotonically yields higher expectancy
    high_conviction_profitable: bool
    conclusion: str


class SignalStrengthEngine:
    """
    Evaluates probability conviction buckets under strict sample-size guards.
    """

    MIN_SAMPLES_PER_BUCKET: int = 10

    @classmethod
    def evaluate_confidence_buckets(
        cls,
        probabilities: np.ndarray,
        actual_outcomes: np.ndarray,
        asset_returns: np.ndarray,
        base_fee_pct: float = 0.0005,
        base_slippage_pct: float = 0.0005,
    ) -> SignalStrengthSummary:
        """
        Partitions predictions by probability distance from 0.50 into 5 predefined bins:
        Bucket 1: 50% to 55%
        Bucket 2: 55% to 60%
        Bucket 3: 60% to 65%
        Bucket 4: 65% to 70%
        Bucket 5: 70%+
        """
        n = min(len(probabilities), len(actual_outcomes), len(asset_returns))
        probs = probabilities[:n]
        actuals = actual_outcomes[:n]
        rets = asset_returns[:n]

        # Normalized conviction distance: |P - 0.5| + 0.5 -> maps [0.5, 1.0]
        conviction = np.maximum(probs, 1.0 - probs)

        bucket_definitions = [
            ("50%–55% (Marginal)", 0.50, 0.55),
            ("55%–60% (Moderate)", 0.55, 0.60),
            ("60%–65% (Strong)", 0.60, 0.65),
            ("65%–70% (Very Strong)", 0.65, 0.70),
            ("70%+ (Extreme Conviction)", 0.70, 1.00),
        ]

        reports: List[ConvictionBucketReport] = []
        expectancies = []

        total_cost_per_trade = (base_fee_pct + base_slippage_pct) * 2.0  # roundtrip

        for label, p_min, p_max in bucket_definitions:
            if p_max == 1.00:
                mask = (conviction >= p_min) & (conviction <= p_max)
            else:
                mask = (conviction >= p_min) & (conviction < p_max)

            count = int(np.sum(mask))

            if count < cls.MIN_SAMPLES_PER_BUCKET:
                reports.append(
                    ConvictionBucketReport(
                        bucket_label=label,
                        prob_min=p_min,
                        prob_max=p_max,
                        observation_count=count,
                        trade_count=count,
                        win_rate=0.0,
                        gross_return=0.0,
                        net_return=0.0,
                        expectancy_per_trade=0.0,
                        sample_status="INSUFFICIENT_SAMPLE",
                        notes=f"Bucket contains only {count} observations (minimum {cls.MIN_SAMPLES_PER_BUCKET} required). Cannot infer statistical edge.",
                    )
                )
                continue

            sub_probs = probs[mask]
            sub_actuals = actuals[mask]
            sub_rets = rets[mask]

            # Signal: +1 if P >= 0.5 else -1
            sub_sigs = np.where(sub_probs >= 0.5, 1.0, -1.0)
            trade_wins = (sub_sigs == np.where(sub_actuals == 1, 1.0, -1.0))
            win_rate = float(np.mean(trade_wins))

            gross_pnls = sub_sigs * sub_rets
            net_pnls = gross_pnls - total_cost_per_trade

            gross_ret = float(np.sum(gross_pnls))
            net_ret = float(np.sum(net_pnls))
            exp = float(np.mean(net_pnls))
            expectancies.append((p_min, exp))

            reports.append(
                ConvictionBucketReport(
                    bucket_label=label,
                    prob_min=p_min,
                    prob_max=p_max,
                    observation_count=count,
                    trade_count=count,
                    win_rate=win_rate,
                    gross_return=gross_ret,
                    net_return=net_ret,
                    expectancy_per_trade=exp,
                    sample_status="RELIABLE",
                    notes="Sufficient sample size verified.",
                )
            )

        # Check for monotonic conviction relationship
        valid_exps = [e[1] for e in expectancies]
        monotonic = (len(valid_exps) >= 2) and all(x < y for x, y in zip(valid_exps, valid_exps[1:]))
        high_conv_profit = any(r.net_return > 0 and r.sample_status == "RELIABLE" for r in reports if r.prob_min >= 0.60)

        if monotonic and high_conv_profit:
            conclusion = "MONOTONIC_CONVICTION_ALPHA: Higher model probability conviction produces systematically higher net expectancy."
        elif not high_conv_profit:
            conclusion = "NO_CONVICTION_EDGE: Higher probability buckets fail to produce positive expectancy after transaction frictions."
        else:
            conclusion = "MIXED_CONVICTION_RELATIONSHIP: Higher conviction does not reliably correlate with increased net returns."

        return SignalStrengthSummary(
            bucket_reports=reports,
            monotonic_conviction_alpha=monotonic,
            high_conviction_profitable=high_conv_profit,
            conclusion=conclusion,
        )
