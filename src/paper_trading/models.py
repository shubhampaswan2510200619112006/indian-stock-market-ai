"""
Phase 8 — Paper Trading & Simulated Live Execution Engine.

Core data models, enums, and Pydantic schemas for the paper trading system.

CRITICAL INVARIANTS:
- execution_mode = PAPER on every model
- LIVE execution is architecturally disabled
- Every fill requires complete provenance
- No synthetic/fabricated execution prices
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class PaperExecutionMode(str, Enum):
    """Execution mode. LIVE is defined but architecturally DISABLED."""
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    LIVE = "LIVE"  # DISABLED — ExecutionGuard prevents initialization


class PaperOrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PaperOrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class PaperOrderStatus(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class PaperOrderExpiry(str, Enum):
    DAY = "DAY"
    GTC = "GTC"  # Good Till Cancelled
    GTD = "GTD"  # Good Till Date


class PaperFillSource(str, Enum):
    """Describes the origin of a fill price."""
    PROVIDER_BID = "PROVIDER_BID"
    PROVIDER_ASK = "PROVIDER_ASK"
    PROVIDER_BID_WITH_SLIPPAGE = "PROVIDER_BID_WITH_SLIPPAGE"
    PROVIDER_ASK_WITH_SLIPPAGE = "PROVIDER_ASK_WITH_SLIPPAGE"


class PaperSessionStatus(str, Enum):
    STARTED = "STARTED"
    PAUSED = "PAUSED"
    RESUMED = "RESUMED"
    STOPPED = "STOPPED"


class MarketState(str, Enum):
    PRE_OPEN = "PRE_OPEN"
    MARKET_OPEN = "MARKET_OPEN"
    MARKET_CLOSED = "MARKET_CLOSED"


# =============================================================================
# Utility
# =============================================================================

def _generate_id(prefix: str = "") -> str:
    """Generate a deterministic-format unique ID."""
    return f"{prefix}{uuid.uuid4().hex[:16]}"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================================
# PaperOrder
# =============================================================================

class PaperOrder(BaseModel):
    """
    Complete paper order with full lifecycle information.
    All timestamps are timezone-aware.
    """
    order_id: str = Field(default_factory=lambda: _generate_id("ORD-"))
    created_at: datetime = Field(default_factory=_now_utc)
    decision_timestamp: Optional[datetime] = None
    session_id: Optional[str] = None

    # Instrument
    symbol: str
    instrument_type: str = "INDEX"  # INDEX, STOCK, INDEX_OPTION, STOCK_OPTION
    strike: Optional[float] = None
    expiry: Optional[date] = None
    option_type: Optional[str] = None  # CE, PE

    # Order details
    side: PaperOrderSide
    quantity: int
    order_type: PaperOrderType = PaperOrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None

    # Strategy / signal
    strategy_id: Optional[str] = None
    strategy_name: Optional[str] = None
    signal_id: Optional[str] = None
    model_version: Optional[str] = None

    # Execution mode — always PAPER
    execution_mode: str = "PAPER"

    # Status lifecycle
    status: PaperOrderStatus = PaperOrderStatus.PENDING
    filled_quantity: int = 0
    average_fill_price: Optional[float] = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Expiry
    expiry_type: PaperOrderExpiry = PaperOrderExpiry.DAY
    expiry_date: Optional[date] = None

    # Stop trigger state
    stop_triggered: bool = False


# =============================================================================
# =============================================================================
# MarketObservation
# =============================================================================

class MarketObservation(BaseModel):
    """
    Normalized market quote observation with genuine provenance.
    """
    observation_id: str = Field(default_factory=lambda: _generate_id("OBS-"))
    symbol: str
    provider: str
    provider_timestamp: datetime
    received_timestamp: datetime
    data_status: str  # REAL_TIME, DELAYED, STALE, UNAVAILABLE, ERROR
    bid: Optional[float] = None
    ask: Optional[float] = None
    last_price: Optional[float] = None
    spread: Optional[float] = None
    quote_age_seconds: float = 0.0


# =============================================================================
# PaperFill
# =============================================================================

class PaperFill(BaseModel):
    """
    A single fill event for a paper order with complete provenance.
    Every fill MUST have complete provenance or be rejected.
    """
    fill_id: str = Field(default_factory=lambda: _generate_id("FILL-"))
    order_id: str
    observation_id: str = Field(default_factory=lambda: _generate_id("OBS-"))
    symbol: str
    side: Optional[PaperOrderSide] = None

    fill_quantity: int
    fill_price: float
    fill_timestamp: datetime

    # Provenance — ALL MANDATORY for a valid fill
    provider: str = ""
    source_provider: str = ""
    provider_timestamp: datetime
    received_timestamp: datetime
    order_submission_timestamp: Optional[datetime] = None
    decision_timestamp: Optional[datetime] = None
    execution_timestamp: datetime

    # Quotes at execution
    bid_at_execution: Optional[float] = None
    ask_at_execution: Optional[float] = None
    spread_at_execution: Optional[float] = None

    price_source: PaperFillSource
    price_source_description: str

    data_status_at_fill: str  # From RealTimeDataStatus
    slippage_applied: float
    transaction_costs: float
    quote_age_seconds: float

    execution_mode: str = "PAPER"

    def __init__(self, **data: Any):
        super().__init__(**data)
        # Harmonize provider and source_provider
        if not self.provider and self.source_provider:
            self.provider = self.source_provider
        elif not self.source_provider and self.provider:
            self.source_provider = self.provider

    @property
    def quantity(self) -> int:
        return self.fill_quantity

    @property
    def price(self) -> float:
        return self.fill_price

    @property
    def data_status(self) -> str:
        return self.data_status_at_fill

    @property
    def slippage(self) -> float:
        return self.slippage_applied

    def validate_provenance(self) -> bool:
        """Verify all mandatory provenance fields are present and consistent."""
        prov = self.provider or self.source_provider
        if not all([
            self.fill_id,
            self.order_id,
            self.symbol,
            self.provider_timestamp,
            self.received_timestamp,
            self.execution_timestamp,
            prov,
            self.price_source,
            self.data_status_at_fill,
        ]):
            return False

        # execution_timestamp >= provider_timestamp
        if self.execution_timestamp < self.provider_timestamp:
            return False

        # If order_submission_timestamp provided: received_timestamp >= order_submission_timestamp
        if self.order_submission_timestamp:
            if self.received_timestamp < self.order_submission_timestamp:
                return False

        return True


# =============================================================================
# PaperPosition
# =============================================================================

class PaperPosition(BaseModel):
    """Aggregated paper position for a single instrument."""
    position_id: str = Field(default_factory=lambda: _generate_id("POS-"))
    symbol: str
    instrument_type: str = "INDEX"

    quantity: int = 0
    average_entry_price: float = 0.0
    current_market_price: Optional[float] = None
    market_value: Optional[float] = None
    realized_pnl: float = 0.0
    unrealized_pnl: Optional[float] = None

    entry_timestamp: Optional[datetime] = None
    last_mark_timestamp: Optional[datetime] = None
    last_mark_status: str = "UNAVAILABLE"  # MARKET_PRICE, MARK_UNAVAILABLE

    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy: Optional[str] = None

    # Options fields — UNAVAILABLE unless verified live data exists
    strike: Optional[float] = None
    expiry: Optional[date] = None
    option_type: Optional[str] = None
    greeks_status: str = "UNAVAILABLE"  # AVAILABLE or UNAVAILABLE
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None

    execution_mode: str = "PAPER"

    @property
    def is_open(self) -> bool:
        return self.quantity != 0


# =============================================================================
# PaperPortfolioSnapshot
# =============================================================================

class PaperPortfolioSnapshot(BaseModel):
    """Point-in-time snapshot of the paper portfolio."""
    timestamp: datetime = Field(default_factory=_now_utc)
    session_id: Optional[str] = None

    cash: float
    equity: float
    available_cash: float
    margin_used: float = 0.0
    gross_exposure: float = 0.0
    net_exposure: float = 0.0

    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0

    peak_equity: float
    current_drawdown_pct: float = 0.0
    max_drawdown_pct: float = 0.0

    open_positions_count: int = 0
    net_greeks_status: str = "UNAVAILABLE"
    net_delta: Optional[float] = None
    net_gamma: Optional[float] = None
    net_theta: Optional[float] = None
    net_vega: Optional[float] = None

    execution_mode: str = "PAPER"


# =============================================================================
# PaperTradeRecord
# =============================================================================

class PaperTradeRecord(BaseModel):
    """Complete audit record for a closed paper trade."""
    trade_id: str = Field(default_factory=lambda: _generate_id("TRD-"))
    session_id: Optional[str] = None
    decision_id: Optional[str] = None

    symbol: str
    strategy: Optional[str] = None
    direction: str  # LONG, SHORT
    entry_timestamp: datetime
    exit_timestamp: Optional[datetime] = None

    quantity: int
    entry_price: float
    exit_price: Optional[float] = None

    gross_pnl: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    net_pnl: float = 0.0
    holding_period_seconds: float = 0.0

    model_version: Optional[str] = None
    regime: Optional[str] = None
    news_context: Optional[str] = None
    options_context: Optional[str] = None
    risk_decision: Optional[str] = None
    execution_quality: Optional[Dict[str, Any]] = None

    execution_mode: str = "PAPER"
    evidence_label: str = "VERY_LIMITED_EVIDENCE"


# =============================================================================
# RiskCheckResult
# =============================================================================

class RiskCheckResult(BaseModel):
    """Result of pre-trade risk evaluation."""
    is_approved: bool
    rejection_reasons: List[str] = Field(default_factory=list)
    risk_metrics: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=_now_utc)


# =============================================================================
# Execution Refusal
# =============================================================================

class ExecutionRefusal(BaseModel):
    """Structured execution refusal with reason."""
    order_id: str
    reason: str
    timestamp: datetime = Field(default_factory=_now_utc)
    details: Optional[str] = None
    data_status: Optional[str] = None
    provider_status: Optional[str] = None
    market_status: Optional[str] = None
