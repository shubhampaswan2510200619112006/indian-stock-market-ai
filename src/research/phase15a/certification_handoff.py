"""
Phase 15A Certification Handoff Manager.

Orchestrates the handoff from normalized intake artifacts into canonical Phase 14 certification.
Strictly respects canonical Phase 14 qualification logic without duplicating or weakening it.

Certification outcomes (Correction 1):
- CERTIFIED
- CERTIFIED_WITH_BLOCKING_CAPABILITY
- CERTIFICATION_FAILED
- QUARANTINED
- REJECTED

Certification traceability (Correction 8):
Traceable through:
certification_result -> normalized_artifact_sha256 -> raw_artifact_sha256 -> intake_id -> vendor/source metadata.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd

from src.research.phase14.certifier import Phase14DataCertifier, DatasetCertificationResult
from src.research.phase14.readiness_engine import Phase14ReadinessEngine, ResearchReadinessReport
from src.research.phase15a.safety_policy import SafetyPolicy


class CertificationOutcomeState(str, Enum):
    CERTIFIED = "CERTIFIED"
    CERTIFIED_WITH_BLOCKING_CAPABILITY = "CERTIFIED_WITH_BLOCKING_CAPABILITY"
    CERTIFICATION_FAILED = "CERTIFICATION_FAILED"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"


@dataclass
class CertificationHandoffRecord:
    handoff_id: str
    dataset_id: str
    version_id: str
    intake_id: str
    vendor: str
    underlying: str
    interval: str
    raw_artifact_sha256: str
    normalized_artifact_sha256: str
    source_description: str
    license_status: str
    outcome_state: str  # CERTIFIED, CERTIFIED_WITH_BLOCKING_CAPABILITY, CERTIFICATION_FAILED, QUARANTINED
    phase14_certified: bool
    phase14_rejection_reasons: List[str]
    phase14_failure_codes: List[str]
    blocking_capabilities: List[str]
    evaluated_at: str
    traceability_chain: Dict[str, str] = field(default_factory=dict)
    phase14_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CertificationHandoffManager:
    """
    Coordinates handoff of normalized datasets to Phase 14 certification engine.
    """

    @classmethod
    def execute_handoff(
        cls,
        df: Optional[pd.DataFrame],
        dataset_id: str,
        version_id: str,
        intake_id: str,
        vendor: str,
        underlying: str,
        interval: str,
        source_file: str,
        dataset_type: str,
        raw_artifact_sha256: str,
        normalized_artifact_sha256: str,
        source_description: str = "Vendor direct delivery",
        license_status: str = "LICENSE_VERIFIED_RESTRICTED_RESEARCH",
        df_1m_reference: Optional[pd.DataFrame] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CertificationHandoffRecord:
        SafetyPolicy.assert_safety_invariants(context=f"CertificationHandoff:{dataset_id}")

        handoff_id = f"HANDOFF-{intake_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        # 1. Invoke canonical Phase 14 Certifier
        p14_result: DatasetCertificationResult = Phase14DataCertifier.certify_dataset(
            df=df,
            dataset_id=dataset_id,
            version_id=version_id,
            underlying=underlying,
            interval=interval,
            vendor=vendor,
            source_file=source_file,
            dataset_type=dataset_type,
            license_status=license_status,
            df_1m_reference=df_1m_reference,
            metadata=metadata,
        )

        # 2. Determine Outcome State according to Correction 1
        blocking_capabilities: List[str] = []
        if p14_result.is_quarantined:
            outcome = CertificationOutcomeState.QUARANTINED
        elif not p14_result.is_certified:
            outcome = CertificationOutcomeState.CERTIFICATION_FAILED
        else:
            # Evaluate readiness to detect blocking capabilities
            readiness_report: ResearchReadinessReport = Phase14ReadinessEngine.evaluate([p14_result])
            for cap_name, cap_res in readiness_report.capability_readiness.items():
                if cap_res.state.value == "BLOCKED":
                    blocking_capabilities.append(cap_name)

            if readiness_report.project_full_market_data_ready == "PASS" and len(blocking_capabilities) == 0:
                outcome = CertificationOutcomeState.CERTIFIED
            else:
                outcome = CertificationOutcomeState.CERTIFIED_WITH_BLOCKING_CAPABILITY

        # 3. Construct Complete Traceability Chain (Correction 8)
        traceability = {
            "certification_run_id": p14_result.certification_run_id,
            "outcome_state": outcome.value,
            "normalized_artifact_sha256": normalized_artifact_sha256,
            "raw_artifact_sha256": raw_artifact_sha256,
            "intake_id": intake_id,
            "vendor": vendor,
            "source_description": source_description,
            "license_reference": license_status,
        }

        return CertificationHandoffRecord(
            handoff_id=handoff_id,
            dataset_id=dataset_id,
            version_id=version_id,
            intake_id=intake_id,
            vendor=vendor,
            underlying=underlying,
            interval=interval,
            raw_artifact_sha256=raw_artifact_sha256,
            normalized_artifact_sha256=normalized_artifact_sha256,
            source_description=source_description,
            license_status=license_status,
            outcome_state=outcome.value,
            phase14_certified=p14_result.is_certified,
            phase14_rejection_reasons=p14_result.rejection_reasons,
            phase14_failure_codes=p14_result.failure_codes,
            blocking_capabilities=blocking_capabilities,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            traceability_chain=traceability,
            phase14_details=p14_result.to_dict(),
        )
