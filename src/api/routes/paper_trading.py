"""
Phase 8 — Paper Trading API Routes.

Every response includes execution_mode: PAPER_TRADE.
No endpoint can submit a broker order.
LIVE execution requests are rejected with explicit errors.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.paper_trading.execution_guard import ExecutionGuard, LiveExecutionDisabledError
from src.paper_trading.service import PaperTradingService

router = APIRouter(prefix="/api/v1/paper", tags=["Paper Trading"])

# Singleton service instance
_service: Optional[PaperTradingService] = None


def _get_service() -> PaperTradingService:
    global _service
    if _service is None:
        _service = PaperTradingService()
    return _service


class PaperOrderRequest(BaseModel):
    symbol: str
    side: str  # BUY, SELL
    quantity: int
    order_type: str = "MARKET"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    instrument_type: str = "INDEX"
    strategy_name: Optional[str] = None
    strike: Optional[float] = None
    expiry_date: Optional[str] = None
    option_type: Optional[str] = None
    execution_mode: str = "PAPER"


class MarketUpdateRequest(BaseModel):
    symbol: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    ltp: Optional[float] = None
    data_status: str = "DELAYED"
    source_provider: str = "YFINANCE"


class ResetRequest(BaseModel):
    confirm: bool = False


@router.post("/orders")
async def submit_paper_order(request: PaperOrderRequest):
    """Submit a paper order. NO LIVE ORDERS."""
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

    service = _get_service()
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
async def get_paper_orders(status: Optional[str] = Query(None)):
    """Get paper order history."""
    service = _get_service()
    return service.get_orders(status=status)


@router.delete("/orders/{order_id}")
async def cancel_paper_order(order_id: str):
    """Cancel a paper order."""
    service = _get_service()
    order = service.order_manager.cancel_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "execution_mode": "PAPER_TRADE",
        "order_id": order.order_id,
        "status": order.status.value,
    }


@router.post("/process")
async def process_market_update(request: MarketUpdateRequest):
    """Process a market data update for paper trading."""
    from datetime import datetime, timezone
    service = _get_service()
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
async def get_paper_portfolio():
    """Get paper portfolio summary."""
    service = _get_service()
    return service.get_portfolio_summary()


@router.get("/positions")
async def get_paper_positions():
    """Get open paper positions."""
    service = _get_service()
    return service.get_positions()


@router.get("/history")
async def get_paper_trade_history():
    """Get paper trade history."""
    service = _get_service()
    return service.get_trade_history()


@router.get("/risk")
async def get_paper_risk_status():
    """Get paper risk engine status."""
    service = _get_service()
    return service.get_risk_status()


@router.get("/status")
async def get_paper_session_status():
    """Get paper session status including safety verification."""
    service = _get_service()
    return service.get_session_status()


@router.post("/reset")
async def reset_paper_account(request: ResetRequest):
    """Reset paper trading account. Requires confirmation."""
    service = _get_service()
    return service.reset_paper_account(confirm=request.confirm)
