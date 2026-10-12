"""
Phase 8 — Paper Trading API Routes.

Every response includes execution_mode: PAPER_TRADE.
No endpoint can submit a broker order.
LIVE execution requests are rejected with explicit errors.
Endpoints enforce authentication, multi-tenant per-user isolation,
and rate limiting.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.security import (
    get_current_user,
    get_optional_user_paper_service,
    get_user_paper_service,
    trading_rate_limiter,
)
from src.auth.service import UserAccount
from src.paper_trading.execution_guard import ExecutionGuard, LiveExecutionDisabledError
from src.paper_trading.service import PaperTradingService

router = APIRouter(prefix="/api/v1/paper", tags=["Paper Trading"])


class PaperOrderRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=25)
    side: str = Field(..., pattern="^(?i)(BUY|SELL)$")
    quantity: int = Field(..., gt=0, le=100000)
    order_type: str = Field("MARKET", pattern="^(?i)(MARKET|LIMIT|STOP|STOP_LIMIT)$")
    limit_price: Optional[float] = Field(None, gt=0)
    stop_price: Optional[float] = Field(None, gt=0)
    instrument_type: str = "INDEX"
    strategy_name: Optional[str] = None
    strike: Optional[float] = None
    expiry_date: Optional[str] = None
    option_type: Optional[str] = None
    execution_mode: str = "PAPER"


class MarketUpdateRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=25)
    bid: Optional[float] = Field(None, ge=0)
    ask: Optional[float] = Field(None, ge=0)
    ltp: Optional[float] = Field(None, ge=0)
    data_status: str = "DELAYED"
    source_provider: str = "YFINANCE"


class ResetRequest(BaseModel):
    confirm: bool = False


class TripBreakerRequest(BaseModel):
    reason: str = Field("MANUAL_EMERGENCY_HALT", max_length=100)


class ClosePositionRequest(BaseModel):
    quantity: Optional[int] = Field(None, gt=0)


@router.post("/orders", dependencies=[Depends(trading_rate_limiter)])
async def submit_paper_order(
    request: PaperOrderRequest,
    user: UserAccount = Depends(get_current_user),
    service: PaperTradingService = Depends(get_user_paper_service),
):
    """Submit a paper order for the authenticated user. NO LIVE ORDERS."""
    # Reject any attempt to use LIVE mode
    if request.execution_mode.upper() == "LIVE":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "LIVE EXECUTION IS NOT IMPLEMENTED",
                "message": "BROKER CONNECTION DISABLED. Only PAPER mode is available.",
                "execution_mode": "PAPER_TRADE",
                "LIVE_EXECUTION": "DISABLED",
            },
        )

    try:
        ExecutionGuard.validate_execution_mode(request.execution_mode)
    except LiveExecutionDisabledError as e:
        raise HTTPException(status_code=403, detail=str(e))

    result = service.place_order(
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        order_type=request.order_type,
        limit_price=request.limit_price,
        stop_price=request.stop_price,
        instrument_type=request.instrument_type,
        strategy_name=request.strategy_name,
        strike=request.strike,
        option_type=request.option_type,
    )
    return result


@router.get("/orders")
async def get_paper_orders(
    status: Optional[str] = Query(None),
    user: UserAccount = Depends(get_current_user),
    service: PaperTradingService = Depends(get_user_paper_service),
):
    """Get paper order history for the authenticated user."""
    return service.get_orders(status=status)


@router.delete("/orders/{order_id}")
async def cancel_paper_order(
    order_id: str,
    user: UserAccount = Depends(get_current_user),
    service: PaperTradingService = Depends(get_user_paper_service),
):
    """Cancel a paper order for the authenticated user."""
    order = service.order_manager.cancel_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "execution_mode": "PAPER_TRADE",
        "order_id": order.order_id,
        "status": order.status.value,
    }


@router.post("/process")
async def process_market_update(
    request: MarketUpdateRequest,
    service: PaperTradingService = Depends(get_optional_user_paper_service),
):
    """Process a market data update for paper trading."""
    result = service.process_market_update(
        symbol=request.symbol,
        bid=request.bid,
        ask=request.ask,
        ltp=request.ltp,
        provider_timestamp=datetime.now(timezone.utc),
        data_status=request.data_status,
        source_provider=request.source_provider,
    )
    return result


@router.get("/portfolio")
async def get_paper_portfolio(
    user: UserAccount = Depends(get_current_user),
    service: PaperTradingService = Depends(get_user_paper_service),
):
    """Get paper portfolio summary for the authenticated user."""
    return service.get_portfolio_summary()


@router.get("/positions")
async def get_paper_positions(
    user: UserAccount = Depends(get_current_user),
    service: PaperTradingService = Depends(get_user_paper_service),
):
    """Get open paper positions for the authenticated user."""
    return service.get_positions()


@router.get("/history")
async def get_paper_trade_history(
    user: UserAccount = Depends(get_current_user),
    service: PaperTradingService = Depends(get_user_paper_service),
):
    """Get paper trade history for the authenticated user."""
    return service.get_trade_history()


@router.get("/risk")
async def get_paper_risk_status(
    service: PaperTradingService = Depends(get_optional_user_paper_service),
):
    """Get paper risk engine status."""
    return service.get_risk_status()


@router.get("/status")
async def get_paper_session_status(
    service: PaperTradingService = Depends(get_optional_user_paper_service),
):
    """Get paper session status including safety verification."""
    return service.get_session_status()


@router.post("/reset", dependencies=[Depends(trading_rate_limiter)])
async def reset_paper_account(
    request: ResetRequest,
    user: UserAccount = Depends(get_current_user),
    service: PaperTradingService = Depends(get_user_paper_service),
):
    """Reset paper trading account for the authenticated user. Requires confirmation."""
    return service.reset_paper_account(confirm=request.confirm)


@router.post("/risk/trip")
async def trip_emergency_breaker(
    request: TripBreakerRequest,
    user: UserAccount = Depends(get_current_user),
    service: PaperTradingService = Depends(get_user_paper_service),
):
    """Manually trip emergency circuit breakers and cancel pending orders for authenticated user."""
    return service.trip_breaker(reason=request.reason)


@router.post("/risk/reset")
async def reset_circuit_breakers(
    user: UserAccount = Depends(get_current_user),
    service: PaperTradingService = Depends(get_user_paper_service),
):
    """Reset paper trading circuit breakers for authenticated user."""
    return service.reset_breakers()


@router.post("/positions/{position_id}/close")
async def close_paper_position(
    position_id: str,
    request: Optional[ClosePositionRequest] = None,
    user: UserAccount = Depends(get_current_user),
    service: PaperTradingService = Depends(get_user_paper_service),
):
    """Close an open paper position with offsetting execution for authenticated user."""
    qty = request.quantity if request else None
    result = service.close_position(position_id, quantity=qty)
    if result.get("status") == "REJECTED":
        raise HTTPException(status_code=400, detail=result.get("rejection_reason"))
    return result
