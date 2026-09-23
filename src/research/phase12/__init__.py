"""
Phase 12 — Data Acquisition, Validation Framework & Onboarding Architecture.

This package defines the formal data engineering, acquisition evaluation,
onboarding validation, and readiness gate framework for the platform.

ABSOLUTE SAFETY INVARIANTS:
Zero broker connections, zero live trading, zero automated paper execution,
zero unpreregistered alpha research, and zero options execution simulations.
"""

from typing import Final

BROKER: Final[str] = "NONE"
LIVE_EXECUTION: Final[str] = "DISABLED"
AUTO_PAPER_ORDER_SUBMISSION: Final[str] = "DISABLED"
OPTIONS_EXECUTION: Final[str] = "BLOCKED"
NEW_UNPREREGISTERED_ALPHA_RESEARCH: Final[str] = "DISABLED"
UNLIMITED_PARAMETER_SEARCH: Final[str] = "DISABLED"
STRATEGY_OPTIMIZATION: Final[str] = "DISABLED"

ALLOW_LIVE_EXECUTION: Final[bool] = False
ALLOW_BROKER_CONNECTION: Final[bool] = False
ALLOW_PAPER_AUTOMATION: Final[bool] = False
ALLOW_OPTIONS_BACKTEST: Final[bool] = False
PURCHASE_AUTHORIZED: Final[bool] = False
HUMAN_DECISION_REQUIRED: Final[bool] = True

__all__ = [
    "BROKER",
    "LIVE_EXECUTION",
    "AUTO_PAPER_ORDER_SUBMISSION",
    "OPTIONS_EXECUTION",
    "NEW_UNPREREGISTERED_ALPHA_RESEARCH",
    "UNLIMITED_PARAMETER_SEARCH",
    "STRATEGY_OPTIMIZATION",
    "ALLOW_LIVE_EXECUTION",
    "ALLOW_BROKER_CONNECTION",
    "ALLOW_PAPER_AUTOMATION",
    "ALLOW_OPTIONS_BACKTEST",
    "PURCHASE_AUTHORIZED",
    "HUMAN_DECISION_REQUIRED",
]
