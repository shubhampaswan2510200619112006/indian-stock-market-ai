"""
Phase 8 — Paper Trading & Simulated Live Execution Engine.

SAFETY:
    LIVE EXECUTION = DISABLED
    BROKER CONNECTIONS = NONE
    PAPER EXECUTION = ENABLED

This package provides paper trading simulation without real broker orders.
"""

from src.paper_trading.execution_guard import (
    ALLOW_LIVE_EXECUTION,
    ExecutionGuard,
    LiveExecutionDisabledError,
)
from src.paper_trading.models import (
    ExecutionRefusal,
    MarketState,
    PaperExecutionMode,
    PaperFill,
    PaperFillSource,
    PaperOrder,
    PaperOrderExpiry,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
    PaperPortfolioSnapshot,
    PaperPosition,
    PaperSessionStatus,
    PaperTradeRecord,
    RiskCheckResult,
)
from src.paper_trading.service import PaperTradingService

__all__ = [
    "ALLOW_LIVE_EXECUTION",
    "ExecutionGuard",
    "ExecutionRefusal",
    "LiveExecutionDisabledError",
    "MarketState",
    "PaperExecutionMode",
    "PaperFill",
    "PaperFillSource",
    "PaperOrder",
    "PaperOrderExpiry",
    "PaperOrderSide",
    "PaperOrderStatus",
    "PaperOrderType",
    "PaperPortfolioSnapshot",
    "PaperPosition",
    "PaperSessionStatus",
    "PaperTradeRecord",
    "PaperTradingService",
    "RiskCheckResult",
]
