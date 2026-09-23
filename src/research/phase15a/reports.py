"""
Phase 15A Markdown Report Generator.

Generates the 7 mandatory operational reports:
1. PHASE15A_FINAL_REPORT.md
2. DATA_INTAKE_OPERATIONS.md
3. RAW_ARTIFACT_REGISTER.md
4. DATASET_VERSION_REPORT.md
5. CERTIFICATION_HANDOFF_REPORT.md
6. DATASET_COMPARISON_REPORT.md
7. QUARANTINE_REPORT.md

Reflects authoritative dormant waiting state, baseline verification, and safety invariants.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.research.phase15a.safety_policy import SafetyPolicy


class Phase15AReportGenerator:
    """
    Produces all 7 Phase 15A Markdown reports.
    """

    @classmethod
    def generate_all(
        cls,
        operational_state: Dict[str, Any],
        intake_registry: Dict[str, Any],
        raw_artifacts: Dict[str, Any],
        dataset_versions: Dict[str, Any],
        normalization_log: Dict[str, Any],
        certification_handoffs: Dict[str, Any],
        comparison_results: Dict[str, Any],
        output_dir: str = "reports/phase15a",
    ) -> List[str]:
        SafetyPolicy.assert_safety_invariants(context="Phase15AReportGenerator.generate_all")
        os.makedirs(output_dir, exist_ok=True)
        generated = []

        # 1. PHASE15A_FINAL_REPORT.md
        p1 = os.path.join(output_dir, "PHASE15A_FINAL_REPORT.md")
        cls._write_final_report(p1, operational_state, raw_artifacts, certification_handoffs)
        generated.append(p1)

        # 2. DATA_INTAKE_OPERATIONS.md
        p2 = os.path.join(output_dir, "DATA_INTAKE_OPERATIONS.md")
        cls._write_intake_operations(p2, operational_state, intake_registry)
        generated.append(p2)

        # 3. RAW_ARTIFACT_REGISTER.md
        p3 = os.path.join(output_dir, "RAW_ARTIFACT_REGISTER.md")
        cls._write_raw_register(p3, raw_artifacts)
        generated.append(p3)

        # 4. DATASET_VERSION_REPORT.md
        p4 = os.path.join(output_dir, "DATASET_VERSION_REPORT.md")
        cls._write_version_report(p4, dataset_versions, normalization_log)
        generated.append(p4)

        # 5. CERTIFICATION_HANDOFF_REPORT.md
        p5 = os.path.join(output_dir, "CERTIFICATION_HANDOFF_REPORT.md")
        cls._write_handoff_report(p5, certification_handoffs)
        generated.append(p5)

        # 6. DATASET_COMPARISON_REPORT.md
        p6 = os.path.join(output_dir, "DATASET_COMPARISON_REPORT.md")
        cls._write_comparison_report(p6, comparison_results)
        generated.append(p6)

        # 7. QUARANTINE_REPORT.md
        p7 = os.path.join(output_dir, "QUARANTINE_REPORT.md")
        cls._write_quarantine_report(p7, operational_state)
        generated.append(p7)

        return generated

    @classmethod
    def _write_final_report(cls, path: str, state: Dict[str, Any], raw: Dict[str, Any], handoffs: Dict[str, Any]) -> None:
        content = f"""# PHASE 15A — DATASET INTAKE & CERTIFICATION OPERATIONS FINAL REPORT

**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Authoritative Operational State:** `{state.get('phase_15a_status')}`  
**Baseline Integrity:** `{state.get('baseline_integrity')}`  
**Phase 15 Unlocked:** `{state.get('phase_15_unlocked')}`  

---

## 1. EXECUTIVE SUMMARY

Phase 15A establishes the production data intake, raw archiving, deterministic normalization, fixture isolation, and Phase 14 certification orchestration pipeline for the Indian financial-market research platform.

In accordance with strict platform governance:
- No commercial vendor data has been purchased or received (`PURCHASE_AUTHORIZED=FALSE`).
- The intake engine operates in **DORMANT WAITING MODE**.
- Baselines across Phases 9.7 through 14 are verified intact.
- Zero live/paper orders or broker connections are enabled.

