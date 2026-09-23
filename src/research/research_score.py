"""
Phase 9.6 — Transparent 100-Point Research Score & Shortlist Engine.

Calculates an objective research ranking score out of 100:
- OOS Robustness: 20 pts
- Statistical Evidence: 20 pts
- Economic Significance: 15 pts
- Cost Robustness: 10 pts
- Regime Robustness: 10 pts
- Data Quality: 10 pts
- Reproducibility: 5 pts
- Baseline Improvement: 10 pts

Non-Negotiable Rule: The 100-point score is a ranking aid ONLY.
It does NOT determine the Phase 10 Gate or final verdict by itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ResearchScoreBreakdown:
    hypothesis_id: str
    oos_robustness_pts: float  # / 20
    statistical_evidence_pts: float  # / 20
    economic_significance_pts: float  # / 15
    cost_robustness_pts: float  # / 10
    regime_robustness_pts: float  # / 10
    data_quality_pts: float  # / 10
    reproducibility_pts: float  # / 5
    baseline_improvement_pts: float  # / 10
    total_score: float  # / 100
    is_shortlist_candidate: bool
    disqualification_reasons: List[str] = field(default_factory=list)


class ResearchScoreEngine:
    """
    Computes transparent research scores and filters top 3 surviving hypotheses.
    """

    MIN_SCORE_FOR_SHORTLIST: float = 65.0

    @classmethod
    def calculate_score(
        cls,
        hypothesis_id: str,
        oos_accuracy: float,
        baseline_accuracy: float,
        sample_size: int,
        net_sharpe: float,
        cost_robust: bool,
        multi_regime_robust: bool,
        has_bid_ask_quotes: bool,
        is_reproducible: bool,
        p_value_proxy: float = 0.50,
    ) -> ResearchScoreBreakdown:
        disqualifications = []

        # 1. OOS Robustness (max 20)
        acc_delta = oos_accuracy - baseline_accuracy
        if acc_delta > 0.05:
            oos_pts = 20.0
        elif acc_delta > 0.02:
            oos_pts = 14.0
        elif acc_delta > 0.0:
            oos_pts = 8.0
        else:
            oos_pts = 2.0
            disqualifications.append("Fails to beat baseline out-of-sample")

        # 2. Statistical Evidence (max 20)
        if sample_size >= 100 and p_value_proxy < 0.05:
            stat_pts = 20.0
        elif sample_size >= 60 and p_value_proxy < 0.15:
            stat_pts = 14.0
        elif sample_size >= 30:
            stat_pts = 8.0
        else:
            stat_pts = 3.0
            disqualifications.append("Insufficient sample size")

        # 3. Economic Significance (max 15)
        if net_sharpe > 1.0:
            econ_pts = 15.0
        elif net_sharpe > 0.5:
            econ_pts = 10.0
        elif net_sharpe > 0.0:
            econ_pts = 5.0
        else:
            econ_pts = 0.0
            disqualifications.append("Negative net Sharpe after transaction costs")

        # 4. Cost Robustness (max 10)
        cost_pts = 10.0 if cost_robust else 1.0
        if not cost_robust:
            disqualifications.append("Fragile to realistic transaction costs and slippage")

        # 5. Regime Robustness (max 10)
        regime_pts = 10.0 if multi_regime_robust else 2.0

        # 6. Data Quality (max 10)
        data_pts = 10.0 if has_bid_ask_quotes else 5.0  # Bhavcopy settlement gets 5/10

        # 7. Reproducibility (max 5)
        repro_pts = 5.0 if is_reproducible else 0.0

        # 8. Baseline Improvement (max 10)
        base_imp_pts = 10.0 if acc_delta > 0.03 else (5.0 if acc_delta > 0 else 0.0)

        total = oos_pts + stat_pts + econ_pts + cost_pts + regime_pts + data_pts + repro_pts + base_imp_pts
        is_candidate = (total >= cls.MIN_SCORE_FOR_SHORTLIST) and (len(disqualifications) == 0)

        return ResearchScoreBreakdown(
            hypothesis_id=hypothesis_id,
            oos_robustness_pts=oos_pts,
            statistical_evidence_pts=stat_pts,
            economic_significance_pts=econ_pts,
            cost_robustness_pts=cost_pts,
            regime_robustness_pts=regime_pts,
            data_quality_pts=data_pts,
            reproducibility_pts=repro_pts,
            baseline_improvement_pts=base_imp_pts,
            total_score=total,
            is_shortlist_candidate=is_candidate,
            disqualification_reasons=disqualifications,
        )

    @classmethod
    def filter_top_shortlist(
        cls,
        scores: List[ResearchScoreBreakdown],
        max_items: int = 3,
    ) -> List[ResearchScoreBreakdown]:
        """
        Sorts candidates by total_score descending and selects at most max_items (top 3).
        Only candidates meeting shortlist criteria survive; otherwise empty list returned.
        """
        candidates = [s for s in scores if s.is_shortlist_candidate]
        candidates.sort(key=lambda x: x.total_score, reverse=True)
        return candidates[:max_items]
