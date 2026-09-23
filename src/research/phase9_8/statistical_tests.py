"""
Phase 9.8 — Statistical Robustness, Block Bootstrap & Permutation Testing Engine.

Provides:
- Stationary Block Bootstrap: Resamples serially correlated returns preserving autocorrelation.
  * Block length = 3 sessions (or documented equivalent).
  * Iterations = 1,000 | Seed = 42.
  * Reports effective sample size N_eff = N / block_length.
  * 95% Bootstrap Confidence Interval for Sharpe and Expectancy.
- Permutation Test: Randomly shuffles returns relative to signals to establish empirical p-value.
- Enforces precise scientific language: A CI spanning zero indicates insufficient evidence,
  not proof of zero edge.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


@dataclass
class BootstrapAnalysisResult:
    metric_name: str
    observed_value: float
    ci_lower_95: float
    ci_upper_95: float
    resampling_method: str
    block_length: int
    bootstrap_iterations: int
    random_seed: int
    original_sample_size: int
    effective_sample_size: int
    spans_zero: bool
    verdict: str


@dataclass
class PermutationTestResult:
    observed_mean_return: float
    permutation_p_value: float
    iterations: int
    random_seed: int
    is_statistically_significant: bool
    verdict: str


class Phase98StatisticalEngine:
    """
    Executes block bootstrap and permutation testing with documented effective sample info.
    """

    @classmethod
    def calculate_block_bootstrap(
        cls,
        returns: np.ndarray,
        block_length: int = 3,
        iterations: int = 1000,
        random_seed: int = 42,
        annualization_factor: float = 15.8745,  # sqrt(252)
    ) -> BootstrapAnalysisResult:
        rng = np.random.default_rng(random_seed)
        n = len(returns)

        if n < 10:
            return BootstrapAnalysisResult(
                metric_name="annualized_sharpe",
                observed_value=0.0,
                ci_lower_95=0.0,
                ci_upper_95=0.0,
                resampling_method="STATIONARY_BLOCK_BOOTSTRAP",
                block_length=block_length,
                bootstrap_iterations=iterations,
                random_seed=random_seed,
                original_sample_size=n,
                effective_sample_size=n,
                spans_zero=True,
                verdict="INSUFFICIENT_SAMPLE_SIZE",
            )

        def calc_sharpe(r: np.ndarray) -> float:
            m = np.mean(r)
            s = np.std(r)
            return float((m * annualization_factor) / (s + 1e-8)) if s > 1e-8 else 0.0

        obs_val = calc_sharpe(returns)
        boot_metrics = []
        n_blocks = int(np.ceil(n / block_length))

        for _ in range(iterations):
            starts = rng.integers(0, max(1, n - block_length + 1), size=n_blocks)
            sampled = []
            for s in starts:
                sampled.extend(returns[s : s + block_length])
            resampled_arr = np.array(sampled[:n])
            boot_metrics.append(calc_sharpe(resampled_arr))

        ci_low = float(np.percentile(boot_metrics, 2.5))
        ci_high = float(np.percentile(boot_metrics, 97.5))
        eff_n = max(1, int(n / block_length))
        spans_zero = (ci_low <= 0.0 <= ci_high)

        verdict = (
            "Confidence interval spans zero: insufficient evidence of a persistent directional edge in the tested setup."
            if spans_zero
            else "Confidence interval strictly positive: statistically defensible edge detected."
        )

        return BootstrapAnalysisResult(
            metric_name="annualized_sharpe",
            observed_value=obs_val,
            ci_lower_95=ci_low,
            ci_upper_95=ci_high,
            resampling_method="STATIONARY_BLOCK_BOOTSTRAP",
            block_length=block_length,
            bootstrap_iterations=iterations,
            random_seed=random_seed,
            original_sample_size=n,
            effective_sample_size=eff_n,
            spans_zero=spans_zero,
            verdict=verdict,
        )

    @classmethod
    def run_permutation_test(
        cls,
        signals: np.ndarray,
        returns: np.ndarray,
        iterations: int = 1000,
        random_seed: int = 42,
    ) -> PermutationTestResult:
        rng = np.random.default_rng(random_seed)
        n = min(len(signals), len(returns))
        sigs = signals[:n]
        rets = returns[:n]

        obs_mean = float(np.mean(sigs * rets))
        perm_means = []

        for _ in range(iterations):
            perm_rets = rng.permutation(rets)
            perm_means.append(float(np.mean(sigs * perm_rets)))

        perm_means = np.array(perm_means)
        p_val = float(np.mean(np.abs(perm_means) >= abs(obs_mean)))
        is_sig = (p_val < 0.05) and (obs_mean > 0)

        verdict = (
            f"Observed return mean {obs_mean:.4f} is statistically significant (p={p_val:.4f})."
            if is_sig
            else f"Observed return mean {obs_mean:.4f} is consistent with null random permutation (p={p_val:.4f})."
        )

        return PermutationTestResult(
            observed_mean_return=obs_mean,
            permutation_p_value=p_val,
            iterations=iterations,
            random_seed=random_seed,
            is_statistically_significant=is_sig,
            verdict=verdict,
        )
