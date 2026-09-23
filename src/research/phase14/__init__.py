"""
Phase 14 — Full Dataset Qualification, Data Certification & Research Readiness.

Provides a deterministic, production-grade certification layer for legitimately
acquired financial-market datasets. Enforces strict safety policies, non-destructive
baseline verification, dynamic capability-scoped readiness, and test fixture isolation.
"""

from __future__ import annotations

from src.research.phase14.safety_policy import SafetyPolicy, SafetyViolationError
from src.research.phase14.baseline_verifier import Phase14BaselineVerifier, BaselineVerificationResult
from src.research.phase14.certification_state import CertificationState, CertificationStateMachine
from src.research.phase14.fixture_quarantine import FixtureQuarantineManager
from src.research.phase14.versioning import DatasetVersionRegistry, DatasetVersionRecord
from src.research.phase14.certifier import Phase14DataCertifier, DatasetCertificationResult
from src.research.phase14.scorecard import Phase14QualityScorecard
from src.research.phase14.readiness_engine import Phase14ReadinessEngine, ResearchReadinessReport

__all__ = [
    "SafetyPolicy",
    "SafetyViolationError",
    "Phase14BaselineVerifier",
    "BaselineVerificationResult",
    "CertificationState",
    "CertificationStateMachine",
    "FixtureQuarantineManager",
    "DatasetVersionRegistry",
    "DatasetVersionRecord",
    "Phase14DataCertifier",
    "DatasetCertificationResult",
    "Phase14QualityScorecard",
    "Phase14ReadinessEngine",
    "ResearchReadinessReport",
]
