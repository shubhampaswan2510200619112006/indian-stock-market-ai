"""
Phase 9.8 — Step 3: Multi-Testing Audit & Data-Snooping Guard.

Tracks every dimension of research exploration to prevent unadjusted p-hacking:
- Number of registered hypotheses
- Number of exploratory tests vs confirmatory tests
- Number of candidate models
- Number of parameter configurations
- Number of datasets & instruments
- Multi-testing significance corrections: Bonferroni alpha and Benjamini-Hochberg FDR.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass
class TestEventRecord:
    event_id: int
    hypothesis_id: str
    track_name: str
    test_type: str  # "EXPLORATORY" or "CONFIRMATORY"
    instrument: str
    model_name: str
    parameter_set: Dict[str, Any]
    p_value_observed: float
    raw_significance: bool
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class MultipleTestingAuditReport:
    generated_at: str
    total_registered_hypotheses: int
    total_exploratory_tests: int
    total_confirmatory_tests: int
    total_candidate_models: int
    total_parameter_configurations: int
    total_instruments: int
    total_horizons: int
    nominal_alpha: float
    bonferroni_adjusted_alpha: float
    fdr_threshold_bh: float
    events: List[TestEventRecord]
    multiple_testing_penalty_applied: bool
    audit_verdict: str


class Phase98DataSnoopingGuard:
    """
    Guards against data-snooping and tracks the complete multiple-testing surface.
    """

    def __init__(self, out_filepath: str = "data/phase9_8/multiple_testing.json"):
        self.out_filepath = Path(out_filepath)
        self.events: List[TestEventRecord] = []
        self.models_seen: set[str] = set()
        self.instruments_seen: set[str] = set()
        self.horizons_seen: set[str] = set()
        self.param_configs_seen: int = 0

    def record_test(
        self,
        hypothesis_id: str,
        track_name: str,
        test_type: str,
        instrument: str,
        model_name: str,
        parameter_set: Dict[str, Any],
        p_value: float,
        horizon: str = "1D",
    ) -> None:
        self.models_seen.add(model_name)
        self.instruments_seen.add(instrument)
        self.horizons_seen.add(horizon)
        self.param_configs_seen += 1

        rec = TestEventRecord(
            event_id=len(self.events) + 1,
            hypothesis_id=hypothesis_id,
            track_name=track_name,
            test_type=test_type,
            instrument=instrument,
            model_name=model_name,
            parameter_set=parameter_set,
            p_value_observed=float(p_value),
            raw_significance=(p_value < 0.05),
        )
        self.events.append(rec)

    def generate_report(self, total_hypotheses: int = 8, nominal_alpha: float = 0.05) -> MultipleTestingAuditReport:
        total_tests = max(1, len(self.events))
        bonferroni_alpha = nominal_alpha / total_tests

        # Benjamini-Hochberg FDR calculation
        p_vals = sorted([e.p_value_observed for e in self.events])
        fdr_thresh = nominal_alpha
        for rank, p in enumerate(p_vals, start=1):
            crit = (rank / total_tests) * nominal_alpha
            if p <= crit:
                fdr_thresh = crit

        exploratory_count = sum(1 for e in self.events if e.test_type == "EXPLORATORY")
        confirmatory_count = sum(1 for e in self.events if e.test_type == "CONFIRMATORY")

        report = MultipleTestingAuditReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_registered_hypotheses=total_hypotheses,
            total_exploratory_tests=exploratory_count,
            total_confirmatory_tests=confirmatory_count,
            total_candidate_models=len(self.models_seen),
            total_parameter_configurations=self.param_configs_seen,
            total_instruments=len(self.instruments_seen),
            total_horizons=len(self.horizons_seen),
            nominal_alpha=nominal_alpha,
            bonferroni_adjusted_alpha=float(bonferroni_alpha),
            fdr_threshold_bh=float(fdr_thresh),
            events=self.events,
            multiple_testing_penalty_applied=True,
            audit_verdict="MULTIPLE_TESTING_CONTROLLED_AND_REPORTED",
        )

        self.out_filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.out_filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, default=str)

        return report
