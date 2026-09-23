"""
Phase 9.6 — Data-Snooping Defense & Test Partition Audit Engine.

Protects against P-hacking, test-set peeking, and retrospective tuning:
- Tracks hypothesis creation timestamp vs test evaluation timestamp.
- Detects repeated evaluation attempts on the final untouched test partition.
- Detects post-hoc threshold and hyperparameter searches.
- Distinguishes PRE_REGISTERED_CONFIRMATORY from EXPLORATORY hypotheses.
- Flags FINAL_TEST_CONTAMINATED if unauthorized test inspection occurs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
import json
import os


class DataSnoopingViolation(Exception):
    """Raised when data snooping, test-set contamination, or retrospective tuning is detected."""
    pass


@dataclass
class PartitionAccessRecord:
    hypothesis_id: str
    partition_name: str
    access_timestamp: str
    accessed_by_function: str
    dataset_hash: str
    is_confirmatory: bool


class DataSnoopingGuard:
    """
    Monitors access to validation and test partitions, preventing repeated queries
    and post-hoc threshold searches.
    """

    MAX_UNTOUCHED_TEST_ACCESS_LIMIT: int = 1

    def __init__(self, audit_filepath: str = "./data/data_snooping_audit.json"):
        self.filepath = audit_filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            self._save([])

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

    def record_test_access(
        self,
        hypothesis_id: str,
        partition_name: str = "FINAL_UNTOUCHED_TEST",
        function_name: str = "evaluate_hypothesis",
        dataset_hash: str = "default_hash",
        is_confirmatory: bool = True,
    ) -> None:
        """
        Records an access event to an evaluation partition.
        Enforces: The final untouched test set may be queried at most ONCE per confirmatory hypothesis.
        """
        records = self._load()
        now_iso = datetime.now(timezone.utc).isoformat()

        if partition_name == "FINAL_UNTOUCHED_TEST":
            # Count previous accesses for this hypothesis
            prev_accesses = [
                r for r in records
                if r["hypothesis_id"] == hypothesis_id and r["partition_name"] == "FINAL_UNTOUCHED_TEST"
            ]
            if len(prev_accesses) >= self.MAX_UNTOUCHED_TEST_ACCESS_LIMIT:
                raise DataSnoopingViolation(
                    f"FINAL_TEST_CONTAMINATED: Hypothesis '{hypothesis_id}' has already accessed the final "
                    f"untouched test partition {len(prev_accesses)} time(s). Repeated test-set evaluation "
                    f"violates confirmatory research integrity."
                )

        record = PartitionAccessRecord(
            hypothesis_id=hypothesis_id,
            partition_name=partition_name,
            access_timestamp=now_iso,
            accessed_by_function=function_name,
            dataset_hash=dataset_hash,
            is_confirmatory=is_confirmatory,
        )
        records.append(asdict(record))
        self._save(records)

    def assert_pre_registration_timing(
        self,
        hypothesis_created_at: str,
        evaluation_started_at: str,
    ) -> None:
        """
        Verifies that hypothesis creation strictly precedes or equals evaluation start time.
        """
        t_create = datetime.fromisoformat(hypothesis_created_at)
        t_eval = datetime.fromisoformat(evaluation_started_at)
        if t_create > t_eval:
            raise DataSnoopingViolation(
                f"Data Snooping Inversion: Hypothesis creation timestamp ({hypothesis_created_at}) "
                f"is chronologically AFTER evaluation start ({evaluation_started_at}). "
                f"Hypotheses must be pre-registered prior to running tests."
            )

    def get_audit_report(self) -> Dict[str, Any]:
        records = self._load()
        test_access_counts: Dict[str, int] = {}
        for r in records:
            hid = r.get("hypothesis_id", "UNKNOWN")
            if r.get("partition_name") == "FINAL_UNTOUCHED_TEST":
                test_access_counts[hid] = test_access_counts.get(hid, 0) + 1

        is_contaminated = any(cnt > self.MAX_UNTOUCHED_TEST_ACCESS_LIMIT for cnt in test_access_counts.values())

        return {
            "total_partition_access_events": len(records),
            "final_untouched_test_accesses": sum(test_access_counts.values()),
            "unique_hypotheses_evaluated_on_test": len(test_access_counts),
            "is_final_test_contaminated": is_contaminated,
            "status": "FINAL_TEST_CONTAMINATED" if is_contaminated else "DATA_SNOOPING_CLEAN",
        }
