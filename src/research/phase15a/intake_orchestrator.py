"""
Phase 15A Intake Orchestrator.

Coordinates dataset intake lifecycle, raw archiving, deterministic normalization,
and Phase 14 certification handoff.
In dormant mode (no commercial vendor datasets purchased/acquired):
- PHASE_15A_STATUS = "WAITING_FOR_VENDOR_DATA"
- REAL_DATASETS_RECEIVED = 0
- DATASETS_CERTIFIED = 0
- FULL_DATASET_CERTIFICATION = "BLOCKED"
- RESEARCH_READINESS = "BLOCKED"
Produces all 7 machine-readable JSON artifacts and 7 Markdown reports.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.research.phase15a.archive_structure import ArchiveStructureManager
from src.research.phase15a.baseline_verifier import Phase15ABaselineVerifier, BaselineVerificationResult
from src.research.phase15a.certification_handoff import CertificationHandoffManager, CertificationHandoffRecord
from src.research.phase15a.dataset_comparator import DatasetComparator, ComparisonReport
from src.research.phase15a.file_inspector import SafeFileInspector
from src.research.phase15a.intake_lifecycle import IntakeLifecycleState, IntakeLifecycleStateMachine
from src.research.phase15a.multi_file_handler import MultiFileDatasetTracker
from src.research.phase15a.normalization_engine import NormalizationEngine, TransformationAuditRecord
from src.research.phase15a.raw_archive import RawArchiveManager, RawArtifactRecord
from src.research.phase15a.reports import Phase15AReportGenerator
from src.research.phase15a.safety_policy import SafetyPolicy


class Phase15AIntakeOrchestrator:
    """
    Operational orchestrator for Phase 15A.
    """

    def __init__(self, data_output_dir: str = "data/phase15a", report_output_dir: str = "reports/phase15a"):
        self.data_output_dir = data_output_dir
        self.report_output_dir = report_output_dir
        self.structure_mgr = ArchiveStructureManager()
        self.raw_mgr = RawArchiveManager()
        self.multi_file_tracker = MultiFileDatasetTracker()

        self.intake_registry: Dict[str, Dict[str, Any]] = {}
        self.dataset_versions: Dict[str, Dict[str, Any]] = {}
        self.normalization_log: List[Dict[str, Any]] = []
        self.certification_handoffs: List[Dict[str, Any]] = []
        self.comparison_results: List[Dict[str, Any]] = []

    def run_dormant_orchestration(self, workspace_root: str = ".") -> Dict[str, Any]:
        """
        Executes Phase 15A orchestration under dormant waiting mode.
        """
        SafetyPolicy.assert_safety_invariants(context="Phase15AIntakeOrchestrator.run_dormant_orchestration")

        # 1. Initialize archive tier directories
        tier_paths = self.structure_mgr.initialize_directories()

        # 2. Verify all frozen baselines (Phase 9.7 through Phase 14)
        baseline_result = Phase15ABaselineVerifier.verify(workspace_root=workspace_root)
        baseline_integrity_status = "INTACT" if baseline_result.all_baselines_intact else "INCOMPLETE"

        # 3. Dormant operational state
        operational_state = {
            "phase": "15A",
            "phase_15a_status": "WAITING_FOR_VENDOR_DATA",
            "real_datasets_received": 0,
            "datasets_certified": 0,
            "full_dataset_certification": "BLOCKED",
            "research_readiness": "BLOCKED",
            "baseline_integrity": baseline_integrity_status,
            "phase_15_unlocked": False,
            "safety_invariants": SafetyPolicy.get_invariants_dict(),
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "tier_directories": tier_paths.to_dict(),
            "baseline_audit": baseline_result.to_dict(),
        }

        # 4. Save 7 JSON artifacts
        os.makedirs(self.data_output_dir, exist_ok=True)

        j1 = os.path.join(self.data_output_dir, "phase15a_intake_registry.json")
        intake_reg_data = {"total_intakes": 0, "intakes": self.intake_registry}
        with open(j1, "w", encoding="utf-8") as f:
            json.dump(intake_reg_data, f, indent=2)

        j2 = os.path.join(self.data_output_dir, "phase15a_raw_artifacts.json")
        raw_art_data = self.raw_mgr.to_dict()
        with open(j2, "w", encoding="utf-8") as f:
            json.dump(raw_art_data, f, indent=2)

        j3 = os.path.join(self.data_output_dir, "phase15a_dataset_versions.json")
        ver_data = {"total_versions": 0, "versions": self.dataset_versions}
        with open(j3, "w", encoding="utf-8") as f:
            json.dump(ver_data, f, indent=2)

        j4 = os.path.join(self.data_output_dir, "phase15a_normalization_log.json")
        norm_data = {"total_normalizations": len(self.normalization_log), "log": self.normalization_log}
        with open(j4, "w", encoding="utf-8") as f:
            json.dump(norm_data, f, indent=2)

        j5 = os.path.join(self.data_output_dir, "phase15a_certification_handoffs.json")
        handoff_data = {"total_handoffs": len(self.certification_handoffs), "handoffs": self.certification_handoffs}
        with open(j5, "w", encoding="utf-8") as f:
            json.dump(handoff_data, f, indent=2)

        j6 = os.path.join(self.data_output_dir, "phase15a_comparison_results.json")
        cmp_data = {"total_comparisons": len(self.comparison_results), "comparisons": self.comparison_results}
        with open(j6, "w", encoding="utf-8") as f:
            json.dump(cmp_data, f, indent=2)

        j7 = os.path.join(self.data_output_dir, "phase15a_operational_state.json")
        with open(j7, "w", encoding="utf-8") as f:
            json.dump(operational_state, f, indent=2)

        # 5. Generate 7 Markdown Reports
        Phase15AReportGenerator.generate_all(
            operational_state=operational_state,
            intake_registry=intake_reg_data,
            raw_artifacts=raw_art_data,
            dataset_versions=ver_data,
            normalization_log=norm_data,
            certification_handoffs=handoff_data,
            comparison_results=cmp_data,
            output_dir=self.report_output_dir,
        )

        return operational_state


def main():
    orchestrator = Phase15AIntakeOrchestrator()
    res = orchestrator.run_dormant_orchestration()
    print(f"Phase 15A Orchestration Complete: status={res['phase_15a_status']}, baselines={res['baseline_integrity']}")


if __name__ == "__main__":
    main()
