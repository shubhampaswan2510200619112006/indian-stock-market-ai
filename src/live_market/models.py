"""
Data Models for Live Market Engine (Phase 7).
Enforces truthful real-time status labels: REAL_TIME, NEAR_REAL_TIME, DELAYED, STALE, UNAVAILABLE, ERROR.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RealTimeDataStatus(str, Enum):
    REAL_TIME = "REAL_TIME"
    NEAR_REAL_TIME = "NEAR_REAL_TIME"
    DELAYED = "DELAYED"
    HISTORICAL = "HISTORICAL"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"


class LiveQuote(BaseModel):
    symbol: str
    provider_symbol: str
    last_price: float
    previous_close: Optional[float] = None
    change: float = 0.0
    change_pct: float = 0.0
    day_high: float
    day_low: float
    volume: int
    provider_timestamp: str
    received_timestamp: str
    normalized_timestamp: str
    latency_ms: float
    source: str
    status_label: RealTimeDataStatus


class LiveCandle(BaseModel):
    symbol: str
    timeframe: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str
    received_at: str
    is_complete: bool = True


class MultiTimeframeSummary(BaseModel):
    symbol: str
    tf_1m: str = "NEUTRAL"
    tf_5m: str = "NEUTRAL"
    tf_15m: str = "NEUTRAL"
    tf_1h: str = "NEUTRAL"
    tf_1d: str = "NEUTRAL"
    overall_multi_tf_regime: str = "SIDEWAYS"
    conflicting_signals: List[str] = Field(default_factory=list)
