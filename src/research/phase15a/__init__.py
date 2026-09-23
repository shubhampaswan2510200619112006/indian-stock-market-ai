"""
Phase 15A — Dataset Intake & Certification Operations.

Provides a production-grade operational data-engineering layer for financial market datasets.
Enforces raw data immutability, deterministic normalization with cryptographic lineage,
ZIP entry tracking, test fixture isolation, and seamless handoff into canonical Phase 14 certification.
"""

from __future__ import annotations

from src.research.phase15a.safety_policy import SafetyPolicy, SafetyViolationError
from src.research.phase15a.baseline_verifier import Phase15ABaselineVerifier, BaselineVerificationResult
from src.research.phase15a.intake_lifecycle import IntakeLifecycleState, IntakeLifecycleStateMachine
from src.research.phase15a.raw_archive import RawArchiveManager, RawArtifactRecord, ZipEntryRecord
from src.research.phase15a.file_inspector import SafeFileInspector, FileInspectionResult
from src.research.phase15a.archive_structure import ArchiveStructureManager
from src.research.phase15a.normalization_engine import NormalizationEngine, TransformationAuditRecord
from src.research.phase15a.multi_file_handler import MultiFileDatasetTracker, MultiFileGroupRecord
from src.research.phase15a.dataset_comparator import DatasetComparator, ComparisonReport
from src.research.phase15a.reports import Phase15AReportGenerator
from src.research.phase15a.intake_orchestrator import Phase15AIntakeOrchestrator

__all__ = [
    "SafetyPolicy",
    "SafetyViolationError",
    "Phase15ABaselineVerifier",
    "BaselineVerificationResult",
    "IntakeLifecycleState",
    "IntakeLifecycleStateMachine",
    "RawArchiveManager",
    "RawArtifactRecord",
    "ZipEntryRecord",
    "SafeFileInspector",
    "FileInspectionResult",
    "ArchiveStructureManager",
    "NormalizationEngine",
    "TransformationAuditRecord",
    "MultiFileDatasetTracker",
    "MultiFileGroupRecord",
    "DatasetComparator",
    "ComparisonReport",
    "CertificationHandoffManager",
    "CertificationHandoffRecord",
    "CertificationOutcomeState",
    "Phase15AReportGenerator",
    "Phase15AIntakeOrchestrator",
]
