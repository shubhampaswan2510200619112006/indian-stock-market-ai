"""
Market data API routes.

Endpoints for underlying quotes and historical OHLCV.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.ingestion.base import DataUnavailableError
from src.ingestion.provider_factory import get_market_provider
from src.utils.config import get_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/underlyings")
def list_underlyings():
    """List all configured underlyings."""
    config = get_config()
    return {
        "underlyings": [
            {
                "symbol": u["symbol"],
                "name": u["name"],
                "exchange": u.get("exchange", "NSE"),
                "instrument_type": u.get("instrument_type"),
                "lot_size": u.get("lot_size"),
                "enabled": u.get("enabled", False),
            }
            for u in config.underlyings
        ]
    }


@router.get("/quote/{symbol}")
def get_quote(symbol: str):
    """
    Get the latest quote for an underlying.

    Returns real market data from the configured provider.
    If data is unavailable, returns a clear error.
    """
    try:
        provider = get_market_provider()
        quote = provider.get_quote(symbol.upper())
        return {
            "quote": quote.model_dump(),
            "provider": provider.provider_name,
        }
    except DataUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "DATA_UNAVAILABLE",
                "message": str(e),
                "symbol": symbol,
            },
        )
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ohlcv/{symbol}")
def get_ohlcv(
    symbol: str,
    days: int = Query(default=90, ge=1, le=365, description="Number of days of history"),
    interval: str = Query(default="1d", description="Candle interval"),
):
    """
    Get historical OHLCV data for an underlying.

    Falls back to yfinance if the primary provider doesn't support historical data.
    """
    end = date.today()
    start = end - timedelta(days=days)

    try:
        provider = get_market_provider()
        df = provider.get_ohlcv(symbol.upper(), start, end, interval)
    except DataUnavailableError:
        # Fallback to yfinance for historical data
        try:
            from src.ingestion.yfinance_provider import YFinanceProvider
            yf_provider = YFinanceProvider()
            df = yf_provider.get_ohlcv(symbol.upper(), start, end, interval)
        except DataUnavailableError as e:
            raise HTTPException(
                status_code=503,
                detail={"error": "DATA_UNAVAILABLE", "message": str(e)},
            )

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail={"error": "NO_DATA", "message": f"No OHLCV data for {symbol}"},
        )

    # Convert dates to strings for JSON serialization
    records = df.to_dict(orient="records")
    for r in records:
        if "date" in r and hasattr(r["date"], "isoformat"):
            r["date"] = r["date"].isoformat()

    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "count": len(records),
        "data": records,
    }
