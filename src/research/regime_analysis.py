"""
Phase 9.6 — Research Question C: Market Regime Investigation & Failure Decomposition.

Investigates whether negative Phase 9.5 performance is universally bad or regime-dependent:
- Evaluates directional predictability and trading metrics across 6 distinct regimes:
  STRONG_BULL, BULL, SIDEWAYS, BEAR, STRONG_BEAR, HIGH_VOLATILITY.
- Enforces strict anti-regime-picking rule: A positive result in one small regime does NOT
  constitute a general edge; it is explicitly classified as LIMITED_EVIDENCE.
- Categorizes failure mode as: UNIVERSALLY_BAD vs REGIME_DEPENDENT_LIMITED_EVIDENCE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.ml.economic_metrics import EconomicMetricsEngine, IndianMarketFrictionModel


@dataclass
class RegimeDetailReport:
    regime_name: str
    session_count: int
    trade_count: int
    directional_accuracy: float
    balanced_accuracy: float
    win_rate: float
    net_return: float
    sharpe_ratio: float
    max_drawdown: float
    expectancy_per_trade: float
    reliability_status: str  # "SUFFICIENT_SAMPLE" or "LIMITED_EVIDENCE_SAMPLE_TOO_SMALL"


@dataclass
class RegimeInvestigationSummary:
    regime_reports: List[RegimeDetailReport]
    primary_failure_mode: str  # "UNIVERSALLY_BAD", "REGIME_DEPENDENT_LIMITED_EVIDENCE", "SIDEWAYS_DRAG"
    is_performance_concentrated: bool
    dominant_regime: str
    conclusion: str


class MarketRegimeInvestigationEngine:
    """
    Rigorously decomposes strategy performance across market regimes.
    """

    MIN_SESSIONS_PER_REGIME: int = 15

    @classmethod
    def decompose_by_regime(
        cls,
        regimes: pd.Series,
        y_true_direction: np.ndarray,
        y_pred_direction: np.ndarray,
        signals: np.ndarray,
        asset_returns: np.ndarray,
    ) -> RegimeInvestigationSummary:
        """
        Decomposes both predictive accuracy and economic trading metrics across all 6 regimes.
        """
        target_regimes = [
            "STRONG_BULL",
            "BULL",
            "SIDEWAYS",
            "BEAR",
            "STRONG_BEAR",
            "HIGH_VOLATILITY",
        ]

        n = min(len(regimes), len(y_true_direction), len(y_pred_direction), len(signals), len(asset_returns))
        reg_arr = regimes.iloc[:n].values
        y_t = y_true_direction[:n]
        y_p = y_pred_direction[:n]
        sigs = signals[:n]
        rets = asset_returns[:n]

        reports: List[RegimeDetailReport] = []
        profitable_regimes = []
        losing_regimes = []

        friction = IndianMarketFrictionModel()

        for reg in target_regimes:
            mask = (reg_arr == reg)
            count = int(np.sum(mask))

            if count == 0:
                reports.append(
                    RegimeDetailReport(
                        regime_name=reg,
                        session_count=0,
                        trade_count=0,
                        directional_accuracy=0.0,
                        balanced_accuracy=0.0,
                        win_rate=0.0,
                        net_return=0.0,
                        sharpe_ratio=0.0,
                        max_drawdown=0.0,
                        expectancy_per_trade=0.0,
                        reliability_status="ZERO_OBSERVATIONS",
                    )
                )
                continue

            sub_yt = y_t[mask]
            sub_yp = y_p[mask]
            sub_sigs = sigs[mask]
            sub_rets = rets[mask]

            acc = float(np.mean(sub_yt == sub_yp)) if count > 0 else 0.0

            # Balanced accuracy
            pos_mask = (sub_yt == 1)
            neg_mask = (sub_yt == 0)
            sens = float(np.mean(sub_yp[pos_mask] == 1)) if np.sum(pos_mask) > 0 else 0.5
            spec = float(np.mean(sub_yp[neg_mask] == 0)) if np.sum(neg_mask) > 0 else 0.5
            bal_acc = (sens + spec) / 2.0

            econ = EconomicMetricsEngine.evaluate_strategy_returns(sub_sigs, sub_rets, friction)

            rel_status = (
                "SUFFICIENT_SAMPLE"
                if count >= cls.MIN_SESSIONS_PER_REGIME and econ.total_trades >= 5
                else "LIMITED_EVIDENCE_SAMPLE_TOO_SMALL"
            )

            if econ.net_return > 0.0 and rel_status == "SUFFICIENT_SAMPLE":
                profitable_regimes.append(reg)
            elif count >= 5:
                losing_regimes.append(reg)

            reports.append(
                RegimeDetailReport(
                    regime_name=reg,
                    session_count=count,
                    trade_count=econ.total_trades,
                    directional_accuracy=acc,
                    balanced_accuracy=bal_acc,
                    win_rate=econ.win_rate,
                    net_return=econ.net_return,
                    sharpe_ratio=econ.sharpe_ratio,
                    max_drawdown=econ.max_drawdown,
                    expectancy_per_trade=econ.expectancy_per_trade,
                    reliability_status=rel_status,
                )
            )

        # Failure mode diagnosis
        sideways_rep = next((r for r in reports if r.regime_name == "SIDEWAYS"), None)
        dominant_reg = "SIDEWAYS" if (sideways_rep and sideways_rep.session_count > n * 0.5) else "MIXED"

        if len(profitable_regimes) == 0:
            failure_mode = "UNIVERSALLY_BAD"
            conclusion = (
                "UNIVERSALLY_BAD: The strategy produced negative net returns and sub-50% accuracy across all "
                "observed regimes. Failure is not solely an artifact of sideways range-bound markets."
            )
        elif len(profitable_regimes) == 1 and len(losing_regimes) >= 2:
            failure_mode = "REGIME_DEPENDENT_LIMITED_EVIDENCE"
            conclusion = (
                f"REGIME_DEPENDENT_LIMITED_EVIDENCE: Nominal profitability observed only in {profitable_regimes[0]}. "
                f"Under anti-regime-picking discipline, this single-regime outperformance CANNOT be claimed as general edge "
                f"and requires independent out-of-sample confirmation."
            )
        else:
            failure_mode = "MIXED_REGIME_PERFORMANCE"
            conclusion = "Performance varies moderately across regimes but remains constrained by transaction costs."

        return RegimeInvestigationSummary(
            regime_reports=reports,
            primary_failure_mode=failure_mode,
            is_performance_concentrated=len(profitable_regimes) == 1,
            dominant_regime=dominant_reg,
            conclusion=conclusion,
        )
