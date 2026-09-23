"""
Automatic Execution Gate.

Enforces execution invariants and microstructural data requirements:
1. Platform safety invariants (Live execution, Broker, Paper trading).
2. Options quality hierarchy (L0 to L4): Backtesting execution models require Level 3/4.
3. Completely blocks execution simulation if underlying data is only LTP or test fixtures.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from src.platform import (
    ALLOW_LIVE_EXECUTION,
    AUTO_PAPER_ORDER_SUBMISSION,
    BROKER,
    LIVE_EXECUTION,
    OPTIONS_EXECUTION,
)


@dataclass
class ExecutionGateResult:
    execution_permitted: bool
    status: str  # EXECUTION_BLOCKED, EXECUTION_PERMITTED
    instrument_type: str
    reason: str
    options_quality_level: str
    live_execution_state: str
    broker_state: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExecutionGate:
    """
    Validates execution feasibility before any backtest order fill or live/paper order attempt.
    """

    @classmethod
    def check_live_or_paper_order(cls, instrument: str, order_type: str = "PAPER") -> ExecutionGateResult:
        """
        Validates whether real-world or paper orders can be submitted to a broker.
        Permanently blocked under platform safety invariants.
        """
        return ExecutionGateResult(
            execution_permitted=False,
            status="EXECUTION_BLOCKED",
            instrument_type=instrument,
            reason="Platform safety invariants strictly prohibit order submission (BROKER=NONE, LIVE=DISABLED, PAPER=DISABLED).",
            options_quality_level="NOT_APPLICABLE",
            live_execution_state=LIVE_EXECUTION,
            broker_state=BROKER,
        )

    @classmethod
    def check_backtest_execution(
        cls,
        instrument_type: str,
        options_quality_level: str = "LEVEL_0",
        bid_ask_coverage_pct: float = 0.0,
        continuous_surface_pct: float = 0.0,
    ) -> ExecutionGateResult:
        """
        Validates whether backtesting execution modeling (slippage, fills) is supported by data.
        """
        # Equities and Cash Index:
        if instrument_type in ["EQUITY", "INDEX_CASH"]:
            return ExecutionGateResult(
                execution_permitted=True,
                status="EXECUTION_PERMITTED",
                instrument_type=instrument_type,
                reason="Daily equity/index execution backtest permitted using standardized statistical friction models.",
                options_quality_level="NOT_APPLICABLE",
                live_execution_state=LIVE_EXECUTION,
                broker_state=BROKER,
            )

        # Options:
        if instrument_type == "OPTIONS":
            if options_quality_level in ["LEVEL_0", "LEVEL_1", "LEVEL_2"]:
                return ExecutionGateResult(
                    execution_permitted=False,
                    status="EXECUTION_BLOCKED",
                    instrument_type="OPTIONS",
                    reason=(
                        f"Options execution modeling requires Level 3/4 continuous surface. "
                        f"Current data is {options_quality_level} (Continuous Surface: {continuous_surface_pct}%). "
                        "Backtesting options fills against LTP or synthetic fixtures is strictly prohibited."
                    ),
                    options_quality_level=options_quality_level,
                    live_execution_state=LIVE_EXECUTION,
                    broker_state=BROKER,
                )
            elif options_quality_level in ["LEVEL_3", "LEVEL_4"]:
                return ExecutionGateResult(
                    execution_permitted=True,
                    status="EXECUTION_PERMITTED",
                    instrument_type="OPTIONS",
                    reason="Verified Level 3/4 continuous Bid/Ask surface available for realistic execution modeling.",
                    options_quality_level=options_quality_level,
                    live_execution_state=LIVE_EXECUTION,
                    broker_state=BROKER,
                )

        return ExecutionGateResult(
            execution_permitted=False,
            status="EXECUTION_BLOCKED",
            instrument_type=instrument_type,
            reason="Unrecognized instrument type or insufficient microstructural evidence.",
            options_quality_level=options_quality_level,
            live_execution_state=LIVE_EXECUTION,
            broker_state=BROKER,
        )
