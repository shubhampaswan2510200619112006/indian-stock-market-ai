"""
Unit tests for News Intelligence Engine (Phase 7).
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from src.news.deduplicator import NewsDeduplicator
from src.news.entity_mapper import EntityMapper
from src.news.event_classifier import EventClassifier
from src.news.impact import NewsImpactAnalyzer
from src.news.models import NewsArticle, NewsEventType, NewsMaterialityType, SourceAuthority
from src.news.sentiment import NewsSentimentAnalyzer
from src.news.storage import NewsStorageManager


def test_news_deduplication():
    """Verify title and URL MD5 fingerprint deduplication."""
    dedup = NewsDeduplicator()
    is_dup1 = dedup.is_duplicate(url="https://example.com/news1", title="RBI Keeps Repo Rate Unchanged")
    is_dup2 = dedup.is_duplicate(url="https://example.com/news1", title="RBI Keeps Repo Rate Unchanged")
    is_dup3 = dedup.is_duplicate(url="https://example.com/news2", title="Nifty Hits New High")

    assert is_dup1 is False
    assert is_dup2 is True
    assert is_dup3 is False


def test_entity_mapping():
    """Verify text entity mapping to tickers and sectors."""
    text = "Reliance Industries and HDFC Bank pushed Nifty higher following RBI monetary policy announcement."
    entity_symbol, sector = EntityMapper.map_entity_and_sector(text)

    assert entity_symbol in ["NIFTY", "RELIANCE", "HDFCBANK"]


test_cases = [
    ("Reliance Industries reported Q3 earnings growth of 15%", NewsEventType.EARNINGS),
    ("SEBI issues new regulatory circular on derivative lot sizes", NewsEventType.REGULATORY),
    ("RBI monetary policy committee keeps repo rate unchanged at 6.5%", NewsEventType.RBI),
]


@pytest.mark.parametrize("title,expected_category", test_cases)
def test_event_classification(title, expected_category):
    """Test EventClassifier categorizing news text."""
    event_type, materiality, reason = EventClassifier.classify_headline(title)
    assert event_type == expected_category


def test_news_sentiment_analysis():
    """Test rule-assisted sentiment analyzer."""
    sentiment_type, pos_score = NewsSentimentAnalyzer.analyze_sentiment("Nifty surges strongly on robust GDP growth")
    assert pos_score > 0

    sentiment_type, neg_score = NewsSentimentAnalyzer.analyze_sentiment("Stock falls following major regulatory penalty")
    assert neg_score < 0


def test_news_impact_non_causal_attribution():
    """Verify impact analyzer includes non-causal attribution disclaimer."""
    obs = NewsImpactAnalyzer.correlate_market_impact(
        article_id="test_1",
        symbol="NIFTY",
        price_return_after=0.015,
        volume_ratio=1.2,
    )
    assert obs.symbol == "NIFTY"
    assert "causal" in obs.observation_notes.lower() or "uncertain" in obs.observation_notes.lower()
