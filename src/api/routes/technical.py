"""
Technical Analysis API endpoints.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.features.price_action import PriceActionEngine
from src.features.technical import extract_latest_features
from src.features.volatility import calculate_realized_volatility_table
from src.ingestion.base import DataUnavailableError
from src.ingestion.provider_factory import get_market_data_provider
from src.ingestion.schemas import TechnicalFeatures, TimeFrame

router = APIRouter(prefix="/technical", tags=["Technical Analysis"])


@router.get("/{symbol}", response_model=TechnicalFeatures)
def get_technical_analysis(
    symbol: str,
    timeframe: str = Query("1d", description="Timeframe: 1d, 1w, 1h, 15m, 5m"),
    days: int = Query(100, ge=20, le=500, description="Lookback window in days"),
):
    """
    Computes timestamp-safe technical features and candlestick pattern analysis for a symbol.
    """
    provider = get_market_data_provider()
    end_date = date.today()
    start_date = end_date - timedelta(days=days * 2)  # Extra buffer for weekends

    try:
        tf_enum = TimeFrame(timeframe)
    except ValueError:
        tf_enum = TimeFrame.DAILY

    try:
        df = provider.get_ohlcv(symbol=symbol, start=start_date, end=end_date)
        if df.empty or len(df) < 10:
            raise HTTPException(status_code=404, detail=f"Insufficient price data for symbol {symbol}")

        # Extract technical features
        features = extract_latest_features(df, symbol=symbol, timeframe=tf_enum)

        # Detect candlestick patterns
        pa_engine = PriceActionEngine(timeframe=tf_enum)
        patterns = pa_engine.detect_patterns(df)
        features.patterns = patterns

        return features
    except DataUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing technical analysis: {e}")


@router.get("/volatility/{symbol}")
def get_volatility_analysis(
    symbol: str,
    days: int = Query(120, ge=30, le=500),
):
    """
    Computes 5D, 10D, 20D, 30D, and 60D annualized realized volatility.
    """
    provider = get_market_data_provider()
    end_date = date.today()
    start_date = end_date - timedelta(days=days * 2)

    try:
        df = provider.get_ohlcv(symbol=symbol, start=start_date, end=end_date)
        if df.empty or len(df) < 10:
            raise HTTPException(status_code=404, detail=f"Insufficient price history for {symbol}")

        rv_table = calculate_realized_volatility_table(df, windows=[5, 10, 20, 30, 60])
        return {
            "symbol": symbol.upper(),
            "timestamp": datetime.now().isoformat(),
            "realized_volatility": rv_table,
            "annualization_factor": "sqrt(252)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing volatility: {e}")
