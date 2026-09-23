"""
Phase 8 — Paper Trading Metrics.

Reuses existing backtesting metric logic.
A profitable paper session MUST NOT automatically be described as an edge.
Evidence labels: VERY_LIMITED_EVIDENCE, LIMITED_EVIDENCE, PRELIMINARY_EVIDENCE, INSUFFICIENT_SAMPLE.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from src.paper_trading.models import PaperPortfolioSnapshot, PaperTradeRecord


def compute_paper_evidence_label(
    total_trades: int,
    trading_days: int = 0,
) -> str:
    """
    Determine statistical evidence label for paper trading results.

    A profitable session does NOT automatically establish an edge.
    """
    if total_trades < 5:
        return "INSUFFICIENT_SAMPLE"
    if total_trades < 15:
        return "VERY_LIMITED_EVIDENCE"
    if total_trades < 30 or trading_days < 20:
        return "LIMITED_EVIDENCE"
    return "PRELIMINARY_EVIDENCE"


def compute_paper_performance(
    trades: List[PaperTradeRecord],
    snapshots: List[PaperPortfolioSnapshot],
    initial_capital: float,
) -> Dict:
    """
    Calculate performance metrics for paper trading.

    Returns INSUFFICIENT_SAMPLE for metrics that cannot be calculated.
    """
    if not trades:
        return {
            "total_trades": 0,
            "status": "INSUFFICIENT_SAMPLE",
            "evidence_label": "INSUFFICIENT_SAMPLE",
            "disclaimer": "Paper trading results do not predict future profitability.",
        }

    total_trades = len(trades)
    winning = [t for t in trades if t.net_pnl > 0]
    losing = [t for t in trades if t.net_pnl <= 0]

    win_rate = len(winning) / total_trades if total_trades > 0 else 0.0
    gross_pnl = sum(t.gross_pnl for t in trades)
    total_fees = sum(t.fees for t in trades)
    total_slippage = sum(t.slippage for t in trades)
    net_pnl = sum(t.net_pnl for t in trades)

    avg_win = float(np.mean([t.net_pnl for t in winning])) if winning else 0.0
    avg_loss = float(np.mean([abs(t.net_pnl) for t in losing])) if losing else 0.0

    gross_wins = sum(t.net_pnl for t in winning)
    gross_losses = sum(abs(t.net_pnl) for t in losing)
    profit_factor = (gross_wins / gross_losses) if gross_losses > 0 else (99.0 if gross_wins > 0 else 0.0)

    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

    # Sharpe/Sortino from snapshots
    sharpe = None
    sortino = None
    max_drawdown = 0.0

    if snapshots and len(snapshots) > 1:
        equities = [s.equity for s in snapshots]
        eq_arr = np.array(equities)

        if len(eq_arr) > 1:
            returns = np.diff(eq_arr) / eq_arr[:-1]
            rf_daily = 0.07 / 252.0

            excess = returns - rf_daily
            std = float(np.std(excess))

            if std > 1e-8 and len(returns) >= 5:
                sharpe = round(float(np.mean(excess) / std * np.sqrt(252)), 2)
                downside = excess[excess < 0]
                ds_std = float(np.std(downside)) if len(downside) > 0 else 1e-8
                if ds_std > 1e-8:
                    sortino = round(float(np.mean(excess) / ds_std * np.sqrt(252)), 2)

            peak = np.maximum.accumulate(eq_arr)
            dd = (eq_arr - peak) / peak
            max_drawdown = round(abs(float(np.min(dd))), 6)

    evidence = compute_paper_evidence_label(total_trades)

    result = {
        "total_trades": total_trades,
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "win_rate": round(win_rate, 4),
        "gross_pnl": round(gross_pnl, 2),
        "total_fees": round(total_fees, 2),
        "total_slippage": round(total_slippage, 2),
        "net_pnl": round(net_pnl, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(profit_factor, 2),
        "expectancy": round(expectancy, 2),
        "max_drawdown_pct": max_drawdown,
        "sharpe_ratio": sharpe if sharpe is not None else "INSUFFICIENT_SAMPLE",
        "sortino_ratio": sortino if sortino is not None else "INSUFFICIENT_SAMPLE",
        "evidence_label": evidence,
        "label": "SIMULATED EXECUTION QUALITY",
        "disclaimer": "Paper trading results do not predict future profitability.",
    }

    return result
