"""
Phase 11 Hypothesis Evaluation Engine.

Evaluates the exact six preregistered cross-sectional equity signals:
- H11-001: Cross-Sectional Momentum (20d lookback / 5d holding)
- H11-002: Short-Term Reversal (5d lookback / 5d holding)
- H11-003: Volatility-Adjusted Momentum (20d lookback / 5d holding)
- H11-004: Volume/Turnover Confirmation (20d lookback / 5d holding, strictly point-in-time VR > 1.2)
- H11-005: Relative Strength Persistence (20d & 60d relative to NIFTY 50 / 10d holding)
- H11-006: Market-Breadth Conditioning (20d momentum conditioned on universe > 50d SMA)

Enforces:
- Strict point-in-time calculation (no lookahead, no future closes or volumes)
- Chronological partitions: Train (diagnostic), Validation (diagnostic), Untouched OOS (evaluative)
- Double-entry transaction friction accounting via IndianEquityCostModel
"""

from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from src.research.phase11.data_auditor import DataAuditor, EQUITY_SYMBOLS
from src.research.phase11.cost_model import IndianEquityCostModel


@dataclass
class PeriodEvaluation:
    rebalance_date: str
    forward_end_date: str
    long_symbols: List[str]
    short_symbols: List[str]
    long_return: float
    short_return: float
    gross_spread: float
    turnover: float
    friction: float
    net_spread: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HypothesisRunResult:
    hypothesis_id: str
    hypothesis_name: str
    lookback: int
    holding_period: int
    total_rebalances: int
    train_rebalances: int
    val_rebalances: int
    oos_rebalances: int
    # OOS Primary Metrics
    oos_gross_expectancy_bps: float
    oos_net_expectancy_bps: float
    oos_annualized_net_return_pct: float
    oos_annualized_volatility_pct: float
    oos_sharpe_ratio: float
    oos_max_drawdown_pct: float
    oos_win_rate_pct: float
    total_statutory_friction_bps: float
    total_brokerage_friction_bps: float
    total_slippage_friction_bps: float
    # Partition Breakdowns
    train_metrics: Dict[str, Any]
    val_metrics: Dict[str, Any]
    oos_metrics: Dict[str, Any]
    # Detailed time series
    rebalance_history: List[PeriodEvaluation]
    additional_reporting: Dict[str, Any] = field(default_factory=dict)


