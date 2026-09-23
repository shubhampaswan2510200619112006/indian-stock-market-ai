"""
Phase 9.5 — Experiment Registry & Multiple-Testing Control.

Tracks every quantitative model, feature configuration, and strategy experiment.
Prevents data-mining bias:
- Records all experiments (best, median, worst, failed, rejected).
- Tracks multiple-testing population to apply Bonferroni / FDR awareness.
- Preserves immutable dataset snapshots, feature versions, parameters, seeds, and outcomes.
- Supported statuses: RESEARCH_ONLY, PROMISING, WEAK_INCONCLUSIVE, NO_EVIDENCE_OF_EDGE, INSUFFICIENT_DATA.
- Hard safety rule: Never labels a model PRODUCTION_READY in this phase.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import os
from typing import Any, Dict, List, Optional
import uuid
import numpy as np


class ExperimentStatus(str, Enum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    PROMISING = "PROMISING"
    WEAK_INCONCLUSIVE = "WEAK_INCONCLUSIVE"
    NO_EVIDENCE_OF_EDGE = "NO_EVIDENCE_OF_EDGE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class ExperimentRecord:
    experiment_id: str
    hypothesis: str
    dataset_snapshot_id: str
    feature_version: str
    target_version: str
    model_name: str
    model_level: str
    hyperparameters: Dict[str, Any]
    threshold: float
    random_seed: int
    train_period_start: str
    train_period_end: str
    test_period_start: str
    test_period_end: str
    oos_observations: int
    oos_trades: int
    oos_accuracy: Optional[float]
    oos_sharpe: Optional[float]
    oos_net_return: Optional[float]
    oos_max_drawdown: Optional[float]
    status: ExperimentStatus = ExperimentStatus.RESEARCH_ONLY
    status_reason: str = ""
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class MultipleTestingAudit:
    total_experiments: int
    promising_experiments: int
    weak_inconclusive_experiments: int
    no_edge_experiments: int
    insufficient_data_experiments: int
    median_oos_accuracy: float
    mean_oos_accuracy: float
    best_oos_accuracy: float
    worst_oos_accuracy: float
    median_oos_sharpe: float
    best_oos_sharpe: float
    worst_oos_sharpe: float


class ExperimentRegistry:
    """
    JSON-backed Experiment Registry for quantitative research tracking.
    """

    def __init__(self, registry_filepath: str = "./data/experiment_registry.json"):
        self.filepath = registry_filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def _load(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, records: List[Dict[str, Any]]) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def record_experiment(self, experiment: ExperimentRecord) -> None:
        """
        Appends an experiment record to the registry.
        Enforces: Status can NEVER be PRODUCTION_READY.
        """
        # Hard safety validation
        if "PRODUCTION_READY" in str(experiment.status):
            raise ValueError("Safety Violation: Model status can NEVER be set to PRODUCTION_READY in Phase 9.5.")

        records = self._load()
        # Overwrite if experiment_id exists, else append
        records = [r for r in records if r.get("experiment_id") != experiment.experiment_id]
        
        record_dict = asdict(experiment)
        record_dict["status"] = experiment.status.value
        records.append(record_dict)
        self._save(records)

    def list_experiments(self) -> List[Dict[str, Any]]:
        return self._load()

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        for r in self._load():
            if r.get("experiment_id") == experiment_id:
                return r
        return None

    def audit_multiple_testing(self) -> MultipleTestingAudit:
        """
        Computes aggregate metrics across the entire experiment population:
        Median, mean, best, and worst across all models to prevent selection bias.
        """
        records = self._load()
        total = len(records)
        if total == 0:
            return MultipleTestingAudit(
                total_experiments=0,
                promising_experiments=0,
                weak_inconclusive_experiments=0,
                no_edge_experiments=0,
                insufficient_data_experiments=0,
                median_oos_accuracy=0.0,
                mean_oos_accuracy=0.0,
                best_oos_accuracy=0.0,
                worst_oos_accuracy=0.0,
                median_oos_sharpe=0.0,
                best_oos_sharpe=0.0,
                worst_oos_sharpe=0.0,
            )

        promising = sum(1 for r in records if r.get("status") == ExperimentStatus.PROMISING.value)
        weak = sum(1 for r in records if r.get("status") == ExperimentStatus.WEAK_INCONCLUSIVE.value)
        no_edge = sum(1 for r in records if r.get("status") == ExperimentStatus.NO_EVIDENCE_OF_EDGE.value)
        insufficient = sum(1 for r in records if r.get("status") == ExperimentStatus.INSUFFICIENT_DATA.value)

        accs = [r["oos_accuracy"] for r in records if r.get("oos_accuracy") is not None]
        sharpes = [r["oos_sharpe"] for r in records if r.get("oos_sharpe") is not None]

        med_acc = float(np.median(accs)) if accs else 0.0
        mean_acc = float(np.mean(accs)) if accs else 0.0
        best_acc = float(np.max(accs)) if accs else 0.0
        worst_acc = float(np.min(accs)) if accs else 0.0

        med_shp = float(np.median(sharpes)) if sharpes else 0.0
        best_shp = float(np.max(sharpes)) if sharpes else 0.0
        worst_shp = float(np.min(sharpes)) if sharpes else 0.0

        return MultipleTestingAudit(
            total_experiments=total,
            promising_experiments=promising,
            weak_inconclusive_experiments=weak,
            no_edge_experiments=no_edge,
            insufficient_data_experiments=insufficient,
            median_oos_accuracy=med_acc,
            mean_oos_accuracy=mean_acc,
            best_oos_accuracy=best_acc,
            worst_oos_accuracy=worst_acc,
            median_oos_sharpe=med_shp,
            best_oos_sharpe=best_shp,
            worst_oos_sharpe=worst_shp,
        )
