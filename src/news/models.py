"""
Data Models for Live News Intelligence Engine (Phase 7).
Captures 3 timestamps (published_at, received_at, processed_at), SourceAuthority, and ImpactObservation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SourceAuthority(str, Enum):
    OFFICIAL_EXCHANGE = "OFFICIAL_EXCHANGE"
    OFFICIAL_COMPANY = "OFFICIAL_COMPANY"
    LICENSED_NEWS = "LICENSED_NEWS"
    PUBLIC_NEWS_FEED = "PUBLIC_NEWS_FEED"
    AGGREGATOR = "AGGREGATOR"


class NewsEventType(str, Enum):
    EARNINGS = "EARNINGS"
    GUIDANCE = "GUIDANCE"
    MERGER_ACQUISITION = "MERGER_ACQUISITION"
    REGULATORY = "REGULATORY"
    LEGAL = "LEGAL"
    MANAGEMENT_CHANGE = "MANAGEMENT_CHANGE"
    DIVIDEND = "DIVIDEND"
    BUYBACK = "BUYBACK"
    MACRO = "MACRO"
    RBI = "RBI"
    INFLATION = "INFLATION"
    INTEREST_RATE = "INTEREST_RATE"
    GLOBAL_MARKET = "GLOBAL_MARKET"
    UNKNOWN = "UNKNOWN"


class NewsSentimentType(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class NewsMaterialityType(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NewsArticle(BaseModel):
    article_id: str
    title: str
    url: str
    source_name: str
    source_authority: SourceAuthority
    published_at: str
    received_at: str
    processed_at: str
    ingestion_latency_ms: float
    processing_latency_ms: float
    total_latency_ms: float
    entity: str = "NIFTY"
    sector: str = "INDEX"
    event_type: NewsEventType = NewsEventType.UNKNOWN
    sentiment: NewsSentimentType = NewsSentimentType.NEUTRAL
    sentiment_score: float = 0.0
    materiality: NewsMaterialityType = NewsMaterialityType.MEDIUM
    materiality_reason: str = "Standard market announcement."


class ImpactObservation(BaseModel):
    article_id: str
    symbol: str
    observed_price_return: float = 0.0
    observed_volume_ratio: float = 1.0
    observed_iv_change: float = 0.0
    observed_oi_change: float = 0.0
    observation_notes: str = "Price change observed following publication; causal attribution is uncertain."
