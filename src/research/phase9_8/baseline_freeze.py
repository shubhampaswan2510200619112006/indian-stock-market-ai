"""
Phase 9.8 — Step 1: Baseline Freeze & Checksum Verification Engine.

Strictly preserves Phase 9.7 artifacts as an immutable baseline:
- data/phase9_7_cost_audit.json
- data/phase9_7_data_audit.json
- data/phase9_7_execution_audit.json
- data/phase9_7_leakage_audit.json
- data/phase9_7_phase10_gate.json
- data/phase9_7_revalidation.json
- PHASE_9_7_RESEARCH_INTEGRITY_REPORT.md
- LEAKAGE_AUDIT_REPORT.md
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Tuple


def compute_file_sha256(filepath: str | Path) -> str:
    p = Path(filepath)
    if not p.exists():
        return "FILE_NOT_FOUND"
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


@dataclass
class BaselineArtifactRecord:
    filepath: str
    expected_sha256: str
    observed_sha256: str
    is_match: bool
    status: str


@dataclass
class BaselineFreezeReport:
    total_artifacts: int
    matched_artifacts: int
    mismatched_artifacts: int
    is_frozen_baseline_intact: bool
    records: List[BaselineArtifactRecord]
    baseline_classification: str = "PHASE_10_NOT_JUSTIFIED"
    readiness: str = "RESEARCH_ONLY"


class Phase97BaselineFreeze:
    """
    Guarantees Phase 9.7 results remain unmodified throughout Phase 9.8.
    """

    FROZEN_CHECKSUMS: Dict[str, str] = {
        "data/phase9_7_cost_audit.json": "1dd4fa359d21408a19b635bd5ecec09985209caadac0d9104e88372d2b1da76a",
        "data/phase9_7_data_audit.json": "a63121b3c1221aa7fe5cfa3b1560bea1fa1ea883f51ff02d4bacd5d472171bcd",
        "data/phase9_7_execution_audit.json": "b6127e442ae696cb95b55745539e41b3a1ab361731d4c74c92c974e5d4d70d64",
        "data/phase9_7_leakage_audit.json": "2554b4f96b1faac3b63942a6c3751a36011599959d0b9b8f92786a050b1801e6",
        "data/phase9_7_phase10_gate.json": "b4c9c9dc8d3b9c8d6bbd2f6fdcefc10699ba4f87ba0855dbb88f572577413a58",
        "data/phase9_7_revalidation.json": "51dfc2cb7b4b93b54d97ee3d6dbc735fdac8de0694cbe180865c4a8d0bd9c67e",
        "PHASE_9_7_RESEARCH_INTEGRITY_REPORT.md": "6e96b6c6f0c10ebb8e3ac82144d9d7729add50a8d125504652d3e75f9b5c9e79",
        "LEAKAGE_AUDIT_REPORT.md": "a892e178beb1c8fa39d8d04a58c98ea552fc1652b3753ff7ccdc4fe4373ff2e8",
    }

    @classmethod
    def verify_baseline(cls) -> BaselineFreezeReport:
        records: List[BaselineArtifactRecord] = []
        matched = 0
        mismatched = 0

        for path_str, expected_hash in cls.FROZEN_CHECKSUMS.items():
            obs_hash = compute_file_sha256(path_str)
            match = (obs_hash == expected_hash)
            if match:
                matched += 1
                status = "INTACT"
            else:
                mismatched += 1
                status = "HASH_MISMATCH" if obs_hash != "FILE_NOT_FOUND" else "MISSING"

            records.append(
                BaselineArtifactRecord(
                    filepath=path_str,
                    expected_sha256=expected_hash,
                    observed_sha256=obs_hash,
                    is_match=match,
                    status=status,
                )
            )

        return BaselineFreezeReport(
            total_artifacts=len(cls.FROZEN_CHECKSUMS),
            matched_artifacts=matched,
            mismatched_artifacts=mismatched,
            is_frozen_baseline_intact=(mismatched == 0),
            records=records,
        )
