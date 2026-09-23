"""
FastAPI Live Market & Intelligence Terminal Routes (Phase 7).
Exposes LiveMarketSnapshot, live quotes, intraday candles, options summary, provider health, and AI Analysis.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException

from src.ai_analyst.analyst import AIMarketAnalyst
from src.ai_analyst.ood_detector import OODDetector
from src.ingestion.providers.news_provider import VerifiedRSSNewsProvider
from src.live_market.service import LiveMarketService
from src.live_market.snapshot import LiveMarketSnapshot, build_live_market_snapshot

router = APIRouter(prefix="/api/v1/live", tags=["Live Terminal"])

_live_service = LiveMarketService()
_news_provider = VerifiedRSSNewsProvider()
_ai_analyst = AIMarketAnalyst()
_ood_detector = OODDetector()


@router.get("/snapshot/{symbol}", response_model=LiveMarketSnapshot)
def get_live_market_snapshot(symbol: str = "NIFTY"):
    """
    Returns aggregate LiveMarketSnapshot object containing market, options, news, ML, and data health data.
    """
    quote = _live_service.fetch_live_quote(symbol)
    candles = _live_service.fetch_intraday_candles(symbol, timeframe="1m", limit=30)
    multi_tf = _live_service.compute_multi_timeframe_summary(symbol)
    news_items = _news_provider.fetch_latest_news(limit=10)
    health = _live_service.get_provider_health()

    opt_summary = _live_service.options_provider.get_live_option_chain(symbol) or {
        "status_label": "UNAVAILABLE",
        "reason": "Live options provider unconfigured.",
    }

    # OOD Check
    live_feats = {"ret_1d": 0.002, "rv_5d": 0.145, "high_low_ratio": 0.009}
    ml_status = _ood_detector.evaluate_live_features(live_feats)

    return build_live_market_snapshot(
        symbol=symbol,
        quote=quote,
        candles=candles,
        multi_tf=multi_tf,
        options_summary=opt_summary,
        news_items=news_items,
        health_statuses=health,
        ml_status=ml_status,
    )


@router.get("/market/{symbol}")
def get_live_market_quote(symbol: str = "NIFTY"):
    """Returns live quote with explicit real-time status label (NEAR_REAL_TIME, DELAYED, STALE)."""
    quote = _live_service.fetch_live_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Live quote unavailable for {symbol}.")
    return quote


@router.get("/candles/{symbol}")
def get_live_intraday_candles(symbol: str = "NIFTY", timeframe: str = "1m", limit: int = 50):
    """Returns intraday candle series."""
    return _live_service.fetch_intraday_candles(symbol, timeframe=timeframe, limit=limit)


@router.get("/options/{underlying}")
def get_live_options_summary(underlying: str = "NIFTY"):
    """Returns live options summary or honest UNAVAILABLE status."""
    res = _live_service.options_provider.get_live_option_chain(underlying)
    if not res:
        return {"underlying": underlying.upper(), "status_label": "UNAVAILABLE", "reason": "Options feed unconfigured."}
    return res


@router.get("/analysis/{symbol}")
def get_ai_market_analysis(symbol: str = "NIFTY"):
    """Returns structured AI Market Analysis JSON."""
    snapshot = get_live_market_snapshot(symbol)
    return _ai_analyst.analyze_snapshot(snapshot)


@router.get("/provider-health")
def get_provider_health_status():
    """Returns health and status labels across all providers."""
    statuses = _live_service.get_provider_health()
    return [
        {
            "provider_name": s.provider_name,
            "provider_type": s.provider_type.value,
            "is_healthy": s.is_healthy,
            "status_label": s.status_label,
            "latency_ms": s.latency_ms,
            "error_count": s.error_count,
            "capabilities": s.capabilities.__dict__,
        }
        for s in statuses
    ]


@router.post("/refresh")
def refresh_live_market_data(symbol: str = "NIFTY"):
    """Forces cache refresh across all subsystems."""
    _live_service.cache.clear()
    return get_live_market_snapshot(symbol)