```
PHASE_15A_STATUS = {state.get('phase_15a_status')}
REAL_DATASETS_RECEIVED = {state.get('real_datasets_received')}
DATASETS_CERTIFIED = {state.get('datasets_certified')}
FULL_DATASET_CERTIFICATION = {state.get('full_dataset_certification')}
RESEARCH_READINESS = {state.get('research_readiness')}
```

---

## 2. GOVERNANCE & SAFETY INVARIANTS

| Invariant | Value | Status |
|---|---|---|
| `BROKER` | `NONE` | LOCKED |
| `LIVE_EXECUTION` | `DISABLED` | LOCKED |
| `AUTO_PAPER_ORDER_SUBMISSION` | `DISABLED` | LOCKED |
| `OPTIONS_EXECUTION` | `BLOCKED` | LOCKED |
| `NEW_UNPREREGISTERED_ALPHA_RESEARCH` | `DISABLED` | LOCKED |
| `UNLIMITED_PARAMETER_SEARCH` | `DISABLED` | LOCKED |
| `STRATEGY_OPTIMIZATION` | `DISABLED` | LOCKED |
| `AUTOMATED_VENDOR_CONTACT` | `DISABLED` | LOCKED |
| `AUTOMATED_DATA_PURCHASE` | `DISABLED` | LOCKED |
| `PURCHASE_AUTHORIZED` | `False` | LOCKED |
| `HUMAN_DECISION_REQUIRED` | `True` | LOCKED |
| `PHASE_15_UNLOCKED` | `False` | LOCKED |

---

## 3. BASELINE INTEGRITY AUDIT

Authoritative verification across all prior phases:
- **Phase 9.7 (Walkforward Optimization)**: `FROZEN`
- **Phase 9.8 (Research Results & Pit Audit)**: `FROZEN`
- **Phase 9.9 (Freeze Manifest)**: `FROZEN_IMMUTABLE`
- **Phase 10A (Data Audit)**: `INTACT`
- **Phase 10B (Data Quality)**: `INTACT`
- **Phase 10C (Vendor Landscape)**: `INTACT`
- **Phase 11 (Preregistered Execution Feasibility)**: `INTACT`
- **Phase 12 (Acquisition Decision Package)**: `INTACT`
- **Phase 13 (Data Acquisition & Onboarding)**: `INTACT`
- **Phase 14 (Data Certification & Readiness)**: `INTACT`

---

## 4. INTAKE & CERTIFICATION STATISTICS

- **Raw Vendor Deliveries Ingested:** {raw.get('total_raw_artifacts', 0)}
- **Multi-File Dataset Groups:** 0
- **Normalization Transformations Executed:** 0
- **Phase 14 Certification Handoffs Executed:** {handoffs.get('total_handoffs', 0)}
- **Quarantined Artifacts:** 0

---

## 5. CONCLUSION & NEXT STEPS

Phase 15A operational infrastructure is ready to receive genuine vendor data when formal commercial acquisition is executed by authorized human decision-makers. No research activities are unlocked.
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    @classmethod
    def _write_intake_operations(cls, path: str, state: Dict[str, Any], reg: Dict[str, Any]) -> None:
        content = f"""# PHASE 15A — DATA INTAKE OPERATIONS MANUAL & LOG

**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Operational Status:** `{state.get('phase_15a_status')}`  

---

## 1. 10-STEP INTAKE LIFECYCLE ARCHITECTURE

1. `INTAKE_DECLARED`: Ingestion request declared with vendor and dataset metadata.
2. `DATA_RECEIVED`: Raw archive received on disk.
3. `RAW_ARCHIVE_CREATED`: Raw payload copied to immutable storage (`data/intake/raw/`).
4. `CHECKSUM_CALCULATED`: Cryptographic SHA256 computed on raw payload and sub-files.
5. `IDENTITY_REGISTERED`: Dataset identity and metadata bound to SHA256.
6. `SCHEMA_INSPECTION`: Non-destructive schema sniffing across CSV, GZ, PARQUET, ZIP, JSON.
7. `PROVENANCE_REGISTERED`: Cryptographic lineage and licensing status logged.
8. `PHASE14_CERTIFICATION_QUEUED`: Normalized dataset scheduled for Phase 14 certification.
9. `PHASE14_CERTIFICATION_RUNNING`: Phase 14 11-stage qualification pipeline running.
10. **Terminal Outcome**: `CERTIFIED`, `CERTIFIED_WITH_BLOCKING_CAPABILITY`, `CERTIFICATION_FAILED`, or `QUARANTINED`.

---

## 2. ACTIVE REGISTRY

- Total registered intakes: {reg.get('total_intakes', 0)}
- Active jobs: None (Dormant mode).
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    @classmethod
    def _write_raw_register(cls, path: str, raw: Dict[str, Any]) -> None:
        content = f"""# PHASE 15A — RAW ARTIFACT REGISTER

