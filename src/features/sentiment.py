"""
Sentiment analysis module interface for future news, macroeconomic events, and corporate announcements.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from src.ingestion.schemas import DataRecord


class SentimentScore(DataRecord):
    """Placeholder sentiment feature score for an entity/symbol."""
    symbol: str
    sentiment_score: float = Field(ge=-1.0, le=1.0, description="Normalized sentiment (-1 bearish to +1 bullish)")
    confidence: float = Field(ge=0.0, le=1.0)
    news_count_24h: int = 0
    key_themes: list[str] = Field(default_factory=list)
