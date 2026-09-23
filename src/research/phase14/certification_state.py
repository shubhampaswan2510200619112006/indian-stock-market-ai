"""
Phase 14 Certification State Machine.

Implements the 16 lifecycle states for dataset qualification and research readiness.
Supports legitimate non-linear branching and preserves a tamper-evident transition audit trail.
Illegal transitions fail safely.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from src.research.phase14.safety_policy import SafetyPolicy


class CertificationState(str, Enum):
    WAITING_FOR_VENDOR_DATA = "WAITING_FOR_VENDOR_DATA"
    DATA_RECEIVED = "DATA_RECEIVED"
    INGESTION_RUNNING = "INGESTION_RUNNING"
    INGESTION_FAILED = "INGESTION_FAILED"
    TECHNICAL_VALIDATION_RUNNING = "TECHNICAL_VALIDATION_RUNNING"
    TECHNICAL_VALIDATION_FAILED = "TECHNICAL_VALIDATION_FAILED"
    TECHNICAL_VALIDATION_PASSED = "TECHNICAL_VALIDATION_PASSED"
    PROVENANCE_VALIDATION_RUNNING = "PROVENANCE_VALIDATION_RUNNING"
    PROVENANCE_VALIDATION_FAILED = "PROVENANCE_VALIDATION_FAILED"
    PROVENANCE_VALIDATION_PASSED = "PROVENANCE_VALIDATION_PASSED"
    LICENSE_VALIDATION_RUNNING = "LICENSE_VALIDATION_RUNNING"
    LICENSE_VALIDATION_FAILED = "LICENSE_VALIDATION_FAILED"
    LICENSE_VALIDATION_PASSED = "LICENSE_VALIDATION_PASSED"
    FULL_DATASET_CERTIFIED = "FULL_DATASET_CERTIFIED"
    RESEARCH_READINESS_BLOCKED = "RESEARCH_READINESS_BLOCKED"
    RESEARCH_READINESS_ELIGIBLE = "RESEARCH_READINESS_ELIGIBLE"


@dataclass
class StateTransitionAuditRecord:
    transition_id: str
    previous_state: str
    new_state: str
    timestamp: str
    transition_reason: str
    evidence_reference: str
    actor: str
    validation_run_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IllegalStateTransitionError(ValueError):
    """Raised when an illegal lifecycle state transition is attempted."""
    pass


class CertificationStateMachine:
    """
    Non-linear branching state machine managing dataset certification lifecycle.
    """

    ALLOWED_TRANSITIONS: Dict[CertificationState, Set[CertificationState]] = {
        CertificationState.WAITING_FOR_VENDOR_DATA: {
            CertificationState.DATA_RECEIVED,
        },
        CertificationState.DATA_RECEIVED: {
            CertificationState.INGESTION_RUNNING,
            CertificationState.WAITING_FOR_VENDOR_DATA,
        },
        CertificationState.INGESTION_RUNNING: {
            CertificationState.INGESTION_FAILED,
            CertificationState.TECHNICAL_VALIDATION_RUNNING,
        },
        CertificationState.INGESTION_FAILED: {
            CertificationState.DATA_RECEIVED,
            CertificationState.WAITING_FOR_VENDOR_DATA,
        },
        CertificationState.TECHNICAL_VALIDATION_RUNNING: {
            CertificationState.TECHNICAL_VALIDATION_FAILED,
            CertificationState.TECHNICAL_VALIDATION_PASSED,
        },
        CertificationState.TECHNICAL_VALIDATION_FAILED: {
            CertificationState.DATA_RECEIVED,
            CertificationState.WAITING_FOR_VENDOR_DATA,
        },
        CertificationState.TECHNICAL_VALIDATION_PASSED: {
            CertificationState.PROVENANCE_VALIDATION_RUNNING,
        },
        CertificationState.PROVENANCE_VALIDATION_RUNNING: {
            CertificationState.PROVENANCE_VALIDATION_FAILED,
            CertificationState.PROVENANCE_VALIDATION_PASSED,
        },
        CertificationState.PROVENANCE_VALIDATION_FAILED: {
            CertificationState.TECHNICAL_VALIDATION_PASSED,
            CertificationState.WAITING_FOR_VENDOR_DATA,
        },
        CertificationState.PROVENANCE_VALIDATION_PASSED: {
            CertificationState.LICENSE_VALIDATION_RUNNING,
        },
        CertificationState.LICENSE_VALIDATION_RUNNING: {
            CertificationState.LICENSE_VALIDATION_FAILED,
            CertificationState.LICENSE_VALIDATION_PASSED,
        },
        CertificationState.LICENSE_VALIDATION_FAILED: {
            CertificationState.PROVENANCE_VALIDATION_PASSED,
            CertificationState.WAITING_FOR_VENDOR_DATA,
        },
        CertificationState.LICENSE_VALIDATION_PASSED: {
            CertificationState.FULL_DATASET_CERTIFIED,
            CertificationState.RESEARCH_READINESS_BLOCKED,
        },
        CertificationState.FULL_DATASET_CERTIFIED: {
            CertificationState.RESEARCH_READINESS_BLOCKED,
            CertificationState.RESEARCH_READINESS_ELIGIBLE,
        },
        CertificationState.RESEARCH_READINESS_BLOCKED: {
            CertificationState.RESEARCH_READINESS_ELIGIBLE,
            CertificationState.WAITING_FOR_VENDOR_DATA,
        },
        CertificationState.RESEARCH_READINESS_ELIGIBLE: {
            CertificationState.RESEARCH_READINESS_BLOCKED,
            CertificationState.WAITING_FOR_VENDOR_DATA,
        },
    }

    def __init__(self, initial_state: CertificationState = CertificationState.WAITING_FOR_VENDOR_DATA):
        self.current_state = initial_state
        self.audit_log: List[StateTransitionAuditRecord] = []
        self._record_transition(
            prev_state="NONE",
            new_state=initial_state.value,
            reason="Initial state machine instantiation",
            evidence="INIT",
            actor="SYSTEM",
        )

    def _record_transition(
        self,
        prev_state: str,
        new_state: str,
        reason: str,
        evidence: str,
        actor: str,
        val_run: Optional[str] = None,
    ) -> None:
        rec = StateTransitionAuditRecord(
            transition_id=f"TRANS-{len(self.audit_log)+1:04d}",
            previous_state=prev_state,
            new_state=new_state,
            timestamp=datetime.now(timezone.utc).isoformat(),
            transition_reason=reason,
            evidence_reference=evidence,
            actor=actor,
            validation_run_id=val_run,
        )
        self.audit_log.append(rec)

    def transition_to(
        self,
        target_state: CertificationState,
        reason: str,
        evidence_reference: str,
        actor: str = "PIPELINE_ORCHESTRATOR",
        validation_run_id: Optional[str] = None,
    ) -> CertificationState:
        """
        Executes a validated state transition. Asserts safety policy beforehand.
        """
        SafetyPolicy.assert_safety_invariants(context=f"StateTransition:{self.current_state}->{target_state}")

        allowed = self.ALLOWED_TRANSITIONS.get(self.current_state, set())
        if target_state not in allowed:
            raise IllegalStateTransitionError(
                f"Illegal state transition from {self.current_state.value} to {target_state.value}. "
                f"Allowed target states: {[s.value for s in allowed]}"
            )

        prev = self.current_state.value
        self.current_state = target_state
        self._record_transition(
            prev_state=prev,
            new_state=target_state.value,
            reason=reason,
            evidence=evidence_reference,
            actor=actor,
            val_run=validation_run_id,
        )
        return self.current_state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_state": self.current_state.value,
            "total_transitions": len(self.audit_log),
            "audit_trail": [a.to_dict() for a in self.audit_log],
        }
