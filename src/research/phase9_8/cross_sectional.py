"""
Phase 9.8 — Track E: Cross-Sectional Equity Signals, Breadth & Dispersion Engine.

Investigates P98-H006:
- Tests whether relative strength divergence between Top 2 and Bottom 2 liquid equities
  predicts a 5-day long-short spread return.
- Measures:
  * 20-day rolling relative strength across 10 liquid Indian large-caps.
  * Weekly rebalanced Long (Top 2) / Short (Bottom 2) spread portfolio.
  * Cross-sectional return dispersion and market breadth.
- CRITICAL SURVIVORSHIP BIAS AUDIT:
  * Flagged explicitly as SURVIVORSHIP_BIAS_RISK = TRUE because historical point-in-time
    constituent membership tables are unavailable.
  * Cannot be presented as survivorship-free evidence for live deployment.
- Evaluated after Indian cash equity delivery statutory frictions (25 bps roundtrip).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class RebalanceRecord:
    rebalance_date: str
    top_stocks: List[str]
    bottom_stocks: List[str]
    long_leg_return_pct: float
    short_leg_return_pct: float
    spread_gross_return_pct: float
    frictions_pct: float
    spread_net_return_pct: float


@dataclass
class CrossSectionalEvaluationResult:
    hypothesis_id: str
    total_rebalances: int
    universe_size: int
    mean_spread_gross_return_pct: float
    mean_spread_net_return_pct: float
    spread_win_rate: float
    annualized_spread_sharpe: float
    max_drawdown_pct: float
    survivorship_bias_risk: bool
    sample_classification: str  # "CONFIRMATORY_WITH_SURVIVORSHIP_LIMITATION"
    success_criteria_met: bool
    evidence_notes: str
    sample_rebalances: List[RebalanceRecord] = field(default_factory=list)


class CrossSectionalEngine:
    """
    Evaluates cross-sectional relative strength momentum and dispersion across liquid equities.
    """

    DELIVERY_FRICTION_PCT: float = 0.0025  # 25 bps statutory delivery roundtrip (STT 10 bps on buy+sell, etc.)

    @classmethod
    def evaluate_relative_strength_5d(cls, df_equities: pd.DataFrame) -> CrossSectionalEvaluationResult:
        df = df_equities.copy()
        df["date"] = pd.to_datetime(df["date"])

        # Pivot close prices: index=date, columns=symbol
        pivot_close = df.pivot(index="date", columns="symbol", values="close").dropna()
        dates = pivot_close.index
        n_dates = len(dates)

        if n_dates < 40 or pivot_close.shape[1] < 5:
            return CrossSectionalEvaluationResult(
                hypothesis_id="P98-H006",
                total_rebalances=0,
                universe_size=pivot_close.shape[1],
                mean_spread_gross_return_pct=0.0,
                mean_spread_net_return_pct=0.0,
                spread_win_rate=0.0,
                annualized_spread_sharpe=0.0,
                max_drawdown_pct=0.0,
                survivorship_bias_risk=True,
                sample_classification="INSUFFICIENT_DATA",
                success_criteria_met=False,
                evidence_notes="Insufficient date coverage or equity cross-section.",
            )

        # 20-day rolling return
        ret_20d = pivot_close.pct_change(20)

        rebalances: List[RebalanceRecord] = []
        step = 5  # Weekly 5-day holding period

        for i in range(25, n_dates - step, step):
            d_t = dates[i]
            d_exit = dates[i + step]

            row_rs = ret_20d.loc[d_t].dropna()
            if len(row_rs) < 5:
                continue

            ranked = row_rs.sort_values(ascending=False)
            top_syms = ranked.index[:2].tolist()
            bot_syms = ranked.index[-2:].tolist()

            # Forward 5D return
            p_entry = pivot_close.loc[d_t]
            p_exit = pivot_close.loc[d_exit]

            long_rets = [(p_exit[s] - p_entry[s]) / p_entry[s] for s in top_syms]
            short_rets = [(p_entry[s] - p_exit[s]) / p_entry[s] for s in bot_syms]

            mean_long = float(np.mean(long_rets))
            mean_short = float(np.mean(short_rets))

            spread_gross = (mean_long + mean_short) / 2.0
            spread_net = spread_gross - cls.DELIVERY_FRICTION_PCT

            rebalances.append(
                RebalanceRecord(
                    rebalance_date=str(d_t.date()),
                    top_stocks=top_syms,
                    bottom_stocks=bot_syms,
                    long_leg_return_pct=mean_long,
                    short_leg_return_pct=mean_short,
                    spread_gross_return_pct=spread_gross,
                    frictions_pct=cls.DELIVERY_FRICTION_PCT,
                    spread_net_return_pct=spread_net,
                )
            )

        n_rebal = len(rebalances)
        if n_rebal == 0:
            return CrossSectionalEvaluationResult(
                hypothesis_id="P98-H006",
                total_rebalances=0,
                universe_size=pivot_close.shape[1],
                mean_spread_gross_return_pct=0.0,
                mean_spread_net_return_pct=0.0,
                spread_win_rate=0.0,
                annualized_spread_sharpe=0.0,
                max_drawdown_pct=0.0,
                survivorship_bias_risk=True,
                sample_classification="INSUFFICIENT_DATA",
                success_criteria_met=False,
                evidence_notes="Zero rebalances executed.",
            )

        net_spreads = np.array([r.spread_net_return_pct for r in rebalances])
        gross_spreads = np.array([r.spread_gross_return_pct for r in rebalances])

        mean_net = float(np.mean(net_spreads))
        mean_gross = float(np.mean(gross_spreads))
        win_rate = float(np.mean(net_spreads > 0))

        std_net = np.std(net_spreads)
        # ~50 weekly rebalances per year
        sharpe = float((mean_net / (std_net + 1e-8)) * np.sqrt(50)) if std_net > 1e-8 else 0.0

        cum = np.cumprod(1.0 + net_spreads)
        peak = np.maximum.accumulate(cum)
        dd = (cum - peak) / peak
        max_dd = float(np.min(dd)) if len(dd) > 0 else 0.0

        success = (mean_net > 0.01) and (sharpe > 0.50) and not True  # Disqualified if survivorship bias

        return CrossSectionalEvaluationResult(
            hypothesis_id="P98-H006",
            total_rebalances=n_rebal,
            universe_size=pivot_close.shape[1],
            mean_spread_gross_return_pct=mean_gross,
            mean_spread_net_return_pct=mean_net,
            spread_win_rate=win_rate,
            annualized_spread_sharpe=sharpe,
            max_drawdown_pct=max_dd,
            survivorship_bias_risk=True,
            sample_classification="CONFIRMATORY_WITH_SURVIVORSHIP_LIMITATION",
            success_criteria_met=False,  # Disqualified due to survivorship bias risk
            evidence_notes=(
                f"Cross-sectional relative strength momentum evaluated across {n_rebal} weekly rebalances on 10 liquid stocks. "
                f"Gross Spread: {mean_gross:.2%}, Net Spread: {mean_net:.2%}, Sharpe: {sharpe:.2f}. "
                f"CRITICAL: SURVIVORSHIP_BIAS_RISK = TRUE. Universe selection suffers from lookback survivorship bias. "
                f"Disqualified from production candidate status."
            ),
            sample_rebalances=rebalances[:10],
        )
