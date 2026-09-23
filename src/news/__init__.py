"""
News Intelligence Engine Package (Phase 7).
"""

from src.news.models import (
    ImpactObservation,
    NewsArticle,
    NewsEventType,
    NewsMaterialityType,
    NewsSentimentType,
    SourceAuthority,
)
from src.news.deduplicator import NewsDeduplicator
from src.news.entity_mapper import EntityMapper
from src.news.event_classifier import EventClassifier
from src.news.sentiment import NewsSentimentAnalyzer
from src.news.impact import NewsImpactAnalyzer
from src.news.storage import NewsStorageManager

__all__ = [
    "ImpactObservation",
    "NewsArticle",
    "NewsEventType",
    "NewsMaterialityType",
    "NewsSentimentType",
    "SourceAuthority",
    "NewsDeduplicator",
    "EntityMapper",
    "EventClassifier",
    "NewsSentimentAnalyzer",
    "NewsImpactAnalyzer",
    "NewsStorageManager",
]
