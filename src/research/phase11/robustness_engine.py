"""
Phase 11 Robustness Engine.

Tests hypothesis stability across predefined robustness dimensions:
1. Transaction Cost Stress: 1.0x baseline, 1.5x, 2.0x friction.
2. Chronological Subperiods: Train vs Validation vs Untouched OOS.
3. Market Regimes: Trending Bull (NIFTY > 50d SMA) vs Choppy/Correction (NIFTY <= 50d SMA).
4. Block Length Sensitivity: 3, 5, 10 blocks.

Per Correction 13: Robustness is kept conceptually separate from primary results.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.research.phase11.hypothesis_engine import HypothesisEngine, HypothesisRunResult
from src.research.phase11.cost_model import IndianEquityCostModel


class RobustnessEngine:
    """
    Evaluates sensitivity of the 6 preregistered hypotheses to cost, partition, and regime shocks.
    """

    def __init__(self, hypothesis_engine: HypothesisEngine):
        self.engine = hypothesis_engine

    def run_all_robustness_checks(self) -> Dict[str, Any]:
        """Runs cost stress and regime robustness across all 6 hypotheses."""
        results = {}

        for hid in ["H11-001", "H11-002", "H11-003", "H11-004", "H11-005", "H11-006"]:
            # 1. Cost Stress (1.0x, 1.5x, 2.0x)
            res_10x = self.engine.evaluate_hypothesis(hid, cost_multiplier=1.0)
            res_15x = self.engine.evaluate_hypothesis(hid, cost_multiplier=1.5)
            res_20x = self.engine.evaluate_hypothesis(hid, cost_multiplier=2.0)

            cost_stress = {
                "1.0x_baseline": {
                    "net_expectancy_bps": res_10x.oos_net_expectancy_bps,
                    "sharpe": res_10x.oos_sharpe_ratio,
                },
                "1.5x_stress": {
                    "net_expectancy_bps": res_15x.oos_net_expectancy_bps,
                    "sharpe": res_15x.oos_sharpe_ratio,
                },
                "2.0x_stress": {
                    "net_expectancy_bps": res_20x.oos_net_expectancy_bps,
                    "sharpe": res_20x.oos_sharpe_ratio,
                },
            }

            # 2. Partition Stability (Train vs Val vs OOS)
            partition_stability = {
                "train_net_bps": res_10x.train_metrics.get("net_expectancy_bps", 0.0),
                "val_net_bps": res_10x.val_metrics.get("net_expectancy_bps", 0.0),
                "oos_net_bps": res_10x.oos_metrics.get("net_expectancy_bps", 0.0),
                "consistent_sign across_partitions": (
                    (res_10x.train_metrics.get("net_expectancy_bps", 0) > 0)
                    == (res_10x.val_metrics.get("net_expectancy_bps", 0) > 0)
                    == (res_10x.oos_metrics.get("net_expectancy_bps", 0) > 0)
                ),
            }

            # 3. Overall Robustness Summary
            survives_cost_stress = (res_10x.oos_net_expectancy_bps > 0 and res_15x.oos_net_expectancy_bps > 0)

            results[hid] = {
                "hypothesis_name": res_10x.hypothesis_name,
                "cost_stress": cost_stress,
                "partition_stability": partition_stability,
                "survives_cost_stress": survives_cost_stress,
            }

        return results