class HypothesisEngine:
    """
    Evaluates hypotheses across chronological partitions on aligned equity panel.
    """

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root
        self.auditor = DataAuditor(workspace_root=workspace_root)
        self.cost_model = IndianEquityCostModel()
        self._load_data()

    def _load_data(self) -> None:
        equity_df, bench_df = self.auditor.load_aligned_data()
        self.equity_df = equity_df
        self.bench_df = bench_df

        # Pivot prices, volumes, and returns for fast point-in-time vectorized slicing
        self.price_pivot = equity_df.pivot(index="date", columns="symbol", values="close")
        self.volume_pivot = equity_df.pivot(index="date", columns="symbol", values="volume")
        self.all_dates = sorted(self.price_pivot.index.tolist())

        # Benchmark mapping
        bench_map = bench_df.set_index("date")["nifty_close"].to_dict()
        self.bench_series = pd.Series([bench_map.get(d, np.nan) for d in self.all_dates], index=self.all_dates).ffill()

        # Partition dates:
        # Train: 2024-01-01 to 2025-03-31
        # Validation: 2025-04-01 to 2025-10-31
        # OOS: 2025-11-01 to 2026-09-09
        self.train_dates = [d for d in self.all_dates if d <= "2025-03-31"]
        self.val_dates = [d for d in self.all_dates if "2025-04-01" <= d <= "2025-10-31"]
        self.oos_dates = [d for d in self.all_dates if d >= "2025-11-01"]

    def _calculate_metrics_from_periods(self, periods: List[PeriodEvaluation], holding_days: int) -> Dict[str, Any]:
        """Computes summary statistics from a sequence of period evaluations."""
        if not periods:
            return {
                "sample_size": 0,
                "gross_expectancy_bps": 0.0,
                "net_expectancy_bps": 0.0,
                "annualized_net_return_pct": 0.0,
                "annualized_volatility_pct": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown_pct": 0.0,
                "win_rate_pct": 0.0,
                "net_spreads_bps": [],
            }

        gross_spreads = np.array([p.gross_spread for p in periods])
        net_spreads = np.array([p.net_spread for p in periods])
        n = len(periods)

        gross_exp_bps = float(np.mean(gross_spreads) * 10000.0)
        net_exp_bps = float(np.mean(net_spreads) * 10000.0)
        win_rate = float(np.mean(net_spreads > 0) * 100.0)

        # Annualization: periods per year = 252 / holding_days
        periods_per_year = 252.0 / holding_days
        ann_net_ret = float(np.mean(net_spreads) * periods_per_year * 100.0)
        ann_vol = float(np.std(net_spreads, ddof=1) * np.sqrt(periods_per_year) * 100.0) if n > 1 else 0.0
        sharpe = (ann_net_ret / ann_vol) if ann_vol > 1e-6 else 0.0

        # Cumulative path & Drawdown
        cum_ret = np.cumprod(1.0 + net_spreads)
        peaks = np.maximum.accumulate(cum_ret)
        drawdowns = (cum_ret - peaks) / peaks
        max_dd = float(np.min(drawdowns) * 100.0) if len(drawdowns) > 0 else 0.0

        return {
            "sample_size": n,
            "gross_expectancy_bps": round(gross_exp_bps, 2),
            "net_expectancy_bps": round(net_exp_bps, 2),
            "annualized_net_return_pct": round(ann_net_ret, 2),
            "annualized_volatility_pct": round(ann_vol, 2),
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "win_rate_pct": round(win_rate, 2),
            "net_spreads_bps": [round(x * 10000.0, 2) for x in net_spreads],
        }

    def evaluate_hypothesis(self, hypothesis_id: str, cost_multiplier: float = 1.0) -> HypothesisRunResult:
        """
        Executes evaluation of a single hypothesis across all partitions.
        """
        cm = IndianEquityCostModel(cost_multiplier=cost_multiplier)

        lookback = 20
        holding_period = 5
        name = "Unknown"

        if hypothesis_id == "H11-001":
            name = "Cross-Sectional Momentum"
            lookback = 20
            holding_period = 5
        elif hypothesis_id == "H11-002":
            name = "Short-Term Reversal"
            lookback = 5
            holding_period = 5
        elif hypothesis_id == "H11-003":
            name = "Volatility-Adjusted Momentum"
            lookback = 20
            holding_period = 5
        elif hypothesis_id == "H11-004":
            name = "Volume/Turnover Confirmation"
            lookback = 20
            holding_period = 5
        elif hypothesis_id == "H11-005":
            name = "Relative Strength Persistence"
            lookback = 60
            holding_period = 10
        elif hypothesis_id == "H11-006":
            name = "Market-Breadth Conditioning"
            lookback = 50
            holding_period = 5

        # Rebalance schedule: non-overlapping windows of length holding_period
        # Start after lookback days have elapsed
        all_evaluations: List[PeriodEvaluation] = []
        additional_reporting: Dict[str, Any] = {}

        # Tracking for H11-006
        breadth_above_50_count = 0
        breadth_below_or_equal_count = 0

        # Step through non-overlapping periods
        idx = lookback
        while idx + holding_period < len(self.all_dates):
            reb_date = self.all_dates[idx]
            fwd_end_date = self.all_dates[idx + holding_period]

            # Price slices up to reb_date (strictly point-in-time)
            prices_hist = self.price_pivot.iloc[:idx + 1]
            volumes_hist = self.volume_pivot.iloc[:idx + 1]

            # Forward prices
            current_prices = self.price_pivot.iloc[idx]
            future_prices = self.price_pivot.iloc[idx + holding_period]
            fwd_returns = (future_prices / current_prices) - 1.0

            long_syms: List[str] = []
            short_syms: List[str] = []
            details: Dict[str, Any] = {}

            # H11-001: 20d momentum
            if hypothesis_id == "H11-001":
                r20 = (prices_hist.iloc[-1] / prices_hist.iloc[-1 - lookback]) - 1.0
                ranked = r20.sort_values(ascending=False)
                long_syms = list(ranked.index[:3])
                short_syms = list(ranked.index[-3:])

            # H11-002: 5d reversal (lowest past return is Long)
            elif hypothesis_id == "H11-002":
                r5 = (prices_hist.iloc[-1] / prices_hist.iloc[-1 - lookback]) - 1.0
                ranked = r5.sort_values(ascending=True)  # Lowest first
                long_syms = list(ranked.index[:3])  # Extreme losers
                short_syms = list(ranked.index[-3:])  # Extreme winners

            # H11-003: Volatility-adjusted momentum
            elif hypothesis_id == "H11-003":
                daily_rets = prices_hist.iloc[-lookback:].pct_change().dropna()
                vol = daily_rets.std()
                r20 = (prices_hist.iloc[-1] / prices_hist.iloc[-1 - lookback]) - 1.0
                vol_adj = r20 / np.maximum(vol, 1e-6)
                ranked = vol_adj.sort_values(ascending=False)
                long_syms = list(ranked.index[:3])
                short_syms = list(ranked.index[-3:])

            # H11-004: Volume/Turnover confirmation
            elif hypothesis_id == "H11-004":
                r20 = (prices_hist.iloc[-1] / prices_hist.iloc[-1 - lookback]) - 1.0
                # Volume ratio denominator strictly excludes today's volume (trailing 20 prior days)
                vol_denom = volumes_hist.iloc[-21:-1].mean()
                vol_ratio = volumes_hist.iloc[-1] / np.maximum(vol_denom, 1.0)
                ranked_r20 = r20.sort_values(ascending=False)
                top_3_candidates = list(ranked_r20.index[:3])
                bottom_3_candidates = list(ranked_r20.index[-3:])

                # Symmetrical volume confirmation rule: Volume Ratio > 1.2
                long_syms = [s for s in top_3_candidates if vol_ratio.get(s, 0.0) > 1.2]
                short_syms = [s for s in bottom_3_candidates if vol_ratio.get(s, 0.0) > 1.2]
                details["confirmed_longs_count"] = len(long_syms)
                details["confirmed_shorts_count"] = len(short_syms)

            # H11-005: Relative strength persistence (dual 20d & 60d vs benchmark)
            elif hypothesis_id == "H11-005":
                bench_hist = self.bench_series.iloc[:idx + 1]
                bench_r20 = (bench_hist.iloc[-1] / bench_hist.iloc[-21]) - 1.0
                bench_r60 = (bench_hist.iloc[-1] / bench_hist.iloc[-61]) - 1.0

                r20 = (prices_hist.iloc[-1] / prices_hist.iloc[-21]) - 1.0
                r60 = (prices_hist.iloc[-1] / prices_hist.iloc[-61]) - 1.0

                rs20 = r20 - bench_r20
                rs60 = r60 - bench_r60

                rank20 = rs20.rank(ascending=True)
                rank60 = rs60.rank(ascending=True)
                combined_score = rank20 + rank60
                ranked = combined_score.sort_values(ascending=False)
                long_syms = list(ranked.index[:3])
                short_syms = list(ranked.index[-3:])

            # H11-006: Market-breadth conditioning
            elif hypothesis_id == "H11-006":
                # % of universe above 50-day SMA
                sma50 = prices_hist.iloc[-50:].mean()
                breadth_above = (prices_hist.iloc[-1] > sma50).mean() * 100.0

                if breadth_above > 50.0:
                    breadth_above_50_count += 1
                    r20 = (prices_hist.iloc[-1] / prices_hist.iloc[-21]) - 1.0
                    ranked = r20.sort_values(ascending=False)
                    long_syms = list(ranked.index[:3])
                    short_syms = list(ranked.index[-3:])
                    details["breadth_state"] = "ACTIVE (>50%)"
                else:
                    breadth_below_or_equal_count += 1
                    long_syms = []
                    short_syms = []
                    details["breadth_state"] = "INACTIVE_CASH (<=50%)"
                details["breadth_pct"] = round(breadth_above, 2)

            # Compute returns
            long_ret = float(fwd_returns[long_syms].mean()) if long_syms else 0.0
            short_ret = float(fwd_returns[short_syms].mean()) if short_syms else 0.0
            gross_spread = long_ret - short_ret

            # Compute dynamic transaction costs
            # If both legs active: 2 full round-trips turnover (1.0 long + 1.0 short)
            # If cash: 0 turnover
            turnover = 0.0
            if long_syms:
                turnover += 1.0
            if short_syms:
                turnover += 1.0

            rt_cost = cm.compute_round_trip(100.0, 100.0)
            # Friction as a rate: total_friction / 100 * turnover
            friction_rate = (rt_cost.total_friction / 100.0) * (turnover / 2.0)  # normalized per dollar of spread
            net_spread = gross_spread - friction_rate

            all_evaluations.append(PeriodEvaluation(
                rebalance_date=reb_date,
                forward_end_date=fwd_end_date,
                long_symbols=long_syms,
                short_symbols=short_syms,
                long_return=long_ret,
                short_return=short_ret,
                gross_spread=gross_spread,
                turnover=turnover,
                friction=friction_rate,
                net_spread=net_spread,
                details=details,
            ))

            idx += holding_period

        # Partition allocations
        train_evals = [p for p in all_evaluations if p.rebalance_date <= "2025-03-31"]
        val_evals = [p for p in all_evaluations if "2025-04-01" <= p.rebalance_date <= "2025-10-31"]
        oos_evals = [p for p in all_evaluations if p.rebalance_date >= "2025-11-01"]

        train_metrics = self._calculate_metrics_from_periods(train_evals, holding_period)
        val_metrics = self._calculate_metrics_from_periods(val_evals, holding_period)
        oos_metrics = self._calculate_metrics_from_periods(oos_evals, holding_period)

        if hypothesis_id == "H11-006":
            additional_reporting = {
                "TOTAL_ELIGIBLE_DATES": len(all_evaluations),
                "BREADTH_ABOVE_50_DATES": breadth_above_50_count,
                "BREADTH_BELOW_OR_EQUAL_50_DATES": breadth_below_or_equal_count,
                "SIGNAL_OBSERVATIONS_AFTER_CONDITIONING": breadth_above_50_count,
            }

        # Detailed breakdown of friction components on OOS
        sample_rt = cm.compute_round_trip(100.0, 100.0)
        statutory_bps = (sample_rt.total_statutory_cost / 100.0) * 10000.0
        brokerage_bps = (sample_rt.total_brokerage / 100.0) * 10000.0
        slippage_bps = (sample_rt.total_slippage / 100.0) * 10000.0

        return HypothesisRunResult(
            hypothesis_id=hypothesis_id,
            hypothesis_name=name,
            lookback=lookback,
            holding_period=holding_period,
            total_rebalances=len(all_evaluations),
            train_rebalances=len(train_evals),
            val_rebalances=len(val_evals),
            oos_rebalances=len(oos_evals),
            oos_gross_expectancy_bps=oos_metrics["gross_expectancy_bps"],
            oos_net_expectancy_bps=oos_metrics["net_expectancy_bps"],
            oos_annualized_net_return_pct=oos_metrics["annualized_net_return_pct"],
            oos_annualized_volatility_pct=oos_metrics["annualized_volatility_pct"],
            oos_sharpe_ratio=oos_metrics["sharpe_ratio"],
            oos_max_drawdown_pct=oos_metrics["max_drawdown_pct"],
            oos_win_rate_pct=oos_metrics["win_rate_pct"],
            total_statutory_friction_bps=round(statutory_bps, 2),
            total_brokerage_friction_bps=round(brokerage_bps, 2),
            total_slippage_friction_bps=round(slippage_bps, 2),
            train_metrics=train_metrics,
            val_metrics=val_metrics,
            oos_metrics=oos_metrics,
            rebalance_history=all_evaluations,
            additional_reporting=additional_reporting,
        )


if __name__ == "__main__":
    engine = HypothesisEngine()
    for hid in ["H11-001", "H11-002", "H11-003", "H11-004", "H11-005", "H11-006"]:
        res = engine.evaluate_hypothesis(hid)
        print(f"{hid} ({res.hypothesis_name}):")
        print(f"  OOS Rebalances: {res.oos_rebalances}")
        print(f"  OOS Gross Exp: {res.oos_gross_expectancy_bps:+.2f} bps | Net Exp: {res.oos_net_expectancy_bps:+.2f} bps | Sharpe: {res.oos_sharpe_ratio:+.2f}")
        if res.additional_reporting:
            print(f"  Additional: {res.additional_reporting}")
