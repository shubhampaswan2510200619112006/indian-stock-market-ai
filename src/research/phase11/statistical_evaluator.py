"""
Phase 11 Statistical Evaluator.

Per Methodology Correction 5:
- Resamples: BOOTSTRAP_RESAMPLES = 1000, SEED = 42
- Stationary block bootstrap to account for time-series autocorrelation
- Primary block length = 5 (matching 5-day holding period)
- Predefined sensitivity check across block lengths: 3, 5, 10
- Computes 95% bootstrap confidence interval and one-sided p-value for H0: Net Expectancy <= 0
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Tuple

import numpy as np

BOOTSTRAP_RESAMPLES: int = 1000
SEED: int = 42
PRIMARY_BLOCK_LENGTH: int = 5


@dataclass
class BootstrapResult:
    mean_bps: float
    ci_lower_bps: float
    ci_upper_bps: float
    sharpe_mean: float
    sharpe_ci_lower: float
    sharpe_ci_upper: float
    p_value: float
    bootstrap_method: str
    block_length: int
    resamples: int
    seed: int
    sensitivity_checks: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StatisticalEvaluator:
    """
    Computes rigorous stationary block bootstrap statistics.
    """

    @classmethod
    def run_stationary_block_bootstrap(
        cls,
        net_spreads_bps: List[float],
        holding_days: int = 5,
        block_length: int = PRIMARY_BLOCK_LENGTH,
        resamples: int = BOOTSTRAP_RESAMPLES,
        seed: int = SEED,
    ) -> BootstrapResult:
        """
        Runs stationary block bootstrap on OOS net spreads.
        """
        arr = np.array(net_spreads_bps)
        n = len(arr)
        if n < 5:
            return BootstrapResult(
                mean_bps=float(np.mean(arr)) if n > 0 else 0.0,
                ci_lower_bps=0.0,
                ci_upper_bps=0.0,
                sharpe_mean=0.0,
                sharpe_ci_lower=0.0,
                sharpe_ci_upper=0.0,
                p_value=1.0,
                bootstrap_method="INSUFFICIENT_SAMPLE",
                block_length=block_length,
                resamples=resamples,
                seed=seed,
                sensitivity_checks={},
            )

        rng = np.random.default_rng(seed)
        p_geom = 1.0 / block_length  # Probability for geometric block distribution

        boot_means = np.empty(resamples)
        boot_sharpes = np.empty(resamples)
        periods_per_year = 252.0 / holding_days

        for b in range(resamples):
            # Stationary block bootstrap indices
            indices = []
            curr_idx = rng.integers(0, n)
            while len(indices) < n:
                indices.append(curr_idx)
                if rng.random() < p_geom:
                    curr_idx = rng.integers(0, n)
                else:
                    curr_idx = (curr_idx + 1) % n

            sample = arr[indices]
            m = np.mean(sample)
            s = np.std(sample, ddof=1)
            boot_means[b] = m
            ann_ret = m * periods_per_year
            ann_vol = s * np.sqrt(periods_per_year)
            boot_sharpes[b] = (ann_ret / ann_vol) if ann_vol > 1e-6 else 0.0

        ci_lower = float(np.percentile(boot_means, 2.5))
        ci_upper = float(np.percentile(boot_means, 97.5))
        sharpe_lower = float(np.percentile(boot_sharpes, 2.5))
        sharpe_upper = float(np.percentile(boot_sharpes, 97.5))

        # Empirical one-sided p-value: proportion of bootstrap means <= 0
        p_val = float(np.mean(boot_means <= 0.0))

        # Sensitivity check to block lengths 3 and 10
        sensitivity = {}
        for test_bl in [3, 10]:
            p_geom_test = 1.0 / test_bl
            test_means = np.empty(resamples)
            for b in range(resamples):
                indices = []
                curr_idx = rng.integers(0, n)
                while len(indices) < n:
                    indices.append(curr_idx)
                    if rng.random() < p_geom_test:
                        curr_idx = rng.integers(0, n)
                    else:
                        curr_idx = (curr_idx + 1) % n
                test_means[b] = np.mean(arr[indices])
            sensitivity[f"block_length_{test_bl}"] = {
                "ci_lower_bps": round(float(np.percentile(test_means, 2.5)), 2),
                "ci_upper_bps": round(float(np.percentile(test_means, 97.5)), 2),
                "p_value": round(float(np.mean(test_means <= 0.0)), 4),
            }

        return BootstrapResult(
            mean_bps=round(float(np.mean(arr)), 2),
            ci_lower_bps=round(ci_lower, 2),
            ci_upper_bps=round(ci_upper, 2),
            sharpe_mean=round(float(np.mean(boot_sharpes)), 2),
            sharpe_ci_lower=round(sharpe_lower, 2),
            sharpe_ci_upper=round(sharpe_upper, 2),
            p_value=round(p_val, 4),
            bootstrap_method="STATIONARY_BLOCK_BOOTSTRAP",
            block_length=block_length,
            resamples=resamples,
            seed=seed,
            sensitivity_checks=sensitivity,
        )
