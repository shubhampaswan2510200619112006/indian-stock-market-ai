"""
Dual Data Coverage & Statistical Evidence Evaluator (Phase 6.5).
Separates physical database volume (Data Coverage) from sample independence and fold stability (Statistical Evidence).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class MLDataCoverageStatus(str, Enum):
    INSUFFICIENT = "INSUFFICIENT"
    LIMITED = "LIMITED"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class MLStatisticalEvidenceStatus(str, Enum):
    INSUFFICIENT = "INSUFFICIENT"
    LIMITED = "LIMITED"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


@dataclass
class DualSufficiencyResult:
    data_coverage_status: MLDataCoverageStatus
    statistical_evidence_status: MLStatisticalEvidenceStatus
    total_observations: int
    trading_days_count: int
    contracts_count: int
    underlyings_count: int
    expiries_count: int
    independent_oos_trades: int
    total_walk_forward_folds: int
    fold_consistency_ratio: float
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = ""

    def is_usable_for_preliminary_research(self) -> bool:
        return self.data_coverage_status in [
            MLDataCoverageStatus.LIMITED,
            MLDataCoverageStatus.MODERATE,
            MLDataCoverageStatus.STRONG,
        ]


def evaluate_dual_sufficiency(
    total_observations: int,
    trading_days_count: int,
    contracts_count: int,
    underlyings_count: int,
    expiries_count: int,
    independent_oos_trades: int,
    total_walk_forward_folds: int,
    fold_consistency_ratio: float,
) -> DualSufficiencyResult:
    """
    Evaluates both Data Coverage Status and Statistical Evidence Status.
    Enforces rule: High quote volume does NOT automatically yield STRONG statistical evidence.
    """
    reasons: List[str] = []
    warnings: List[str] = []

    # 1. Evaluate Data Coverage Status
    if total_observations < 500 or trading_days_count < 15:
        cov_status = MLDataCoverageStatus.INSUFFICIENT
        reasons.append(f"Data Coverage INSUFFICIENT ({total_observations} quotes across {trading_days_count} days).")
    elif total_observations < 10000 or trading_days_count < 250:
        cov_status = MLDataCoverageStatus.LIMITED
        reasons.append(f"Data Coverage LIMITED ({total_observations} quotes, {trading_days_count} days, {underlyings_count} symbol(s)).")
    elif total_observations < 50000 or trading_days_count < 500 or underlyings_count < 2:
        cov_status = MLDataCoverageStatus.MODERATE
        reasons.append(f"Data Coverage MODERATE ({total_observations} quotes across {trading_days_count} days).")
    else:
        cov_status = MLDataCoverageStatus.STRONG
        reasons.append(f"Data Coverage STRONG ({total_observations} quotes, {trading_days_count} days, {underlyings_count} symbols).")

    # 2. Evaluate Statistical Evidence Status
    if independent_oos_trades < 5 or total_walk_forward_folds < 3:
        stat_status = MLStatisticalEvidenceStatus.INSUFFICIENT
        warnings.append(
            f"Statistical Evidence INSUFFICIENT ({independent_oos_trades} independent OOS trades across {total_walk_forward_folds} folds). "
            "Sample size is statistically inadequate for edge conclusions."
        )
    elif independent_oos_trades < 25 or fold_consistency_ratio < 0.50:
        stat_status = MLStatisticalEvidenceStatus.LIMITED
        warnings.append(
            f"Statistical Evidence LIMITED ({independent_oos_trades} OOS trades, fold consistency = {fold_consistency_ratio * 100:.1f}%). "
            "Highly correlated samples prevent strong statistical claims."
        )
    elif independent_oos_trades < 100 or fold_consistency_ratio < 0.70:
        stat_status = MLStatisticalEvidenceStatus.MODERATE
        reasons.append(f"Statistical Evidence MODERATE ({independent_oos_trades} independent trades across folds).")
    else:
        stat_status = MLStatisticalEvidenceStatus.STRONG
        reasons.append(f"Statistical Evidence STRONG ({independent_oos_trades} trades with high fold consistency).")

    disclaimer = (
        "CRITICAL DISCLAIMER: Positive historical P&L or large quote counts do NOT prove future profitability, "
        "production readiness, or statistical significance. All outputs are preliminary research measurements."
    )

    return DualSufficiencyResult(
        data_coverage_status=cov_status,
        statistical_evidence_status=stat_status,
        total_observations=total_observations,
        trading_days_count=trading_days_count,
        contracts_count=contracts_count,
        underlyings_count=underlyings_count,
        expiries_count=expiries_count,
        independent_oos_trades=independent_oos_trades,
        total_walk_forward_folds=total_walk_forward_folds,
        fold_consistency_ratio=fold_consistency_ratio,
        reasons=reasons,
        warnings=warnings,
        disclaimer=disclaimer,
    )
