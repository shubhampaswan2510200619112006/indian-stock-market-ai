"""
Phase 15A Centralized Safety Policy.

Enforces read-only safety accessors and multi-point invariant assertions.
Safety flags are immutable by policy; no Phase 15A code provides methods to modify them.
Validates safety before intake, before normalization, and before certification handoff.
"""

from __future__ import annotations

from typing import Dict, Any


class SafetyViolationError(RuntimeError):
    """Raised when any platform safety invariant is violated."""
    pass


class SafetyPolicy:
    """
    Centralized read-only policy manager for platform safety invariants.
    """

    _BROKER: str = "NONE"
    _LIVE_EXECUTION: str = "DISABLED"
    _AUTO_PAPER_ORDER_SUBMISSION: str = "DISABLED"
    _OPTIONS_EXECUTION: str = "BLOCKED"
    _NEW_UNPREREGISTERED_ALPHA_RESEARCH: str = "DISABLED"
    _UNLIMITED_PARAMETER_SEARCH: str = "DISABLED"
    _STRATEGY_OPTIMIZATION: str = "DISABLED"
    _AUTOMATED_VENDOR_CONTACT: str = "DISABLED"
    _AUTOMATED_DATA_PURCHASE: str = "DISABLED"
    _PURCHASE_AUTHORIZED: bool = False
    _HUMAN_DECISION_REQUIRED: bool = True
    _PHASE_15_UNLOCKED: bool = False

    @classmethod
    def get_broker(cls) -> str:
        return cls._BROKER

    @classmethod
    def get_live_execution(cls) -> str:
        return cls._LIVE_EXECUTION

    @classmethod
    def get_auto_paper_order_submission(cls) -> str:
        return cls._AUTO_PAPER_ORDER_SUBMISSION

    @classmethod
    def get_options_execution(cls) -> str:
        return cls._OPTIONS_EXECUTION

    @classmethod
    def get_new_alpha_research(cls) -> str:
        return cls._NEW_UNPREREGISTERED_ALPHA_RESEARCH

    @classmethod
    def get_unlimited_parameter_search(cls) -> str:
        return cls._UNLIMITED_PARAMETER_SEARCH

    @classmethod
    def get_strategy_optimization(cls) -> str:
        return cls._STRATEGY_OPTIMIZATION

    @classmethod
    def get_automated_vendor_contact(cls) -> str:
        return cls._AUTOMATED_VENDOR_CONTACT

    @classmethod
    def get_automated_data_purchase(cls) -> str:
        return cls._AUTOMATED_DATA_PURCHASE

    @classmethod
    def get_purchase_authorized(cls) -> bool:
        return cls._PURCHASE_AUTHORIZED

    @classmethod
    def get_human_decision_required(cls) -> bool:
        return cls._HUMAN_DECISION_REQUIRED

    @classmethod
    def get_phase_15_unlocked(cls) -> bool:
        return cls._PHASE_15_UNLOCKED

    @classmethod
    def get_invariants_dict(cls) -> Dict[str, Any]:
        return {
            "broker": cls._BROKER,
            "live_execution": cls._LIVE_EXECUTION,
            "auto_paper_order_submission": cls._AUTO_PAPER_ORDER_SUBMISSION,
            "options_execution": cls._OPTIONS_EXECUTION,
            "new_alpha_research": cls._NEW_UNPREREGISTERED_ALPHA_RESEARCH,
            "unlimited_parameter_search": cls._UNLIMITED_PARAMETER_SEARCH,
            "strategy_optimization": cls._STRATEGY_OPTIMIZATION,
            "automated_vendor_contact": cls._AUTOMATED_VENDOR_CONTACT,
            "automated_data_purchase": cls._AUTOMATED_DATA_PURCHASE,
            "purchase_authorized": cls._PURCHASE_AUTHORIZED,
            "human_decision_required": cls._HUMAN_DECISION_REQUIRED,
            "phase_15_unlocked": cls._PHASE_15_UNLOCKED,
        }

    @classmethod
    def assert_safety_invariants(cls, context: str = "general") -> None:
        """
        Validates safety invariants. If any invariant is compromised, raises SafetyViolationError.
        """
        errors = []

        if cls.get_broker() != "NONE":
            errors.append(f"BROKER must be 'NONE', observed: {cls.get_broker()}")
        if cls.get_live_execution() != "DISABLED":
            errors.append(f"LIVE_EXECUTION must be 'DISABLED', observed: {cls.get_live_execution()}")
        if cls.get_auto_paper_order_submission() != "DISABLED":
            errors.append(f"AUTO_PAPER_ORDER_SUBMISSION must be 'DISABLED', observed: {cls.get_auto_paper_order_submission()}")
        if cls.get_options_execution() != "BLOCKED":
            errors.append(f"OPTIONS_EXECUTION must be 'BLOCKED', observed: {cls.get_options_execution()}")
        if cls.get_new_alpha_research() != "DISABLED":
            errors.append(f"NEW_UNPREREGISTERED_ALPHA_RESEARCH must be 'DISABLED', observed: {cls.get_new_alpha_research()}")
        if cls.get_unlimited_parameter_search() != "DISABLED":
            errors.append(f"UNLIMITED_PARAMETER_SEARCH must be 'DISABLED', observed: {cls.get_unlimited_parameter_search()}")
        if cls.get_strategy_optimization() != "DISABLED":
            errors.append(f"STRATEGY_OPTIMIZATION must be 'DISABLED', observed: {cls.get_strategy_optimization()}")
        if cls.get_automated_vendor_contact() != "DISABLED":
            errors.append(f"AUTOMATED_VENDOR_CONTACT must be 'DISABLED', observed: {cls.get_automated_vendor_contact()}")
        if cls.get_automated_data_purchase() != "DISABLED":
            errors.append(f"AUTOMATED_DATA_PURCHASE must be 'DISABLED', observed: {cls.get_automated_data_purchase()}")
        if cls.get_purchase_authorized() is not False:
            errors.append(f"PURCHASE_AUTHORIZED must be False, observed: {cls.get_purchase_authorized()}")
        if cls.get_human_decision_required() is not True:
            errors.append(f"HUMAN_DECISION_REQUIRED must be True, observed: {cls.get_human_decision_required()}")
        if cls.get_phase_15_unlocked() is not False:
            errors.append(f"PHASE_15_UNLOCKED must be False, observed: {cls.get_phase_15_unlocked()}")

        if errors:
            raise SafetyViolationError(f"Safety invariant violation in [{context}]: {'; '.join(errors)}")
