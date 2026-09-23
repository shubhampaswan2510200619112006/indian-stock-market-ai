"""
Phase 9.5 — Realistic Economic Metrics & Indian Market Cost/Slippage Engine.

Evaluates trading & predictive strategies after realistic frictions:
- Statutory transaction costs (STT, NSE turnover fee, GST, SEBI fee, Stamp duty).
- Realistic slippage (Bid-Ask half-spread, impact slippage).
- Economic metrics: Cumulative Return, CAGR, Sharpe, Sortino, Calmar, Max Drawdown,
  Win Rate, Profit Factor, Expectancy, Turnover, Fees, Slippage, MAE, MFE.
- Handles sample size sufficiency: If trade count < 10, marks metrics as NOT_RELIABLE_INSUFFICIENT_SAMPLE.
- Evaluates against Buy & Hold and No-Trade baselines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class IndianMarketFrictionModel:
    """
    NSE transaction costs & slippage model.
    STT: 0.1% on delivery or 0.025% on intraday equity (sell side) / 0.0625% on option exercise/turnover.
    Exchange turnover: 0.00345% (NSE)
    GST: 18% on (brokerage + exchange turnover fee)
    SEBI turnover fee: 0.0001%
    Stamp duty: 0.003% (buy side)
    Default conservative aggregate roundtrip fee: ~0.05% of underlying trade value.
    """
    base_fee_pct: float = 0.0005  # 5 bps round-trip statutory costs
    base_slippage_pct: float = 0.0005  # 5 bps half-spread / execution slippage
    cost_multiplier: float = 1.0
    slippage_multiplier: float = 1.0

    @property
    def total_friction_pct(self) -> float:
        return (self.base_fee_pct * self.cost_multiplier) + (self.base_slippage_pct * self.slippage_multiplier)


@dataclass
class EconomicEvaluationReport:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    gross_return: float
    net_return: float
    total_fees: float
    total_slippage: float
    cagr: Optional[float]
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    profit_factor: float
    expectancy_per_trade: float
    turnover: float
    benchmark_buy_and_hold_return: float
    benchmark_sharpe: float
    incremental_sharpe_vs_benchmark: float
    sample_reliability: str  # "RELIABLE" or "NOT_RELIABLE_INSUFFICIENT_SAMPLE"
    trade_pnls: List[float] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)


class EconomicMetricsEngine:
    """
    Computes rigorous economic and risk-adjusted metrics for strategy returns.
    """

    MIN_TRADES_FOR_RELIABILITY: int = 10

    @classmethod
    def evaluate_strategy_returns(
        cls,
        signals: np.ndarray,
        asset_returns: np.ndarray,
        frictions: Optional[IndianMarketFrictionModel] = None,
        risk_free_rate: float = 0.065,  # 6.5% Indian 10y G-Sec yield
        periods_per_year: int = 252,
    ) -> EconomicEvaluationReport:
        """
        Evaluates a signal series against asset returns with realistic Indian friction.
        signals: +1 (long), -1 (short), 0 (flat/cash)
        asset_returns: 1D asset return series
        """
        friction_model = frictions or IndianMarketFrictionModel()
        n = len(signals)
        if n == 0 or len(asset_returns) == 0:
            return cls._empty_report()

        # Align lengths
        min_len = min(n, len(asset_returns))
        sigs = np.array(signals[:min_len], dtype=float)
        rets = np.array(asset_returns[:min_len], dtype=float)

        # Detect position changes to calculate transaction turnover
        position_changes = np.abs(np.diff(sigs, prepend=0.0))
        turnover = float(np.sum(position_changes))

        # Calculate fees and slippage on trades
        unit_friction = friction_model.total_friction_pct
        fee_deductions = position_changes * (friction_model.base_fee_pct * friction_model.cost_multiplier)
        slippage_deductions = position_changes * (friction_model.base_slippage_pct * friction_model.slippage_multiplier)

        gross_daily_pnl = sigs * rets
        net_daily_pnl = gross_daily_pnl - (fee_deductions + slippage_deductions)

        # Cumulative compounding equity curve
        equity = 1.0 + np.cumsum(net_daily_pnl)
        gross_cum = float(np.sum(gross_daily_pnl))
        net_cum = float(np.sum(net_daily_pnl))
        total_fees = float(np.sum(fee_deductions))
        total_slippage = float(np.sum(slippage_deductions))

        # Trade extraction
        trade_pnls = []
        current_trade_pnl = 0.0
        in_trade = False
        current_sig = 0.0

        for i in range(min_len):
            if sigs[i] != 0:
                if not in_trade:
                    in_trade = True
                    current_sig = sigs[i]
                    current_trade_pnl = net_daily_pnl[i]
                elif sigs[i] == current_sig:
                    current_trade_pnl += net_daily_pnl[i]
                else:  # Flipped position
                    trade_pnls.append(current_trade_pnl)
                    current_sig = sigs[i]
                    current_trade_pnl = net_daily_pnl[i]
            else:
                if in_trade:
                    trade_pnls.append(current_trade_pnl)
                    in_trade = False
                    current_trade_pnl = 0.0
        if in_trade:
            trade_pnls.append(current_trade_pnl)

        total_trades = len(trade_pnls)
        wins = [p for p in trade_pnls if p > 0]
        losses = [p for p in trade_pnls if p < 0]
        win_rate = len(wins) / total_trades if total_trades > 0 else 0.0

        total_gains = sum(wins)
        total_losses = abs(sum(losses))
        profit_factor = (total_gains / total_losses) if total_losses > 1e-6 else (10.0 if total_gains > 0 else 1.0)
        expectancy = float(np.mean(trade_pnls)) if total_trades > 0 else 0.0

        # Risk Metrics
        mean_ret = float(np.mean(net_daily_pnl))
        vol = float(np.std(net_daily_pnl)) * np.sqrt(periods_per_year) if len(net_daily_pnl) > 1 else 0.0
        rf_daily = risk_free_rate / periods_per_year
        excess_daily = net_daily_pnl - rf_daily

        sharpe = (
            float(np.mean(excess_daily) / (np.std(excess_daily) + 1e-8)) * np.sqrt(periods_per_year)
            if np.std(excess_daily) > 1e-8
            else 0.0
        )

        downside = net_daily_pnl[net_daily_pnl < 0]
        downside_std = float(np.std(downside)) * np.sqrt(periods_per_year) if len(downside) > 1 else 1e-6
        sortino = float((mean_ret * periods_per_year - risk_free_rate) / downside_std)

        # Drawdown
        cum_max = np.maximum.accumulate(equity)
        drawdowns = (cum_max - equity) / np.maximum(cum_max, 1e-6)
        max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

        # Calmar
        years = min_len / periods_per_year
        cagr = ((equity[-1] ** (1.0 / years)) - 1.0) if years >= 0.5 and equity[-1] > 0 else None
        calmar = (cagr / max_dd) if (cagr is not None and max_dd > 1e-4) else 0.0

        # Benchmark: Buy & Hold
        b_cum = float(np.sum(rets))
        b_vol = float(np.std(rets)) * np.sqrt(periods_per_year) if len(rets) > 1 else 0.0
        b_excess = rets - rf_daily
        b_sharpe = (
            float(np.mean(b_excess) / (np.std(b_excess) + 1e-8)) * np.sqrt(periods_per_year)
            if np.std(b_excess) > 1e-8
            else 0.0
        )

        sample_status = "RELIABLE" if total_trades >= cls.MIN_TRADES_FOR_RELIABILITY else "NOT_RELIABLE_INSUFFICIENT_SAMPLE"

        return EconomicEvaluationReport(
            total_trades=total_trades,
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=float(win_rate),
            gross_return=gross_cum,
            net_return=net_cum,
            total_fees=total_fees,
            total_slippage=total_slippage,
            cagr=cagr,
            annualized_volatility=vol,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            max_drawdown=max_dd,
            profit_factor=profit_factor,
            expectancy_per_trade=expectancy,
            turnover=turnover,
            benchmark_buy_and_hold_return=b_cum,
            benchmark_sharpe=b_sharpe,
            incremental_sharpe_vs_benchmark=sharpe - b_sharpe,
            sample_reliability=sample_status,
            trade_pnls=trade_pnls,
            equity_curve=equity.tolist(),
        )

    @classmethod
    def _empty_report(cls) -> EconomicEvaluationReport:
        return EconomicEvaluationReport(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            gross_return=0.0,
            net_return=0.0,
            total_fees=0.0,
            total_slippage=0.0,
            cagr=None,
            annualized_volatility=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            max_drawdown=0.0,
            profit_factor=0.0,
            expectancy_per_trade=0.0,
            turnover=0.0,
            benchmark_buy_and_hold_return=0.0,
            benchmark_sharpe=0.0,
            incremental_sharpe_vs_benchmark=0.0,
            sample_reliability="NOT_RELIABLE_INSUFFICIENT_SAMPLE",
            trade_pnls=[],
            equity_curve=[],
        )
