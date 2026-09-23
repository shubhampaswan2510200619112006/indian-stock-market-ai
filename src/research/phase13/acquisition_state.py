"""
Phase 13 Acquisition State Machine & Human Authorization Protocol.

Implements non-linear branching state transitions across 21 lifecycle states.
Enforces safety invariants before every transition.
Requires structured HumanAuthorizationRecord for manual acquisition approval.
Preserves complete immutable audit trail.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from src.research.phase13.safety_policy import SafetyPolicy


class AcquisitionLifecycleState(str, Enum):
    AWAITING_VENDOR_CONTACT = "AWAITING_VENDOR_CONTACT"
    VENDOR_CONTACTED = "VENDOR_CONTACTED"
    AWAITING_VENDOR_RESPONSE = "AWAITING_VENDOR_RESPONSE"
    RESPONSE_RECEIVED = "RESPONSE_RECEIVED"
    AWAITING_QUOTE = "AWAITING_QUOTE"
    QUOTE_RECEIVED = "QUOTE_RECEIVED"
    AWAITING_SAMPLE = "AWAITING_SAMPLE"
    SAMPLE_RECEIVED = "SAMPLE_RECEIVED"
    SAMPLE_VALIDATION_RUNNING = "SAMPLE_VALIDATION_RUNNING"
    SAMPLE_VALIDATION_FAILED = "SAMPLE_VALIDATION_FAILED"
    SAMPLE_VALIDATION_PASSED = "SAMPLE_VALIDATION_PASSED"
    AWAITING_LICENSE_REVIEW = "AWAITING_LICENSE_REVIEW"
    AWAITING_HUMAN_DECISION = "AWAITING_HUMAN_DECISION"
    APPROVED_FOR_MANUAL_ACQUISITION = "APPROVED_FOR_MANUAL_ACQUISITION"
    DECLINED = "DECLINED"
    ACQUISITION_IN_PROGRESS = "ACQUISITION_IN_PROGRESS"
    DATA_RECEIVED = "DATA_RECEIVED"
    FULL_VALIDATION_RUNNING = "FULL_VALIDATION_RUNNING"
    FULL_VALIDATION_FAILED = "FULL_VALIDATION_FAILED"
    FULL_VALIDATION_PASSED = "FULL_VALIDATION_PASSED"
    ONBOARDING_COMPLETE = "ONBOARDING_COMPLETE"


# Aliases for Phase 12 compatibility
STATE_ALIASES = {
    "AWAITING_HUMAN_VENDOR_DECISION": AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
    "AWAITING_HUMAN_ACQUISITION_DECISION": AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
    "VENDOR_EVALUATION_COMPLETE": AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
}


@dataclass
class HumanAuthorizationRecord:
    human_decision: str  # APPROVE, REJECT, REQUEST_MORE_INFO, NEGOTIATE
    decision_timestamp: str
    vendor: str
    product: str
    approved_scope: str
    approved_cost_ref: str
    authorization_id: str
    decision_outcome: str  # APPROVED_FOR_MANUAL_ACQUISITION, DECLINED
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StateTransitionEvent:
    from_state: str
    to_state: str
    timestamp: str
    transition_reason: str
    evidence_reference: Optional[str] = None
    actor: str = "SYSTEM"
    validation_run_id: Optional[str] = None
    authorization_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AcquisitionStateMachine:
    """
    Branching state machine managing the Phase 13 data acquisition lifecycle.
    """

    # Permitted non-linear branch transitions
    VALID_TRANSITIONS: Dict[AcquisitionLifecycleState, List[AcquisitionLifecycleState]] = {
        AcquisitionLifecycleState.AWAITING_VENDOR_CONTACT: [
            AcquisitionLifecycleState.VENDOR_CONTACTED,
            AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
        ],
        AcquisitionLifecycleState.VENDOR_CONTACTED: [
            AcquisitionLifecycleState.AWAITING_VENDOR_RESPONSE,
            AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
        ],
        AcquisitionLifecycleState.AWAITING_VENDOR_RESPONSE: [
            AcquisitionLifecycleState.RESPONSE_RECEIVED,
            AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
        ],
        AcquisitionLifecycleState.RESPONSE_RECEIVED: [
            AcquisitionLifecycleState.AWAITING_QUOTE,
            AcquisitionLifecycleState.AWAITING_SAMPLE,
            AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
            AcquisitionLifecycleState.DECLINED,
        ],
        AcquisitionLifecycleState.AWAITING_QUOTE: [
            AcquisitionLifecycleState.QUOTE_RECEIVED,
            AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
        ],
        AcquisitionLifecycleState.QUOTE_RECEIVED: [
            AcquisitionLifecycleState.AWAITING_SAMPLE,
            AcquisitionLifecycleState.AWAITING_LICENSE_REVIEW,
            AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
            AcquisitionLifecycleState.DECLINED,
        ],
        AcquisitionLifecycleState.AWAITING_SAMPLE: [
            AcquisitionLifecycleState.SAMPLE_RECEIVED,
            AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
        ],
        AcquisitionLifecycleState.SAMPLE_RECEIVED: [
            AcquisitionLifecycleState.SAMPLE_VALIDATION_RUNNING,
        ],
        AcquisitionLifecycleState.SAMPLE_VALIDATION_RUNNING: [
            AcquisitionLifecycleState.SAMPLE_VALIDATION_PASSED,
            AcquisitionLifecycleState.SAMPLE_VALIDATION_FAILED,
        ],
        AcquisitionLifecycleState.SAMPLE_VALIDATION_FAILED: [
            AcquisitionLifecycleState.AWAITING_SAMPLE,  # Request rectified sample
            AcquisitionLifecycleState.DECLINED,
            AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
        ],
        AcquisitionLifecycleState.SAMPLE_VALIDATION_PASSED: [
            AcquisitionLifecycleState.AWAITING_LICENSE_REVIEW,
            AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
        ],
        AcquisitionLifecycleState.AWAITING_LICENSE_REVIEW: [
            AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
            AcquisitionLifecycleState.DECLINED,
        ],
        AcquisitionLifecycleState.AWAITING_HUMAN_DECISION: [
            AcquisitionLifecycleState.APPROVED_FOR_MANUAL_ACQUISITION,
            AcquisitionLifecycleState.DECLINED,
            AcquisitionLifecycleState.AWAITING_SAMPLE,
            AcquisitionLifecycleState.AWAITING_VENDOR_RESPONSE,
        ],
        AcquisitionLifecycleState.APPROVED_FOR_MANUAL_ACQUISITION: [
            AcquisitionLifecycleState.ACQUISITION_IN_PROGRESS,
        ],
        AcquisitionLifecycleState.DECLINED: [
            AcquisitionLifecycleState.AWAITING_VENDOR_CONTACT,  # Reset for alternative vendor
        ],
        AcquisitionLifecycleState.ACQUISITION_IN_PROGRESS: [
            AcquisitionLifecycleState.DATA_RECEIVED,
            AcquisitionLifecycleState.DECLINED,
        ],
        AcquisitionLifecycleState.DATA_RECEIVED: [
            AcquisitionLifecycleState.FULL_VALIDATION_RUNNING,
        ],
        AcquisitionLifecycleState.FULL_VALIDATION_RUNNING: [
            AcquisitionLifecycleState.FULL_VALIDATION_PASSED,
            AcquisitionLifecycleState.FULL_VALIDATION_FAILED,
        ],
        AcquisitionLifecycleState.FULL_VALIDATION_FAILED: [
            AcquisitionLifecycleState.AWAITING_HUMAN_DECISION,
            AcquisitionLifecycleState.DECLINED,
        ],
        AcquisitionLifecycleState.FULL_VALIDATION_PASSED: [
            AcquisitionLifecycleState.ONBOARDING_COMPLETE,
        ],
        AcquisitionLifecycleState.ONBOARDING_COMPLETE: [],
    }

    def __init__(self, initial_state: AcquisitionLifecycleState = AcquisitionLifecycleState.AWAITING_HUMAN_DECISION):
        self.current_state = initial_state
        self.history: List[StateTransitionEvent] = []
        self.authorization_record: Optional[HumanAuthorizationRecord] = None

    def transition(
        self,
        to_state: AcquisitionLifecycleState,
        reason: str,
        evidence_reference: Optional[str] = None,
        actor: str = "SYSTEM",
        validation_run_id: Optional[str] = None,
        auth_record: Optional[HumanAuthorizationRecord] = None,
    ) -> bool:
        """
        Executes a branching state transition with safety and evidence verification.
        """
        # Assert safety policy before any transition
        SafetyPolicy.assert_safety_invariants(context=f"State transition to {to_state.value}")

        allowed = self.VALID_TRANSITIONS.get(self.current_state, [])
        if to_state not in allowed:
            raise ValueError(
                f"Illegal state transition from {self.current_state.value} to {to_state.value}. "
                f"Permitted branches: {[s.value for s in allowed]}"
            )

        # Transition to APPROVED_FOR_MANUAL_ACQUISITION strictly requires valid HumanAuthorizationRecord
        if to_state == AcquisitionLifecycleState.APPROVED_FOR_MANUAL_ACQUISITION:
            if auth_record is None or auth_record.human_decision != "APPROVE":
                raise PermissionError(
                    "Transition to APPROVED_FOR_MANUAL_ACQUISITION strictly requires a verified "
                    "HumanAuthorizationRecord with decision 'APPROVE'. Automated approval is forbidden."
                )
            self.authorization_record = auth_record

        # Transitions to SAMPLE_VALIDATION_PASSED or FULL_VALIDATION_PASSED require validation_run_id
        if to_state in [AcquisitionLifecycleState.SAMPLE_VALIDATION_PASSED, AcquisitionLifecycleState.FULL_VALIDATION_PASSED]:
            if not validation_run_id:
                raise ValueError(f"Transition to {to_state.value} requires an authoritative validation_run_id.")

        event = StateTransitionEvent(
            from_state=self.current_state.value,
            to_state=to_state.value,
            timestamp=datetime.now(timezone.utc).isoformat(),
            transition_reason=reason,
            evidence_reference=evidence_reference,
            actor=actor,
            validation_run_id=validation_run_id,
            authorization_id=auth_record.authorization_id if auth_record else None,
        )

        self.current_state = to_state
        self.history.append(event)
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_state": self.current_state.value,
            "overall_state": "AWAITING_HUMAN_ACQUISITION_DECISION" if self.current_state == AcquisitionLifecycleState.AWAITING_HUMAN_DECISION else self.current_state.value,
            "authorization_record": self.authorization_record.to_dict() if self.authorization_record else None,
            "history": [e.to_dict() for e in self.history],
            "safety_invariants": SafetyPolicy.get_invariants_dict(),
        }