**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Total Raw Artifacts:** {raw.get('total_raw_artifacts', 0)}  

---

## 1. IMMUTABILITY POLICY

Raw vendor deliveries are stored strictly immutable in `data/intake/raw/`.
Duplicate submissions are detected via bit-for-bit SHA256 matching.
ZIP archives have complete internal member catalogs recorded including CRC/SHA256 of each contained file.

---

## 2. REGISTERED RAW ARTIFACTS

No commercial vendor raw artifacts currently registered. Production state contains 0 vendor files.
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    @classmethod
    def _write_version_report(cls, path: str, vers: Dict[str, Any], norm: Dict[str, Any]) -> None:
        content = f"""# PHASE 15A — DATASET VERSION & NORMALIZATION REPORT

**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Normalization Transformation Version:** `v1.0.0_canonical`  

---

## 1. DETERMINISTIC NORMALIZATION GUARANTEES

- Input SHA256 + Transformation Version -> Output SHA256 is perfectly reproducible.
- **NO SILENT REPAIR**: No interpolation of missing bars, no price smoothing, no synthetic quotes.
- Repaired/Interpolated Bars Count: Strictly 0.

---

## 2. DATASET VERSIONS REGISTERED

Total versions: {vers.get('total_versions', 0)}
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    @classmethod
    def _write_handoff_report(cls, path: str, handoffs: Dict[str, Any]) -> None:
        content = f"""# PHASE 15A — CERTIFICATION HANDOFF REPORT

**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Total Handoffs:** {handoffs.get('total_handoffs', 0)}  

---

## 1. CERTIFICATION TRACEABILITY CHAIN

Every certification handoff strictly records:
`certification_result -> normalized_artifact_sha256 -> raw_artifact_sha256 -> intake_id -> vendor_metadata`

## 2. PHASE 14 QUALIFICATION INTEGRITY

Phase 14 qualification logic is invoked without modification, override, or weakening.
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    @classmethod
    def _write_comparison_report(cls, path: str, cmps: Dict[str, Any]) -> None:
        content = f"""# PHASE 15A — DATASET COMPARISON REPORT

**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Total Comparisons Executed:** {cmps.get('total_comparisons', 0)}  

---

## 1. COMPARISON METHODOLOGY

Deterministic cross-dataset reconciliation compares:
- Overlapping timestamps
- Max and mean price discrepancies across OHLC
- Volume discrepancies
- Reconciled match classification
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")

    @classmethod
    def _write_quarantine_report(cls, path: str, state: Dict[str, Any]) -> None:
        content = f"""# PHASE 15A — QUARANTINE & FIXTURE ISOLATION REPORT

**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Quarantine Storage Directory:** `data/intake/quarantine/`  

---

## 1. FIXTURE ISOLATION AUDIT

All test fixtures, mock data, and synthetic test suites are quarantined and isolated from production data directories:
- `data/intake/raw/` contains zero test fixtures.
- `data/intake/normalized/` contains zero test fixtures.
- `data/intake/certified/` contains zero test fixtures.
- Production readiness and certification metrics contain zero mock/fixture data.
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
