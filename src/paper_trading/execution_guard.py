"""
Phase 8 — Execution Guard.

Hard safety boundary that architecturally prevents live broker execution.
No configuration, environment variable, or runtime flag can override this.

INVARIANT:
    ALLOW_LIVE_EXECUTION = False
    This is not configurable. It is a compile-time constant.
"""

from __future__ import annotations


# =============================================================================
# HARD SAFETY CONSTANT — NOT CONFIGURABLE
# =============================================================================
# This is NOT read from YAML, env, or any external source.
# It is a source-code constant. Changing it requires modifying this file.
ALLOW_LIVE_EXECUTION: bool = False


class LiveExecutionDisabledError(Exception):
    """Raised when any code path attempts to initialize live execution."""
    pass


class ExecutionGuard:
    """
    Non-bypassable safety guard preventing live broker execution.

    RULES:
    1. ALLOW_LIVE_EXECUTION is a source-code constant set to False.
    2. No YAML config, env var, API param, or UI control can override it.
    3. Any attempt to invoke LIVE mode raises LiveExecutionDisabledError.
    4. No broker API integration exists in the codebase.
    """

    @staticmethod
    def validate_execution_mode(mode: str) -> None:
        """
        Validate that the requested execution mode is permitted.

        Raises LiveExecutionDisabledError if LIVE mode is requested,
        regardless of any external configuration.
        """
        mode_upper = mode.upper().strip()

        if mode_upper == "LIVE":
            raise LiveExecutionDisabledError(
                "LIVE EXECUTION IS NOT IMPLEMENTED. "
                "BROKER CONNECTION DISABLED. "
                "Phase 8 supports PAPER execution mode only. "
                "No broker API integration exists in this system."
            )

        if mode_upper not in ("PAPER", "BACKTEST"):
            raise LiveExecutionDisabledError(
                f"Unknown execution mode: '{mode}'. "
                f"Only PAPER and BACKTEST modes are available. "
                f"LIVE EXECUTION IS NOT IMPLEMENTED."
            )

    @staticmethod
    def is_live_enabled() -> bool:
        """Always returns False. Live execution is architecturally disabled."""
        return False

    @staticmethod
    def get_execution_status() -> dict:
        """Return current execution safety status."""
        return {
            "LIVE_EXECUTION": "DISABLED",
            "BROKER_CONNECTIONS": "NONE",
            "PAPER_EXECUTION": "ENABLED",
            "BACKTEST_EXECUTION": "ENABLED",
            "ALLOW_LIVE_EXECUTION": ALLOW_LIVE_EXECUTION,
            "safety_message": (
                "This system does NOT send real orders. "
                "Broker execution is architecturally unavailable."
            ),
        }

    @staticmethod
    def assert_paper_mode() -> None:
        """Assert that we are in paper mode. For use in critical code paths."""
        if ALLOW_LIVE_EXECUTION:
            # Even if someone modifies the constant, this is a second check
            raise LiveExecutionDisabledError(
                "CRITICAL SAFETY VIOLATION: ALLOW_LIVE_EXECUTION must be False. "
                "Live execution is not implemented."
            )
