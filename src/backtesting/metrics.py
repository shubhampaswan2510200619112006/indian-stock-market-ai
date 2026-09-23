"""
Quantitative Performance Metrics Engine.

Calculates:
- Return, CAGR
- Win rate, Expectancy, Profit factor
- Max drawdown, Sharpe, Sortino, Calmar
- MAE (Max Adverse Excursion), MFE (Max Favorable Excursion)
- Sample size gating
"""

from __future__ import annotations

import math
from typing import List
import numpy as np

from src.backtesting.models import ExecutedTrade, PerformanceMetrics, PortfolioSnapshot


def calculate_performance_metrics(
    trades: List[ExecutedTrade],
    equity_curve: List[PortfolioSnapshot],
    initial_equity: float,
    min_sample_size: int = 10,
) -> PerformanceMetrics:
    """
    Computes statistical and quantitative risk/return metrics from executed trades and equity snapshots.
    """
    if not trades:
        return PerformanceMetrics(sample_size_sufficient=False)

    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t.net_pnl > 0)
    losing_trades = sum(1 for t in trades if t.net_pnl <= 0)
    win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

    gross_pnl = sum(t.gross_pnl for t in trades)
    total_costs = sum(t.total_costs for t in trades)
    net_pnl = sum(t.net_pnl for t in trades)

    # Wins / Losses averages
    wins = [t.net_pnl for t in trades if t.net_pnl > 0]
    losses = [abs(t.net_pnl) for t in trades if t.net_pnl < 0]

    avg_win = float(np.mean(wins)) if wins else 0.0
    avg_loss = float(np.mean(losses)) if losses else 0.0
    
    # Expectancy = (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
    loss_rate = 1.0 - win_rate
    expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

    # Profit Factor = Gross Wins / Gross Losses
    gross_wins = sum(wins)
    gross_losses = sum(losses)
    profit_factor = (gross_wins / gross_losses) if gross_losses > 0 else (99.0 if gross_wins > 0 else 0.0)

    # Holding period
    holding_days = [t.holding_days for t in trades]
    avg_holding_days = float(np.mean(holding_days)) if holding_days else 0.0

    # MAE / MFE
    maes = [t.max_adverse_excursion for t in trades]
    mfes = [t.max_favorable_excursion for t in trades]
    avg_mae = float(np.mean(maes)) if maes else 0.0
    avg_mfe = float(np.mean(mfes)) if mfes else 0.0

    # Equity Curve Metrics
    if equity_curve and len(equity_curve) > 1:
        equities = [s.equity for s in equity_curve]
        total_return_pct = (equities[-1] - initial_equity) / initial_equity

        # Calculate daily returns
        eq_arr = np.array(equities)
        daily_returns = np.diff(eq_arr) / eq_arr[:-1]

        # CAGR calculation
        days_span = max(1, (equity_curve[-1].timestamp - equity_curve[0].timestamp).days)
        years = days_span / 365.25
        if years > 0 and equities[-1] > 0:
            cagr_pct = ((equities[-1] / initial_equity) ** (1.0 / years)) - 1.0
        else:
            cagr_pct = 0.0

        # Maximum Drawdown
        peak = np.maximum.accumulate(eq_arr)
        drawdowns = (eq_arr - peak) / peak
        max_drawdown_pct = abs(float(np.min(drawdowns)))

        # Sharpe & Sortino
        rf_daily = 0.07 / 252.0  # 7% annual risk-free rate
        excess_returns = daily_returns - rf_daily
        ret_std = float(np.std(excess_returns))

        if ret_std > 1e-8:
            sharpe_ratio = float(np.mean(excess_returns) / ret_std * np.sqrt(252))
        else:
            sharpe_ratio = 0.0

        downside_returns = excess_returns[excess_returns < 0]
        downside_std = float(np.std(downside_returns)) if len(downside_returns) > 0 else 1e-8
        if downside_std > 1e-8:
            sortino_ratio = float(np.mean(excess_returns) / downside_std * np.sqrt(252))
        else:
            sortino_ratio = 0.0

        # Calmar Ratio = CAGR / Max Drawdown
        calmar_ratio = (cagr_pct / max_drawdown_pct) if max_drawdown_pct > 1e-6 else 0.0

    else:
        total_return_pct = net_pnl / initial_equity
        cagr_pct = 0.0
        max_drawdown_pct = 0.0
        sharpe_ratio = 0.0
        sortino_ratio = 0.0
        calmar_ratio = 0.0

    sample_size_sufficient = total_trades >= min_sample_size

    return PerformanceMetrics(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=round(win_rate, 4),
        gross_pnl=round(gross_pnl, 2),
        total_costs=round(total_costs, 2),
        net_pnl=round(net_pnl, 2),
        total_return_pct=round(total_return_pct, 4),
        cagr_pct=round(cagr_pct, 4),
        avg_win=round(avg_win, 2),
        avg_loss=round(avg_loss, 2),
        expectancy=round(expectancy, 2),
        profit_factor=round(profit_factor, 2),
        max_drawdown_pct=round(max_drawdown_pct, 4),
        sharpe_ratio=round(sharpe_ratio, 2),
        sortino_ratio=round(sortino_ratio, 2),
        calmar_ratio=round(calmar_ratio, 2),
        avg_holding_days=round(avg_holding_days, 1),
        max_adverse_excursion_avg=round(avg_mae, 2),
        max_favorable_excursion_avg=round(avg_mfe, 2),
        sample_size_sufficient=sample_size_sufficient,
    )
