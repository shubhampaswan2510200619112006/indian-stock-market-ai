"""
Phase 11 Multiplicity Controller.

Applies formal multiple-testing corrections across the 6 primary hypotheses:
- Nominal significance level: alpha = 0.05
- Bonferroni FWER threshold: alpha / 6 = 0.00833
- Benjamini-Hochberg False Discovery Rate (FDR) q-values
- Enforces strict scientific terminology: false discoveries are controlled under model assumptions, never 'eliminated'.
"""

from __future__ import annotations

from typing import Any, Dict, List


class MultiplicityController:
    """
    Controls family-wise error rate and false discovery rate across Phase 11 hypotheses.
    """

    NOMINAL_ALPHA: float = 0.05
    TOTAL_TESTS: int = 6
    BONFERRONI_ALPHA: float = 0.05 / 6.0  # 0.008333...

    @classmethod
    def apply_multiplicity_corrections(cls, hypothesis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes raw p-values and computes Bonferroni and Benjamini-Hochberg adjusted significance.
        """
        m = len(hypothesis_results)
        # Extract tuples: (hypothesis_id, p_value, net_exp)
        test_items = []
        for h in hypothesis_results:
            hid = h["hypothesis_id"]
            p_val = h["statistical_evaluation"]["p_value"]
            net_exp = h["oos_net_expectancy_bps"]
            test_items.append({
                "hypothesis_id": hid,
                "p_value": p_val,
                "net_expectancy_bps": net_exp,
            })

        # 1. Bonferroni Correction
        bonferroni_survivors = []
        for item in test_items:
            # Must have positive net expectancy AND p_value <= Bonferroni threshold
            is_sig = (item["net_expectancy_bps"] > 0) and (item["p_value"] <= cls.BONFERRONI_ALPHA)
            item["bonferroni_significant"] = is_sig
            item["bonferroni_alpha"] = round(cls.BONFERRONI_ALPHA, 5)
            if is_sig:
                bonferroni_survivors.append(item["hypothesis_id"])

        # 2. Benjamini-Hochberg FDR
        # Sort by p-value ascending
        sorted_items = sorted(test_items, key=lambda x: x["p_value"])
        bh_survivors = []
        for rank, item in enumerate(sorted_items, start=1):
            bh_threshold = (rank / m) * cls.NOMINAL_ALPHA
            item["bh_threshold"] = round(bh_threshold, 5)
            is_bh_sig = (item["net_expectancy_bps"] > 0) and (item["p_value"] <= bh_threshold)
            item["bh_significant"] = is_bh_sig
            if is_bh_sig:
                bh_survivors.append(item["hypothesis_id"])

        any_survived = len(bonferroni_survivors) > 0

        verdict_statement = (
            "NO_STATISTICAL_CLAIM_SURVIVED_MULTIPLICITY_ADJUSTMENT"
            if not any_survived
            else f"{len(bonferroni_survivors)} HYPOTHESIS_SURVIVED_MULTIPLICITY_ADJUSTMENT"
        )

        return {
            "total_primary_hypotheses": m,
            "nominal_alpha": cls.NOMINAL_ALPHA,
            "bonferroni_alpha": round(cls.BONFERRONI_ALPHA, 5),
            "bonferroni_survivors_count": len(bonferroni_survivors),
            "bonferroni_survivors": bonferroni_survivors,
            "bh_survivors_count": len(bh_survivors),
            "bh_survivors": bh_survivors,
            "verdict_statement": verdict_statement,
            "adjusted_tests": test_items,
        }
