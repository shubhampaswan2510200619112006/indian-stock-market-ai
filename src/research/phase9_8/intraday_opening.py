"""
Phase 9.8 — Track A: Intraday Opening Drive & Opening Gap Research Engine.

Investigates:
1. P98-H001: 15-Minute Opening Range Breakout (ORB 15m)
   - Range established 09:15 to 09:30 IST.
   - Long if subsequent 5m bar breaks above 15m high; Short if breaks below 15m low.
   - Held until intraday MOC exit at 15:15 IST.
2. P98-H002: Opening Gap Continuation vs Mean-Reversion (30m)
   - Overnight gap measured from previous close to 09:15 open.
   - Significant gap threshold = +/- 0.30% (fixed, anti-mining).
   - Evaluates whether opening 30-minute bar (09:15 - 09:45) mean-reverts or continues.

Mandatory Constraints:
- Sample limited to ~59 sessions -> Classified explicitly as EXPLORATORY_ONLY.
- Evaluated after Indian statutory intraday transaction frictions (10 bps roundtrip).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class ORBTradeRecord:
    date: str
    direction: str
    breakout_price: float
    exit_price: float
    gross_return_pct: float
    fees_pct: float
    slippage_pct: float
    net_return_pct: float
    held_bars: int


@dataclass
class ORBEvaluationResult:
    hypothesis_id: str
    total_sessions_analyzed: int
    total_breakouts: int
    win_rate: float
    gross_return_pct: float
    net_return_pct: float
    net_expectancy_bps: float
    annualized_sharpe: float
    max_drawdown_pct: float
    sample_classification: str  # "INSUFFICIENT_DATA_FOR_CONFIRMATORY_INFERENCE (EXPLORATORY_ONLY)"
    success_criteria_met: bool
    evidence_notes: str
    trades: List[ORBTradeRecord] = field(default_factory=list)


@dataclass
class GapTradeRecord:
    date: str
    gap_pct: float
    gap_type: str  # "UP_GAP" or "DOWN_GAP"
    trade_direction: str  # "REVERSION" or "CONTINUATION"
    open_price: float
    exit_price: float
    gross_return_pct: float
    net_return_pct: float


@dataclass
class GapEvaluationResult:
    hypothesis_id: str
    total_sessions_analyzed: int
    total_gap_events: int
    mean_reversion_win_rate: float
    continuation_win_rate: float
    reversion_gross_expectancy_bps: float
    reversion_net_expectancy_bps: float
    sample_classification: str
    success_criteria_met: bool
    evidence_notes: str
    gap_trades: List[GapTradeRecord] = field(default_factory=list)


class IntradayOpeningEngine:
    """
    Evaluates Opening Range Breakout (ORB) and Opening Gap behavior on intraday data.
    """

    INTRADAY_FEE_PCT: float = 0.0005     # 5 bps statutory friction
    INTRADAY_SLIPPAGE_PCT: float = 0.0005 # 5 bps slippage

    @classmethod
    def evaluate_orb_15m(cls, df_5m: pd.DataFrame, symbol: str = "^NSEI") -> ORBEvaluationResult:
        """
        Evaluates 15-minute Opening Range Breakout on 5-minute bars.
        """
        df = df_5m.copy()
        df["time"] = df["datetime"].dt.time
        dates = sorted(df["date"].unique())

        trades: List[ORBTradeRecord] = []

        for d in dates:
            day_df = df[df["date"] == d].sort_values("datetime").reset_index(drop=True)
            if len(day_df) < 6:  # Need at least 30 mins
                continue

            # First 15 mins: first 3 bars (09:15, 09:20, 09:25 close at 09:30)
            orb_bars = day_df.iloc[:3]
            orb_high = orb_bars["high"].max()
            orb_low = orb_bars["low"].min()

            remainder = day_df.iloc[3:]
            if len(remainder) == 0:
                continue

            in_trade = False
            trade_dir = ""
            entry_price = 0.0
            exit_price = 0.0
            held_bars = 0

            for idx, row in remainder.iterrows():
                if not in_trade:
                    if row["close"] > orb_high:
                        in_trade = True
                        trade_dir = "LONG"
                        entry_price = row["close"]
                    elif row["close"] < orb_low:
                        in_trade = True
                        trade_dir = "SHORT"
                        entry_price = row["close"]
                else:
                    held_bars += 1
                    # Exit at last bar of session (15:15 or later)
                    if idx == remainder.index[-1]:
                        exit_price = row["close"]
                        break

            if in_trade and entry_price > 0 and exit_price > 0:
                if trade_dir == "LONG":
                    gross_ret = (exit_price - entry_price) / entry_price
                else:
                    gross_ret = (entry_price - exit_price) / entry_price

                total_friction = cls.INTRADAY_FEE_PCT + cls.INTRADAY_SLIPPAGE_PCT
                net_ret = gross_ret - total_friction

                trades.append(
                    ORBTradeRecord(
                        date=str(d),
                        direction=trade_dir,
                        breakout_price=float(entry_price),
                        exit_price=float(exit_price),
                        gross_return_pct=float(gross_ret),
                        fees_pct=float(cls.INTRADAY_FEE_PCT),
                        slippage_pct=float(cls.INTRADAY_SLIPPAGE_PCT),
                        net_return_pct=float(net_ret),
                        held_bars=held_bars,
                    )
                )

        n_trades = len(trades)
        if n_trades == 0:
            return ORBEvaluationResult(
                hypothesis_id="P98-H001",
                total_sessions_analyzed=len(dates),
                total_breakouts=0,
                win_rate=0.0,
                gross_return_pct=0.0,
                net_return_pct=0.0,
                net_expectancy_bps=0.0,
                annualized_sharpe=0.0,
                max_drawdown_pct=0.0,
                sample_classification="INSUFFICIENT_DATA_FOR_CONFIRMATORY_INFERENCE (EXPLORATORY_ONLY)",
                success_criteria_met=False,
                evidence_notes="Zero qualifying breakout trades in sample.",
            )

        net_rets = np.array([t.net_return_pct for t in trades])
        gross_rets = np.array([t.gross_return_pct for t in trades])
        win_rate = float(np.mean(net_rets > 0))
        tot_net = float(np.sum(net_rets))
        tot_gross = float(np.sum(gross_rets))
        expectancy_bps = float(np.mean(net_rets) * 10000.0)

        # Sharpe calculation
        std_net = np.std(net_rets)
        sharpe = float((np.mean(net_rets) / (std_net + 1e-8)) * np.sqrt(252)) if std_net > 1e-8 else 0.0

        # Drawdown
        cum = np.cumprod(1.0 + net_rets)
        peak = np.maximum.accumulate(cum)
        dd = (cum - peak) / peak
        max_dd = float(np.min(dd)) if len(dd) > 0 else 0.0

        # Success requires Net Sharpe > 0.50, Win Rate > 53%, Net Exp > 5 bps AND N >= 60
        # Given N = 59 sessions, N < 60, so cannot be confirmatory
        success = (sharpe > 0.50) and (win_rate > 0.53) and (expectancy_bps > 5.0) and (n_trades >= 60)

        return ORBEvaluationResult(
            hypothesis_id="P98-H001",
            total_sessions_analyzed=len(dates),
            total_breakouts=n_trades,
            win_rate=win_rate,
            gross_return_pct=tot_gross,
            net_return_pct=tot_net,
            net_expectancy_bps=expectancy_bps,
            annualized_sharpe=sharpe,
            max_drawdown_pct=max_dd,
            sample_classification="INSUFFICIENT_DATA_FOR_CONFIRMATORY_INFERENCE (EXPLORATORY_ONLY)",
            success_criteria_met=success,
            evidence_notes=(
                f"15m ORB generated {n_trades} trades across {len(dates)} sessions. "
                f"Win Rate: {win_rate:.1%}, Net Expectancy: {expectancy_bps:.1f} bps, Annualized Sharpe: {sharpe:.2f}. "
                f"The P98-H001 sample contains {n_trades} trades and therefore does not satisfy the project's preregistered minimum sample criterion of N>=60 for confirmatory classification. "
                f"This threshold is a project-specific research gate and is not being presented as a universal statistical law. "
                f"Classified strictly as EXPLORATORY_ONLY."
            ),
            trades=trades[:10],
        )

    @classmethod
    def evaluate_gap_30m(cls, df_5m: pd.DataFrame, gap_threshold_pct: float = 0.003) -> GapEvaluationResult:
        """
        Evaluates 30-minute Opening Gap Continuation vs Mean-Reversion.
        Gap defined as (Day T open - Day T-1 close) / Day T-1 close.
        """
        df = df_5m.copy()
        dates = sorted(df["date"].unique())

        gap_trades: List[GapTradeRecord] = []
        prior_close = None

        for d in dates:
            day_df = df[df["date"] == d].sort_values("datetime").reset_index(drop=True)
            if len(day_df) < 6:
                continue

            current_open = day_df.iloc[0]["open"]
            exit_30m = day_df.iloc[5]["close"]  # 6th bar close (09:40-09:45 bar)

            if prior_close is not None:
                gap_pct = (current_open - prior_close) / prior_close
                if abs(gap_pct) >= gap_threshold_pct:
                    is_up_gap = (gap_pct > 0)
                    gap_type = "UP_GAP" if is_up_gap else "DOWN_GAP"

                    # Mean reversion: short on up gap, long on down gap
                    if is_up_gap:
                        rev_gross = (current_open - exit_30m) / current_open
                    else:
                        rev_gross = (exit_30m - current_open) / current_open

                    total_friction = cls.INTRADAY_FEE_PCT + cls.INTRADAY_SLIPPAGE_PCT
                    rev_net = rev_gross - total_friction

                    gap_trades.append(
                        GapTradeRecord(
                            date=str(d),
                            gap_pct=float(gap_pct),
                            gap_type=gap_type,
                            trade_direction="REVERSION",
                            open_price=float(current_open),
                            exit_price=float(exit_30m),
                            gross_return_pct=float(rev_gross),
                            net_return_pct=float(rev_net),
                        )
                    )

            prior_close = day_df.iloc[-1]["close"]

        n_events = len(gap_trades)
        if n_events == 0:
            return GapEvaluationResult(
                hypothesis_id="P98-H002",
                total_sessions_analyzed=len(dates),
                total_gap_events=0,
                mean_reversion_win_rate=0.0,
                continuation_win_rate=0.0,
                reversion_gross_expectancy_bps=0.0,
                reversion_net_expectancy_bps=0.0,
                sample_classification="INSUFFICIENT_DATA_FOR_CONFIRMATORY_INFERENCE (EXPLORATORY_ONLY)",
                success_criteria_met=False,
                evidence_notes="Zero opening gaps >= 0.30% detected in the available ~59 sessions.",
            )

        rev_nets = np.array([g.net_return_pct for g in gap_trades])
        rev_gross = np.array([g.gross_return_pct for g in gap_trades])
        reversion_win_rate = float(np.mean(rev_nets > 0))
        cont_win_rate = 1.0 - reversion_win_rate
        net_exp_bps = float(np.mean(rev_nets) * 10000.0)
        gross_exp_bps = float(np.mean(rev_gross) * 10000.0)

        success = (reversion_win_rate > 0.55) and (net_exp_bps > 5.0) and (n_events >= 20)

        return GapEvaluationResult(
            hypothesis_id="P98-H002",
            total_sessions_analyzed=len(dates),
            total_gap_events=n_events,
            mean_reversion_win_rate=reversion_win_rate,
            continuation_win_rate=cont_win_rate,
            reversion_gross_expectancy_bps=gross_exp_bps,
            reversion_net_expectancy_bps=net_exp_bps,
            sample_classification="INSUFFICIENT_DATA_FOR_CONFIRMATORY_INFERENCE (EXPLORATORY_ONLY)",
            success_criteria_met=success,
            evidence_notes=(
                f"Opening gap (|gap| >= 0.30%) evaluated across {n_events} gap sessions. "
                f"Mean-reversion Win Rate: {reversion_win_rate:.1%}, Net Expectancy: {net_exp_bps:.1f} bps. "
                f"Sample size N = {n_events} is limited; classified strictly as EXPLORATORY_ONLY."
            ),
            gap_trades=gap_trades[:10],
        )
