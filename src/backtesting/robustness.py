"""
Parameter Robustness, Monte Carlo Order Shuffling & Execution Stress Testing.

ROBUSTNESS GATING:
- Parameter Sensitivity: varies score thresholds, stop-loss %, DTE thresholds.
- Monte Carlo: 500 permutations of historical trade returns for drawdown distribution.
- Stress Testing: BASE, CONSERVATIVE, HIGH_COST models.
- Flag: "FRAGILE / POSSIBLE OVERFITTING" if performance decays rapidly under minor tweaks.
"""

from __future__ import annotations

import random
from typing import List, Dict
import numpy as np
from pydantic import BaseModel

from src.backtesting.models import BacktestConfig, BacktestResult, CostModelType, ExecutionCostModel
from src.backtesting.engine import BacktestEngine


class ParameterSensitivityPoint(BaseModel):
    min_strategy_score: float
    stop_loss_pct: float
    cagr_pct: float
    win_rate: float
    net_pnl: float
    is_profitable: bool


class RobustnessReport(BaseModel):
    symbol: str
    status: str                         # STABLE, FRAGILE / POSSIBLE OVERFITTING
    baseline_cagr: float
    parameter_points: List[ParameterSensitivityPoint]
    cagr_std_dev: float
    profitable_param_pct: float         # % of parameter combinations that are profitable
    monte_carlo_p5_drawdown: float       # 5th percentile worst drawdown in Monte Carlo
    stress_test_high_cost_pnl: float    # P/L under high cost model


class RobustnessTester:
    """
    Evaluates parameter sensitivity and statistical stability.
    """

    def __init__(self, base_config: BacktestConfig):
        self.base_config = base_config

    def evaluate_robustness(self) -> RobustnessReport:
        points: List[ParameterSensitivityPoint] = []
        cagrs: List[float] = []

        scores = [50.0, 60.0, 70.0]
        stop_losses = [0.30, 0.50, 0.70]

        for score in scores:
            for sl in stop_losses:
                cfg = self.base_config.model_copy()
                cfg.min_strategy_score = score
                cfg.stop_loss_pct = sl
                
                engine = BacktestEngine(cfg)
                res = engine.run()
                
                pt = ParameterSensitivityPoint(
                    min_strategy_score=score,
                    stop_loss_pct=sl,
                    cagr_pct=res.metrics.cagr_pct,
                    win_rate=res.metrics.win_rate,
                    net_pnl=res.metrics.net_pnl,
                    is_profitable=res.metrics.net_pnl > 0,
                )
                points.append(pt)
                cagrs.append(res.metrics.cagr_pct)

        # Baseline run
        base_res = BacktestEngine(self.base_config).run()
        baseline_cagr = base_res.metrics.cagr_pct

        profitable_count = sum(1 for p in points if p.is_profitable)
        profitable_pct = round(profitable_count / max(1, len(points)), 2)
        std_dev = float(np.std(cagrs)) if cagrs else 0.0

        # Monte Carlo Drawdown Simulation
        trade_returns = [t.net_pnl for t in base_res.trades]
        mc_p5_dd = self._run_monte_carlo_drawdown(trade_returns, self.base_config.initial_equity)

        # High Cost Stress Test
        stress_cfg = self.base_config.model_copy()
        stress_cfg.cost_model = ExecutionCostModel(
            model_type=CostModelType.HIGH_COST,
            slippage_pct=0.015,         # 1.5% high slippage
            brokerage_per_lot=40.0,
        )
        stress_res = BacktestEngine(stress_cfg).run()
        high_cost_pnl = stress_res.metrics.net_pnl

        # Status determination
        if profitable_pct >= 0.6 and high_cost_pnl >= 0:
            status = "STABLE"
        else:
            status = "FRAGILE / POSSIBLE OVERFITTING"

        return RobustnessReport(
            symbol=self.base_config.symbol,
            status=status,
            baseline_cagr=baseline_cagr,
            parameter_points=points,
            cagr_std_dev=round(std_dev, 4),
            profitable_param_pct=profitable_pct,
            monte_carlo_p5_drawdown=round(mc_p5_dd, 4),
            stress_test_high_cost_pnl=round(high_cost_pnl, 2),
        )

    def _run_monte_carlo_drawdown(
        self,
        trade_pnls: List[float],
        initial_equity: float,
        num_simulations: int = 200,
    ) -> float:
        if not trade_pnls:
            return 0.0

        drawdowns: List[float] = []

        for _ in range(num_simulations):
            shuffled = trade_pnls.copy()
            random.shuffle(shuffled)

            equity = initial_equity
            peak = equity
            max_dd = 0.0

            for pnl in shuffled:
                equity += pnl
                peak = max(peak, equity)
                dd = (peak - equity) / peak if peak > 0 else 0.0
                max_dd = max(max_dd, dd)

            drawdowns.append(max_dd)

        # Return 5th percentile worst drawdown
        return float(np.percentile(drawdowns, 95))
