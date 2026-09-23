"""
Phase 15A Intake Lifecycle State Machine.

Implements the 10-step data intake lifecycle and its failure branches.
Supports the required terminal certification outcomes:
- CERTIFIED
- CERTIFIED_WITH_BLOCKING_CAPABILITY
- CERTIFICATION_FAILED
- QUARANTINED
- REJECTED
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from src.research.phase15a.safety_policy import SafetyPolicy


class IntakeLifecycleState(str, Enum):
    # Forward linear stages
    INTAKE_DECLARED = "INTAKE_DECLARED"
    DATA_RECEIVED = "DATA_RECEIVED"
    RAW_ARCHIVE_CREATED = "RAW_ARCHIVE_CREATED"
    CHECKSUM_CALCULATED = "CHECKSUM_CALCULATED"
    IDENTITY_REGISTERED = "IDENTITY_REGISTERED"
    SCHEMA_INSPECTION = "SCHEMA_INSPECTION"
    PROVENANCE_REGISTERED = "PROVENANCE_REGISTERED"
    PHASE14_CERTIFICATION_QUEUED = "PHASE14_CERTIFICATION_QUEUED"
    PHASE14_CERTIFICATION_RUNNING = "PHASE14_CERTIFICATION_RUNNING"
    
    # Terminal outcomes (Correction 1)
    CERTIFIED = "CERTIFIED"
    CERTIFIED_WITH_BLOCKING_CAPABILITY = "CERTIFIED_WITH_BLOCKING_CAPABILITY"
    CERTIFICATION_FAILED = "CERTIFICATION_FAILED"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"

    # Intermediate failure branches
    INGESTION_FAILED = "INGESTION_FAILED"
    CHECKSUM_FAILED = "CHECKSUM_FAILED"
    SCHEMA_FAILED = "SCHEMA_FAILED"
    PROVENANCE_FAILED = "PROVENANCE_FAILED"


@dataclass
class IntakeTransitionAuditRecord:
    transition_id: str
    intake_id: str
    previous_state: str
    new_state: str
    timestamp: str
    transition_reason: str
    evidence_reference: str
    actor: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IllegalIntakeTransitionError(ValueError):
    """Raised when an illegal intake state transition is attempted."""
    pass


class IntakeLifecycleStateMachine:
    """
    Manages state transitions across the intake and certification lifecycle.
    """

    ALLOWED_TRANSITIONS: Dict[IntakeLifecycleState, Set[IntakeLifecycleState]] = {
        IntakeLifecycleState.INTAKE_DECLARED: {
            IntakeLifecycleState.DATA_RECEIVED,
            IntakeLifecycleState.INGESTION_FAILED,
            IntakeLifecycleState.REJECTED,
        },
        IntakeLifecycleState.DATA_RECEIVED: {
            IntakeLifecycleState.RAW_ARCHIVE_CREATED,
            IntakeLifecycleState.INGESTION_FAILED,
            IntakeLifecycleState.QUARANTINED,
            IntakeLifecycleState.REJECTED,
        },
        IntakeLifecycleState.RAW_ARCHIVE_CREATED: {
            IntakeLifecycleState.CHECKSUM_CALCULATED,
            IntakeLifecycleState.CHECKSUM_FAILED,
            IntakeLifecycleState.REJECTED,
        },
        IntakeLifecycleState.CHECKSUM_CALCULATED: {
            IntakeLifecycleState.IDENTITY_REGISTERED,
            IntakeLifecycleState.QUARANTINED,
            IntakeLifecycleState.REJECTED,
        },
        IntakeLifecycleState.IDENTITY_REGISTERED: {
            IntakeLifecycleState.SCHEMA_INSPECTION,
            IntakeLifecycleState.SCHEMA_FAILED,
            IntakeLifecycleState.QUARANTINED,
            IntakeLifecycleState.REJECTED,
        },
        IntakeLifecycleState.SCHEMA_INSPECTION: {
            IntakeLifecycleState.PROVENANCE_REGISTERED,
            IntakeLifecycleState.SCHEMA_FAILED,
            IntakeLifecycleState.REJECTED,
        },
        IntakeLifecycleState.PROVENANCE_REGISTERED: {
            IntakeLifecycleState.PHASE14_CERTIFICATION_QUEUED,
            IntakeLifecycleState.PROVENANCE_FAILED,
            IntakeLifecycleState.REJECTED,
        },
        IntakeLifecycleState.PHASE14_CERTIFICATION_QUEUED: {
            IntakeLifecycleState.PHASE14_CERTIFICATION_RUNNING,
            IntakeLifecycleState.REJECTED,
        },
        IntakeLifecycleState.PHASE14_CERTIFICATION_RUNNING: {
            IntakeLifecycleState.CERTIFIED,
            IntakeLifecycleState.CERTIFIED_WITH_BLOCKING_CAPABILITY,
            IntakeLifecycleState.CERTIFICATION_FAILED,
            IntakeLifecycleState.QUARANTINED,
            IntakeLifecycleState.REJECTED,
        },
        # Terminal states can transition to REJECTED if post-intake defects or contamination discovered
        IntakeLifecycleState.CERTIFIED: {IntakeLifecycleState.REJECTED, IntakeLifecycleState.QUARANTINED},
        IntakeLifecycleState.CERTIFIED_WITH_BLOCKING_CAPABILITY: {IntakeLifecycleState.REJECTED, IntakeLifecycleState.QUARANTINED},
        IntakeLifecycleState.CERTIFICATION_FAILED: {IntakeLifecycleState.REJECTED},
        IntakeLifecycleState.QUARANTINED: set(),
        IntakeLifecycleState.REJECTED: set(),
        IntakeLifecycleState.INGESTION_FAILED: set(),
        IntakeLifecycleState.CHECKSUM_FAILED: set(),
        IntakeLifecycleState.SCHEMA_FAILED: set(),
        IntakeLifecycleState.PROVENANCE_FAILED: set(),
    }

    def __init__(self, intake_id: str, initial_state: IntakeLifecycleState = IntakeLifecycleState.INTAKE_DECLARED):
        self.intake_id = intake_id
        self.current_state = initial_state
        self.audit_log: List[IntakeTransitionAuditRecord] = []
        self._record_transition("NONE", initial_state.value, "Initial declaration", "INIT", "SYSTEM")

    def _record_transition(self, prev: str, new_st: str, reason: str, evidence: str, actor: str) -> None:
        rec = IntakeTransitionAuditRecord(
            transition_id=f"TRANS-{self.intake_id}-{len(self.audit_log)+1:03d}",
            intake_id=self.intake_id,
            previous_state=prev,
            new_state=new_st,
            timestamp=datetime.now(timezone.utc).isoformat(),
            transition_reason=reason,
            evidence_reference=evidence,
            actor=actor,
        )
        self.audit_log.append(rec)

    def transition_to(
        self,
        target_state: IntakeLifecycleState,
        reason: str,
        evidence_reference: str,
        actor: str = "INTAKE_PIPELINE",
    ) -> IntakeLifecycleState:
        SafetyPolicy.assert_safety_invariants(context=f"IntakeTransition:{self.intake_id}:{self.current_state}->{target_state}")

        allowed = self.ALLOWED_TRANSITIONS.get(self.current_state, set())
        if target_state not in allowed:
            raise IllegalIntakeTransitionError(
                f"Illegal intake transition from {self.current_state.value} to {target_state.value}. "
                f"Allowed states: {[s.value for s in allowed]}"
            )

        prev = self.current_state.value
        self.current_state = target_state
        self._record_transition(prev, target_state.value, reason, evidence_reference, actor)
        return self.current_state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intake_id": self.intake_id,
            "current_state": self.current_state.value,
            "total_transitions": len(self.audit_log),
            "audit_trail": [a.to_dict() for a in self.audit_log],
        }
