"""
Phase 16 — Multiple Testing Correction Infrastructure.

Standalone statistical utility module. This module provides correction methods
for multiple testing problems (familywise error rate and false discovery rate).

IMPORTANT CONSTRAINTS:
- This is generic statistical infrastructure ONLY.
- It does NOT initiate a new research cycle.
- It does NOT add new hypotheses.
- It does NOT unlock Phase 15 research.
- It does NOT modify the existing hypothesis registry or frozen results.
- It preserves existing statistical methodology and terminology.

Usage: Import and use as a utility. The existing research framework
calls this independently if/when a research cycle is initiated.

References:
- Bonferroni: Bonferroni (1936) — controls familywise error rate (FWER)
- Benjamini-Hochberg: Benjamini & Hochberg (1995) — controls false discovery rate (FDR)
  DOI: 10.1111/j.2517-6161.1995.tb02031.x
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Sequence, Tuple

import numpy as np


# =============================================================================
# Correction method enum
# =============================================================================

class CorrectionMethod(str, Enum):
    BONFERRONI = "BONFERRONI"
    BENJAMINI_HOCHBERG = "BENJAMINI_HOCHBERG"
    NONE = "NONE"


# =============================================================================
# Result types
# =============================================================================

@dataclass
class CorrectedPValue:
    """Result for a single hypothesis after multiple-testing correction."""
    hypothesis_index: int
    hypothesis_id: str
    raw_p_value: float
    adjusted_p_value: float
    rejected: bool        # True if H0 rejected at corrected threshold
    correction_method: CorrectionMethod
    alpha_used: float
    rank: Optional[int] = None   # For BH: rank used in correction


@dataclass
class MultipleTestingReport:
    """
    Report from a multiple-testing correction run.

    Does NOT draw investment or trading conclusions.
    Statistical significance ≠ practical significance or profitability.
    """
    method: CorrectionMethod
    alpha: float
    total_hypotheses: int
    rejected_count: int
    corrected_results: List[CorrectedPValue] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def rejection_rate(self) -> float:
        if self.total_hypotheses == 0:
            return 0.0
        return self.rejected_count / self.total_hypotheses

    def get_rejected_ids(self) -> List[str]:
        return [r.hypothesis_id for r in self.corrected_results if r.rejected]

    def get_not_rejected_ids(self) -> List[str]:
        return [r.hypothesis_id for r in self.corrected_results if not r.rejected]


# =============================================================================
# Correction functions
# =============================================================================

def apply_bonferroni(
    p_values: Sequence[float],
    hypothesis_ids: Optional[Sequence[str]] = None,
    alpha: float = 0.05,
) -> MultipleTestingReport:
    """
    Apply Bonferroni correction to a set of p-values.

    Controls familywise error rate (FWER) at level alpha.
    Adjusted threshold per test: alpha / m (where m = number of tests).

    Pros: Conservative, controls FWER.
    Cons: Low power when many tests are correlated.

    Args:
        p_values: Observed p-values (one per hypothesis).
        hypothesis_ids: Optional string identifiers. Defaults to '0','1','2',...
        alpha: Target FWER level (default 0.05).

    Returns:
        MultipleTestingReport with per-hypothesis adjusted p-values and rejection decisions.
    """
    n = len(p_values)
    if n == 0:
        return MultipleTestingReport(
            method=CorrectionMethod.BONFERRONI,
            alpha=alpha,
            total_hypotheses=0,
            rejected_count=0,
            notes=["No p-values provided."],
        )

    ids = list(hypothesis_ids) if hypothesis_ids else [str(i) for i in range(n)]
    if len(ids) != n:
        raise ValueError(f"hypothesis_ids length ({len(ids)}) must match p_values length ({n})")

    bonferroni_threshold = alpha / n
    results = []
    for i, (p, hid) in enumerate(zip(p_values, ids)):
        # Bonferroni adjusted p-value: min(p * m, 1.0)
        adj_p = min(float(p) * n, 1.0)
        rejected = float(p) <= bonferroni_threshold
        results.append(CorrectedPValue(
            hypothesis_index=i,
            hypothesis_id=hid,
            raw_p_value=float(p),
            adjusted_p_value=adj_p,
            rejected=rejected,
            correction_method=CorrectionMethod.BONFERRONI,
            alpha_used=alpha,
        ))

    rejected_count = sum(1 for r in results if r.rejected)
    return MultipleTestingReport(
        method=CorrectionMethod.BONFERRONI,
        alpha=alpha,
        total_hypotheses=n,
        rejected_count=rejected_count,
        corrected_results=results,
        notes=[
            f"Bonferroni threshold: {bonferroni_threshold:.6f} (alpha={alpha}/m={n})",
            "FWER controlled at level alpha.",
            "Note: Statistical significance does not imply profitability or trading edge.",
        ],
    )


def apply_benjamini_hochberg(
    p_values: Sequence[float],
    hypothesis_ids: Optional[Sequence[str]] = None,
    alpha: float = 0.05,
) -> MultipleTestingReport:
    """
    Apply Benjamini-Hochberg (BH) procedure for False Discovery Rate (FDR) control.

    Controls FDR at level alpha, i.e., the expected proportion of false discoveries
    among all rejected hypotheses.

    Less conservative than Bonferroni; appropriate when testing many hypotheses
    with some expected to be true positives.

    Reference: Benjamini & Hochberg (1995), JRSS-B 57(1):289–300.

    Args:
        p_values: Observed p-values (one per hypothesis).
        hypothesis_ids: Optional string identifiers.
        alpha: Target FDR level (default 0.05).

    Returns:
        MultipleTestingReport with per-hypothesis BH-adjusted p-values and decisions.
    """
    n = len(p_values)
    if n == 0:
        return MultipleTestingReport(
            method=CorrectionMethod.BENJAMINI_HOCHBERG,
            alpha=alpha,
            total_hypotheses=0,
            rejected_count=0,
            notes=["No p-values provided."],
        )

    ids = list(hypothesis_ids) if hypothesis_ids else [str(i) for i in range(n)]
    if len(ids) != n:
        raise ValueError(f"hypothesis_ids length ({len(ids)}) must match p_values length ({n})")

    # Sort p-values ascending with original indices
    p_array = np.array([float(p) for p in p_values])
    sorted_indices = np.argsort(p_array)
    sorted_p = p_array[sorted_indices]

    # BH thresholds: k/m * alpha for rank k (1-indexed)
    ranks = np.arange(1, n + 1)
    bh_thresholds = (ranks / n) * alpha

    # Find the largest k where p_{(k)} <= k/m * alpha
    below = sorted_p <= bh_thresholds
    if below.any():
        max_rank = int(np.max(ranks[below]))
    else:
        max_rank = 0

    # All hypotheses with rank <= max_rank are rejected
    rejected_set = set(sorted_indices[:max_rank])

    # BH adjusted p-values (Benjamini-Hochberg step-up adjusted p-values)
    # p_adj_{(k)} = min_{j >= k} (m / j * p_{(j)})
    # Computed from largest rank down
    bh_adjusted = (n / ranks) * sorted_p
    # Take cumulative minimum from right
    bh_adjusted_min = np.minimum.accumulate(bh_adjusted[::-1])[::-1]
    bh_adjusted_clipped = np.minimum(bh_adjusted_min, 1.0)

    # Map back to original order
    adj_p_by_original = np.empty(n)
    for new_idx, orig_idx in enumerate(sorted_indices):
        adj_p_by_original[orig_idx] = bh_adjusted_clipped[new_idx]

    results = []
    for i, (p, hid) in enumerate(zip(p_values, ids)):
        # Find rank in sorted order
        rank_in_sorted = int(np.where(sorted_indices == i)[0][0]) + 1
        rejected = i in rejected_set
        results.append(CorrectedPValue(
            hypothesis_index=i,
            hypothesis_id=hid,
            raw_p_value=float(p),
            adjusted_p_value=float(adj_p_by_original[i]),
            rejected=rejected,
            correction_method=CorrectionMethod.BENJAMINI_HOCHBERG,
            alpha_used=alpha,
            rank=rank_in_sorted,
        ))

    rejected_count = sum(1 for r in results if r.rejected)
    return MultipleTestingReport(
        method=CorrectionMethod.BENJAMINI_HOCHBERG,
        alpha=alpha,
        total_hypotheses=n,
        rejected_count=rejected_count,
        corrected_results=results,
        notes=[
            f"BH FDR controlled at level alpha={alpha}.",
            f"Max rejection rank: {max_rank}/{n}.",
            "Reference: Benjamini & Hochberg (1995), JRSS-B 57(1):289–300.",
            "Note: Statistical significance does not imply profitability or trading edge.",
        ],
    )


def correct_p_values(
    p_values: Sequence[float],
    hypothesis_ids: Optional[Sequence[str]] = None,
    method: CorrectionMethod = CorrectionMethod.BENJAMINI_HOCHBERG,
    alpha: float = 0.05,
) -> MultipleTestingReport:
    """
    Apply multiple-testing correction using the specified method.

    Args:
        p_values: Raw p-values from hypothesis tests.
        hypothesis_ids: Optional identifiers for each hypothesis.
        method: Correction method (BONFERRONI or BENJAMINI_HOCHBERG).
        alpha: Significance level.

    Returns:
        MultipleTestingReport.
    """
    if method == CorrectionMethod.BONFERRONI:
        return apply_bonferroni(p_values, hypothesis_ids, alpha)
    elif method == CorrectionMethod.BENJAMINI_HOCHBERG:
        return apply_benjamini_hochberg(p_values, hypothesis_ids, alpha)
    elif method == CorrectionMethod.NONE:
        # No correction — return raw p-values with naive threshold
        n = len(p_values)
        ids = list(hypothesis_ids) if hypothesis_ids else [str(i) for i in range(n)]
        results = [
            CorrectedPValue(
                hypothesis_index=i,
                hypothesis_id=hid,
                raw_p_value=float(p),
                adjusted_p_value=float(p),
                rejected=float(p) <= alpha,
                correction_method=CorrectionMethod.NONE,
                alpha_used=alpha,
            )
            for i, (p, hid) in enumerate(zip(p_values, ids))
        ]
        return MultipleTestingReport(
            method=CorrectionMethod.NONE,
            alpha=alpha,
            total_hypotheses=n,
            rejected_count=sum(1 for r in results if r.rejected),
            corrected_results=results,
            notes=["No multiple-testing correction applied."],
        )
    else:
        raise ValueError(f"Unknown correction method: {method}")
