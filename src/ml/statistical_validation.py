"""
Statistical Validation Engine (Phase 6.5).
Calculates Block Bootstrap Confidence Intervals and Permutation Tests.
Explicitly documents resampling parameters, dependence assumptions, and null hypotheses.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


@dataclass
class BootstrapResult:
    metric_name: str
    mean_estimate: float
    ci_lower: float
    ci_upper: float
    confidence_level: float
    bootstrap_iterations: int
    resampling_unit: str
    random_seed: int
    dependence_disclaimer: str


@dataclass
class PermutationTestResult:
    metric_name: str
    observed_value: float
    null_mean: float
    p_value: float
    permutations: int
    null_hypothesis: str


def compute_block_bootstrap_ci(
    values: np.ndarray,
    metric_func=np.mean,
    n_iterations: int = 1000,
    confidence_level: float = 0.95,
    block_size: int = 3,
    random_seed: int = 42,
    metric_name: str = "Metric",
) -> BootstrapResult:
    """
    Computes Block Bootstrap 95% Confidence Interval for time-dependent financial metrics.
    """
    disclaimer = (
        "BOOTSTRAP LIMITATION: Block bootstrap accounts for short-term serial dependence, "
        "but time-series financial observations are non-IID and non-stationary. "
        "Bootstrap CIs indicate sample variability, NOT proof of future statistical edge."
    )

    if len(values) < 5:
        return BootstrapResult(
            metric_name=metric_name,
            mean_estimate=float(np.mean(values)) if len(values) > 0 else 0.0,
            ci_lower=0.0,
            ci_upper=0.0,
            confidence_level=confidence_level,
            bootstrap_iterations=n_iterations,
            resampling_unit=f"Block size = {block_size}",
            random_seed=random_seed,
            dependence_disclaimer="STATISTICAL_TESTING_LIMITED_BY_SAMPLE_SIZE",
        )

    rng = np.random.RandomState(random_seed)
    n = len(values)
    bootstrap_estimates = []

    # Block bootstrap sampling
    num_blocks_needed = int(np.ceil(n / block_size))
    for _ in range(n_iterations):
        block_starts = rng.randint(0, max(1, n - block_size + 1), size=num_blocks_needed)
        sample = []
        for start in block_starts:
            sample.extend(values[start : start + block_size])
        sample = np.array(sample[:n])
        bootstrap_estimates.append(metric_func(sample))

    alpha = 1.0 - confidence_level
    ci_lower = float(np.percentile(bootstrap_estimates, alpha / 2.0 * 100.0))
    ci_upper = float(np.percentile(bootstrap_estimates, (1.0 - alpha / 2.0) * 100.0))

    return BootstrapResult(
        metric_name=metric_name,
        mean_estimate=float(np.mean(values)),
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        confidence_level=confidence_level,
        bootstrap_iterations=n_iterations,
        resampling_unit=f"Block (size={block_size})",
        random_seed=random_seed,
        dependence_disclaimer=disclaimer,
    )


def compute_permutation_test(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_permutations: int = 1000,
    random_seed: int = 42,
    metric_name: str = "Accuracy",
) -> PermutationTestResult:
    """
    Permutation Test evaluating H0: Model predictions have no relationship with target outcomes.
    """
    null_hypothesis = f"H0: Model {metric_name} is no better than random label permutation."
    if len(y_true) < 5:
        return PermutationTestResult(
            metric_name=metric_name,
            observed_value=0.0,
            null_mean=0.5,
            p_value=1.0,
            permutations=n_permutations,
            null_hypothesis=null_hypothesis + " (LIMITED_BY_SAMPLE_SIZE)",
        )

    observed_metric = float(np.mean(y_true == y_pred))
    rng = np.random.RandomState(random_seed)
    null_metrics = []

    for _ in range(n_permutations):
        permuted_y = rng.permutation(y_true)
        null_metrics.append(np.mean(permuted_y == y_pred))

    null_metrics = np.array(null_metrics)
    null_mean = float(np.mean(null_metrics))
    p_val = float(np.mean(null_metrics >= observed_metric))

    return PermutationTestResult(
        metric_name=metric_name,
        observed_value=observed_metric,
        null_mean=null_mean,
        p_value=p_val,
        permutations=n_permutations,
        null_hypothesis=null_hypothesis,
    )
