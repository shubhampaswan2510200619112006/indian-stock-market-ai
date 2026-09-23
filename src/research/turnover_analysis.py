"""
Phase 9.6 — Research Question K: Turnover Analysis & Friction Decay Engine.

Measures trading frequency, portfolio turnover, and fee drag per trade:
- Trades per session.
- Average holding period in trading sessions.
- Cost per trade vs Gross P&L per trade.
- Quantifies turnover drag decay rate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.ml.economic_metrics import EconomicMetricsEngine, IndianMarketFrictionModel


@dataclass
class TurnoverAnalysisReport:
    total_sessions: int
    total_trades: int
    trades_per_session: float
    average_holding_period_sessions: float
    total_turnover: float
    cost_per_trade_bps: float
    gross_pnl_per_trade_bps: float
    net_pnl_per_trade_bps: float
    is_excessive_turnover: bool
    turnover_diagnosis: str


class TurnoverAnalysisEngine:
    """
    Evaluates trading frequency and the rate of transaction drag decay.
    """

    @classmethod
    def analyze_turnover(
        cls,
        signals: np.ndarray,
        asset_returns: np.ndarray,
        friction_model: Optional[IndianMarketFrictionModel] = None,
    ) -> TurnoverAnalysisReport:
        friction = friction_model or IndianMarketFrictionModel()
        n = min(len(signals), len(asset_returns))
        sigs = signals[:n]
        rets = asset_returns[:n]

        econ = EconomicMetricsEngine.evaluate_strategy_returns(sigs, rets, frictions=friction)
        total_trades = max(1, econ.total_trades)
        trades_per_sess = float(total_trades / n) if n > 0 else 0.0

        # Holding period: average sessions per trade
        active_sessions = int(np.sum(sigs != 0))
        avg_holding = float(active_sessions / total_trades) if total_trades > 0 else 0.0

        # Frictions in basis points (1 bp = 0.0001 = 0.01%)
        total_fric = econ.total_fees + econ.total_slippage
        cost_per_trade_bps = float((total_fric / total_trades) * 10_000)
        gross_per_trade_bps = float((econ.gross_return / total_trades) * 10_000)
        net_per_trade_bps = float((econ.net_return / total_trades) * 10_000)

        # Excessive turnover if cost per trade > gross PnL per trade or trades/session > 0.4
        excessive = (cost_per_trade_bps > gross_per_trade_bps) or (trades_per_sess > 0.35)

        if excessive and gross_per_trade_bps > 0:
            diag = (
                f"EXCESSIVE_TURNOVER_DRAG: Strategy trades {trades_per_sess:.2f} times per session "
                f"(avg holding {avg_holding:.1f} days). Transaction friction ({cost_per_trade_bps:.1f} bps/trade) "
                f"exceeds gross edge ({gross_per_trade_bps:.1f} bps/trade), driving net edge to {net_per_trade_bps:.1f} bps."
            )
        elif gross_per_trade_bps <= 0:
            diag = (
                f"ZERO_GROSS_ALPHA: Strategy loses {gross_per_trade_bps:.1f} bps/trade before transaction costs. "
                "Turnover is compounding losses from an uninformative predictive signal."
            )
        else:
            diag = (
                f"SUSTAINABLE_TURNOVER: Gross profit ({gross_per_trade_bps:.1f} bps/trade) exceeds "
                f"transaction costs ({cost_per_trade_bps:.1f} bps/trade)."
            )

        return TurnoverAnalysisReport(
            total_sessions=n,
            total_trades=total_trades,
            trades_per_session=trades_per_sess,
            average_holding_period_sessions=avg_holding,
            total_turnover=econ.turnover,
            cost_per_trade_bps=cost_per_trade_bps,
            gross_pnl_per_trade_bps=gross_per_trade_bps,
            net_pnl_per_trade_bps=net_per_trade_bps,
            is_excessive_turnover=excessive,
            turnover_diagnosis=diag,
        )
