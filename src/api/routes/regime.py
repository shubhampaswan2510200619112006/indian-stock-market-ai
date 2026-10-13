"""
Market Regime API endpoints.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.features.market_regime import MarketRegimeEngine
from src.ingestion.provider_factory import get_market_data_provider
from src.ingestion.schemas import MarketRegimeResult
from src.ingestion.yfinance_provider import YFinanceProvider

router = APIRouter(prefix="/regime", tags=["Market Regime"])


@router.get("/current", response_model=MarketRegimeResult)
@router.get("/current/{symbol}", response_model=MarketRegimeResult)
def get_current_market_regime(
    symbol: str = "NIFTY",
):
    """
    Evaluates current market regime combining NIFTY, BANK NIFTY, technical structure,
    realized vol, and India VIX.
    """
    provider = get_market_data_provider()
    end_date = date.today()
    start_date = end_date - timedelta(days=150)

    try:
        nifty_df = provider.get_ohlcv(symbol="NIFTY", start=start_date, end=end_date)
        banknifty_df = None
        try:
            banknifty_df = provider.get_ohlcv(symbol="BANKNIFTY", start=start_date, end=end_date)
        except Exception:
            pass

        vix_val = None
        if isinstance(provider, YFinanceProvider):
            vix_val = provider.get_india_vix()

        engine = MarketRegimeEngine()
        regime_res = engine.evaluate_regime(
            nifty_df=nifty_df,
            banknifty_df=banknifty_df,
            vix_value=vix_val,
            symbol=symbol,
        )

        return regime_res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating market regime: {e}")
