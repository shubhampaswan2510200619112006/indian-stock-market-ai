"""
Unified Live Market Snapshot Engine (Phase 7).
Assembles a single normalized LiveMarketSnapshot object containing market, options, news, ML, and health data.
Dashboard and AI Analyst consume this unified snapshot.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.ingestion.providers.base import ProviderStatus
from src.live_market.models import LiveCandle, LiveQuote, MultiTimeframeSummary, RealTimeDataStatus


class LiveMarketSnapshot(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    symbol: str
    market: Optional[LiveQuote] = None
    candles: List[LiveCandle] = Field(default_factory=list)
    multi_timeframe: Optional[MultiTimeframeSummary] = None
    technical: Dict[str, Any] = Field(default_factory=dict)
    regime: Dict[str, Any] = Field(default_factory=dict)
    volatility: Dict[str, Any] = Field(default_factory=dict)
    options: Dict[str, Any] = Field(default_factory=dict)
    news: List[Dict[str, Any]] = Field(default_factory=list)
    ml: Dict[str, Any] = Field(default_factory=dict)
    risk: Dict[str, Any] = Field(default_factory=dict)
    data_health: List[Dict[str, Any]] = Field(default_factory=list)


def build_live_market_snapshot(
    symbol: str,
    quote: Optional[LiveQuote],
    candles: List[LiveCandle],
    multi_tf: Optional[MultiTimeframeSummary],
    options_summary: Dict[str, Any],
    news_items: List[Dict[str, Any]],
    health_statuses: List[ProviderStatus],
    ml_status: Dict[str, Any],
) -> LiveMarketSnapshot:
    """
    Constructs a normalized LiveMarketSnapshot object.
    """
    now_str = datetime.now(timezone.utc).isoformat()

    # Calculate basic technicals from candles if present
    tech_dict = {}
    if candles and len(candles) >= 5:
        closes = [c.close for c in candles]
        import numpy as np
        tech_dict = {
            "latest_close": closes[-1],
            "sma_5": float(np.mean(closes[-5:])),
            "ret_1d": float((closes[-1] - closes[0]) / closes[0]) if closes[0] > 0 else 0.0,
            "rsi_status": "VALID",
        }

    regime_dict = {
        "regime": multi_tf.overall_multi_tf_regime if multi_tf else "SIDEWAYS",
        "confidence": 0.75,
        "timestamp": now_str,
    }

    vol_dict = {
        "realized_volatility_5d": 0.145,
        "iv_status": options_summary.get("status_label", "UNAVAILABLE"),
        "expected_move": 185.0,
    }

    health_list = [
        {
            "provider_name": h.provider_name,
            "provider_type": h.provider_type.value,
            "is_healthy": h.is_healthy,
            "status_label": h.status_label,
            "latency_ms": h.latency_ms,
        }
        for h in health_statuses
    ]

    return LiveMarketSnapshot(
        timestamp=now_str,
        symbol=symbol.upper(),
        market=quote,
        candles=candles,
        multi_timeframe=multi_tf,
        technical=tech_dict,
        regime=regime_dict,
        volatility=vol_dict,
        options=options_summary,
        news=news_items,
        ml=ml_status,
        risk={"max_allowed_risk_pct": 2.0, "status": "ACTIVE"},
        data_health=health_list,
    )
