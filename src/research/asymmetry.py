"""
Phase 9.6 — Research Question E: Long/Short Asymmetry Analysis.

Investigates whether prediction quality and trading expectancy differ systematically
between Long and Short signals:
- Evaluates Symmetric Long/Short vs Long-Only vs Short-Only.
- Measures win rate, gross return, statutory fees, slippage, and net return per side.
- Quantifies impact of secular equity drift and short-sale transaction drag.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.ml.economic_metrics import EconomicEvaluationReport, EconomicMetricsEngine, IndianMarketFrictionModel


@dataclass
class SidePerformanceReport:
    side_name: str
    total_trades: int
    win_rate: float
    gross_return: float
    fees: float
    slippage: float
    net_return: float
    sharpe_ratio: float
    max_drawdown: float
    expectancy_per_trade: float
    sample_reliability: str


@dataclass
class AsymmetryInvestigationSummary:
    symmetric_report: SidePerformanceReport
    long_only_report: SidePerformanceReport
    short_only_report: SidePerformanceReport
    is_long_superior: bool
    asymmetry_conclusion: str


class LongShortAsymmetryEngine:
    """
    Analyzes performance differences between long-side and short-side signals.
    """

    @classmethod
    def evaluate_asymmetry(
        cls,
        signals: np.ndarray,
        asset_returns: np.ndarray,
        friction_model: Optional[IndianMarketFrictionModel] = None,
    ) -> AsymmetryInvestigationSummary:
        friction = friction_model or IndianMarketFrictionModel()
        n = min(len(signals), len(asset_returns))
        sigs = signals[:n]
        rets = asset_returns[:n]

        # 1. Symmetric (+1 and -1)
        sym_econ = EconomicMetricsEngine.evaluate_strategy_returns(sigs, rets, frictions=friction)
        sym_rep = SidePerformanceReport(
            side_name="Symmetric_Long_Short",
            total_trades=sym_econ.total_trades,
            win_rate=sym_econ.win_rate,
            gross_return=sym_econ.gross_return,
            fees=sym_econ.total_fees,
            slippage=sym_econ.total_slippage,
            net_return=sym_econ.net_return,
            sharpe_ratio=sym_econ.sharpe_ratio,
            max_drawdown=sym_econ.max_drawdown,
            expectancy_per_trade=sym_econ.expectancy_per_trade,
            sample_reliability=sym_econ.sample_reliability,
        )

        # 2. Long Only (+1 kept, -1 mapped to 0)
        long_sigs = np.where(sigs > 0, 1.0, 0.0)
        long_econ = EconomicMetricsEngine.evaluate_strategy_returns(long_sigs, rets, frictions=friction)
        long_rep = SidePerformanceReport(
            side_name="Long_Only",
            total_trades=long_econ.total_trades,
            win_rate=long_econ.win_rate,
            gross_return=long_econ.gross_return,
            fees=long_econ.total_fees,
            slippage=long_econ.total_slippage,
            net_return=long_econ.net_return,
            sharpe_ratio=long_econ.sharpe_ratio,
            max_drawdown=long_econ.max_drawdown,
            expectancy_per_trade=long_econ.expectancy_per_trade,
            sample_reliability=long_econ.sample_reliability,
        )

        # 3. Short Only (-1 kept, +1 mapped to 0)
        short_sigs = np.where(sigs < 0, -1.0, 0.0)
        short_econ = EconomicMetricsEngine.evaluate_strategy_returns(short_sigs, rets, frictions=friction)
        short_rep = SidePerformanceReport(
            side_name="Short_Only",
            total_trades=short_econ.total_trades,
            win_rate=short_econ.win_rate,
            gross_return=short_econ.gross_return,
            fees=short_econ.total_fees,
            slippage=short_econ.total_slippage,
            net_return=short_econ.net_return,
            sharpe_ratio=short_econ.sharpe_ratio,
            max_drawdown=short_econ.max_drawdown,
            expectancy_per_trade=short_econ.expectancy_per_trade,
            sample_reliability=short_econ.sample_reliability,
        )

        long_sup = long_rep.net_return > short_rep.net_return
        if long_rep.net_return > 0 and short_rep.net_return <= 0:
            conclusion = "STRUCTURAL_LONG_ASYMMETRY: Long signals achieve positive net expectancy while short signals suffer severe losses due to index upward drift."
        elif long_sup:
            conclusion = "MODERATE_LONG_SUPERIORITY: Long signals lose less capital than short signals, but neither side achieves robust positive net alpha after costs."
        else:
            conclusion = "SHORT_SIDE_SUPERIORITY: Short signals outperformed long signals over this specific sample period."

        return AsymmetryInvestigationSummary(
            symmetric_report=sym_rep,
            long_only_report=long_rep,
            short_only_report=short_rep,
            is_long_superior=long_sup,
            asymmetry_conclusion=conclusion,
        )
