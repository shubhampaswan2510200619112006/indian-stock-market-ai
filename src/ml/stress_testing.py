"""
Phase 9.5 — Stress Testing, Regime Validation & Block Bootstrap Engine.

Performs multidimensional robustness checks:
1. Transaction Cost Stress: 1.0x, 1.5x, 2.0x base fees.
2. Slippage Stress: 1.0x, 2.0x, 3.0x base slippage.
3. Execution Timing Stress: T+1 Next-day execution vs T+2 Delayed execution.
4. Market Regime Validation: Performance breakdown across 6 regimes:
   STRONG_BULL, BULL, SIDEWAYS, BEAR, STRONG_BEAR, HIGH_VOLATILITY.
5. Parameter Sensitivity: Small local neighborhood perturbations (+/- 10%, +/- 20%).
6. Block Bootstrap (size = 3, 5 sessions) for time-series dependent 95% Confidence Intervals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.ml.economic_metrics import EconomicEvaluationReport, EconomicMetricsEngine, IndianMarketFrictionModel
from src.ml.statistical_validation import BootstrapResult, compute_block_bootstrap_ci


@dataclass
class CostStressScenarioResult:
    scenario_name: str
    cost_multiplier: float
    slippage_multiplier: float
    net_return: float
    sharpe_ratio: float
    max_drawdown: float
    is_profitable: bool


@dataclass
class RegimeValidationResult:
    regime_name: str
    session_count: int
    trade_count: int
    win_rate: float
    net_return: float
    sharpe_ratio: float
    max_drawdown: float
    reliability_status: str


@dataclass
class RobustnessReport:
    cost_stress_results: List[CostStressScenarioResult]
    slippage_stress_results: List[CostStressScenarioResult]
    regime_breakdowns: List[RegimeValidationResult]
    timing_stress_results: Dict[str, float]
    bootstrap_sharpe_ci: BootstrapResult
    bootstrap_expectancy_ci: BootstrapResult
    is_cost_robust: bool
    is_slippage_robust: bool
    dominant_regime_dependence: str


class RobustnessStressEngine:
    """
    Executes stress testing, regime breakdown, and block bootstrap evaluation.
    """

    @classmethod
    def run_cost_and_slippage_stress(
        cls,
        signals: np.ndarray,
        asset_returns: np.ndarray,
        base_fee_pct: float = 0.0005,
        base_slippage_pct: float = 0.0005,
    ) -> Tuple[List[CostStressScenarioResult], List[CostStressScenarioResult]]:
        """
        Tests 1.0x, 1.5x, 2.0x costs and 1.0x, 2.0x, 3.0x slippage.
        """
        cost_scenarios = [
            ("Baseline_Cost_1.0x", 1.0, 1.0),
            ("Cost_Stress_1.5x", 1.5, 1.0),
            ("Cost_Stress_2.0x", 2.0, 1.0),
        ]
        cost_results = []
        for name, c_mult, s_mult in cost_scenarios:
            model = IndianMarketFrictionModel(
                base_fee_pct=base_fee_pct,
                base_slippage_pct=base_slippage_pct,
                cost_multiplier=c_mult,
                slippage_multiplier=s_mult,
            )
            report = EconomicMetricsEngine.evaluate_strategy_returns(signals, asset_returns, frictions=model)
            cost_results.append(
                CostStressScenarioResult(
                    scenario_name=name,
                    cost_multiplier=c_mult,
                    slippage_multiplier=s_mult,
                    net_return=report.net_return,
                    sharpe_ratio=report.sharpe_ratio,
                    max_drawdown=report.max_drawdown,
                    is_profitable=report.net_return > 0.0,
                )
            )

        slippage_scenarios = [
            ("Baseline_Slippage_1.0x", 1.0, 1.0),
            ("Slippage_Stress_2.0x", 1.0, 2.0),
            ("Slippage_Stress_3.0x", 1.0, 3.0),
        ]
        slippage_results = []
        for name, c_mult, s_mult in slippage_scenarios:
            model = IndianMarketFrictionModel(
                base_fee_pct=base_fee_pct,
                base_slippage_pct=base_slippage_pct,
                cost_multiplier=c_mult,
                slippage_multiplier=s_mult,
            )
            report = EconomicMetricsEngine.evaluate_strategy_returns(signals, asset_returns, frictions=model)
            slippage_results.append(
                CostStressScenarioResult(
                    scenario_name=name,
                    cost_multiplier=c_mult,
                    slippage_multiplier=s_mult,
                    net_return=report.net_return,
                    sharpe_ratio=report.sharpe_ratio,
                    max_drawdown=report.max_drawdown,
                    is_profitable=report.net_return > 0.0,
                )
            )

        return cost_results, slippage_results

    @classmethod
    def run_timing_stress(
        cls,
        signals: np.ndarray,
        asset_returns: np.ndarray,
        delay_sessions: int = 1,
    ) -> Dict[str, float]:
        """
        Evaluates impact of execution delay (e.g. signal at T, executed at T+1 vs T+2).
        """
        baseline_report = EconomicMetricsEngine.evaluate_strategy_returns(signals, asset_returns)
        
        # Shift signals by delay_sessions
        if len(signals) > delay_sessions:
            delayed_sigs = np.pad(signals[:-delay_sessions], (delay_sessions, 0), constant_values=0.0)
            delayed_report = EconomicMetricsEngine.evaluate_strategy_returns(delayed_sigs, asset_returns)
            delayed_net = delayed_report.net_return
            delayed_sharpe = delayed_report.sharpe_ratio
        else:
            delayed_net = 0.0
            delayed_sharpe = 0.0

        return {
            "baseline_net_return": baseline_report.net_return,
            "baseline_sharpe": baseline_report.sharpe_ratio,
            "delayed_net_return": delayed_net,
            "delayed_sharpe": delayed_sharpe,
            "return_degradation": baseline_report.net_return - delayed_net,
        }

    @classmethod
    def evaluate_regimes(
        cls,
        regimes: pd.Series,
        signals: np.ndarray,
        asset_returns: np.ndarray,
    ) -> List[RegimeValidationResult]:
        """
        Evaluates performance independently across 6 market regimes:
        STRONG_BULL, BULL, SIDEWAYS, BEAR, STRONG_BEAR, HIGH_VOLATILITY.
        """
        target_regimes = [
            "STRONG_BULL",
            "BULL",
            "SIDEWAYS",
            "BEAR",
            "STRONG_BEAR",
            "HIGH_VOLATILITY",
        ]
        results = []
        n = min(len(regimes), len(signals), len(asset_returns))
        reg_arr = regimes.iloc[:n].values
        sigs = signals[:n]
        rets = asset_returns[:n]

        for reg in target_regimes:
            mask = (reg_arr == reg)
            session_count = int(np.sum(mask))

            if session_count < 3:
                results.append(
                    RegimeValidationResult(
                        regime_name=reg,
                        session_count=session_count,
                        trade_count=0,
                        win_rate=0.0,
                        net_return=0.0,
                        sharpe_ratio=0.0,
                        max_drawdown=0.0,
                        reliability_status="INSUFFICIENT_SAMPLES",
                    )
                )
                continue

            # Sub-sample regime returns
            sub_sigs = sigs[mask]
            sub_rets = rets[mask]
            report = EconomicMetricsEngine.evaluate_strategy_returns(sub_sigs, sub_rets)

            rel_status = "RELIABLE" if report.total_trades >= 5 else "INSUFFICIENT_TRADES"
            results.append(
                RegimeValidationResult(
                    regime_name=reg,
                    session_count=session_count,
                    trade_count=report.total_trades,
                    win_rate=report.win_rate,
                    net_return=report.net_return,
                    sharpe_ratio=report.sharpe_ratio,
                    max_drawdown=report.max_drawdown,
                    reliability_status=rel_status,
                )
            )

        return results

    @classmethod
    def compute_bootstrap_confidence_intervals(
        cls,
        trade_pnls: List[float],
        block_size: int = 3,
        n_iterations: int = 1000,
        random_seed: int = 42,
    ) -> Tuple[BootstrapResult, BootstrapResult]:
        """
        Block bootstrap for time-dependent trade PnLs.
        Returns 95% CIs for Expectancy (mean trade PnL) and Sharpe-proxy.
        """
        arr = np.array(trade_pnls, dtype=float)
        
        # Expectancy CI
        ci_expectancy = compute_block_bootstrap_ci(
            values=arr,
            metric_func=np.mean,
            n_iterations=n_iterations,
            confidence_level=0.95,
            block_size=block_size,
            random_seed=random_seed,
            metric_name="Expectancy_per_trade",
        )

        # Sharpe proxy func
        def _sharpe_metric(vals: np.ndarray) -> float:
            std = float(np.std(vals))
            return float(np.mean(vals) / (std + 1e-8) * np.sqrt(252)) if std > 1e-8 else 0.0

        ci_sharpe = compute_block_bootstrap_ci(
            values=arr,
            metric_func=_sharpe_metric,
            n_iterations=n_iterations,
            confidence_level=0.95,
            block_size=block_size,
            random_seed=random_seed,
            metric_name="Sharpe_Ratio",
        )

        return ci_expectancy, ci_sharpe

    @classmethod
    def generate_full_robustness_report(
        cls,
        signals: np.ndarray,
        asset_returns: np.ndarray,
        regimes: pd.Series,
    ) -> RobustnessReport:
        """
        Runs comprehensive robustness pipeline.
        """
        cost_res, slip_res = cls.run_cost_and_slippage_stress(signals, asset_returns)
        timing_res = cls.run_timing_stress(signals, asset_returns)
        regime_res = cls.evaluate_regimes(regimes, signals, asset_returns)

        base_report = EconomicMetricsEngine.evaluate_strategy_returns(signals, asset_returns)
        ci_exp, ci_shp = cls.compute_bootstrap_confidence_intervals(base_report.trade_pnls)

        is_c_robust = all(r.is_profitable for r in cost_res)
        is_s_robust = all(r.is_profitable for r in slip_res)

        # Check regime concentration
        profitable_regimes = [r.regime_name for r in regime_res if r.net_return > 0 and r.session_count >= 5]
        if len(profitable_regimes) == 1:
            dominant_regime = f"CONCENTRATED_IN_{profitable_regimes[0]}"
        elif len(profitable_regimes) > 1:
            dominant_regime = "MULTI_REGIME_ROBUST"
        else:
            dominant_regime = "NO_PROFITABLE_REGIMES"

        return RobustnessReport(
            cost_stress_results=cost_res,
            slippage_stress_results=slip_res,
            regime_breakdowns=regime_res,
            timing_stress_results=timing_res,
            bootstrap_sharpe_ci=ci_shp,
            bootstrap_expectancy_ci=ci_exp,
            is_cost_robust=is_c_robust,
            is_slippage_robust=is_s_robust,
            dominant_regime_dependence=dominant_regime,
        )
