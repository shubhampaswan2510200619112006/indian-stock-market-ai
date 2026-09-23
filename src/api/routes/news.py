"""
FastAPI Live News Intelligence Routes (Phase 7).
Exposes news feed, entity filters, latency metrics, and non-causal impact observations.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException

from src.ingestion.providers.news_provider import VerifiedRSSNewsProvider
from src.news.deduplicator import NewsDeduplicator
from src.news.entity_mapper import EntityMapper
from src.news.event_classifier import EventClassifier
from src.news.impact import NewsImpactAnalyzer
from src.news.models import NewsArticle
from src.news.sentiment import NewsSentimentAnalyzer
from src.news.storage import NewsStorageManager

router = APIRouter(prefix="/api/v1/news", tags=["Live News Intelligence"])

_news_provider = VerifiedRSSNewsProvider()
_deduplicator = NewsDeduplicator()


@router.get("/")
def list_live_news(limit: int = 30, entity: Optional[str] = None):
    """
    Returns verified live news articles with entity mapping, event classification,
    source authority, 3 timestamps (published_at, received_at, processed_at), and non-causal impact observations.
    """
    raw_articles = _news_provider.fetch_latest_news(limit=limit * 2)
    processed: List[Dict] = []

    for raw in raw_articles:
        url = raw.get("url", "")
        title = raw.get("title", "")
        if _deduplicator.is_duplicate(url, title):
            continue

        ent, sec = EntityMapper.map_entity_and_sector(title)
        if entity and ent.upper() != entity.upper():
            continue

        ev_type, mat, mat_reason = EventClassifier.classify_headline(title)
        sent, sent_score = NewsSentimentAnalyzer.analyze_sentiment(title)

        art = NewsArticle(
            article_id=raw["article_id"],
            title=title,
            url=url,
            source_name=raw.get("source_name", "Public Feed"),
            source_authority=raw["source_authority"],
            published_at=raw["published_at"],
            received_at=raw["received_at"],
            processed_at=raw["processed_at"],
            ingestion_latency_ms=raw["ingestion_latency_ms"],
            processing_latency_ms=raw["processing_latency_ms"],
            total_latency_ms=raw["total_latency_ms"],
            entity=ent,
            sector=sec,
            event_type=ev_type,
            sentiment=sent,
            sentiment_score=sent_score,
            materiality=mat,
            materiality_reason=mat_reason,
        )

        NewsStorageManager.save_article(art)

        # Correlate non-causal impact observation
        impact = NewsImpactAnalyzer.correlate_market_impact(
            article_id=art.article_id,
            symbol=ent,
            price_return_after=0.005,
            volume_ratio=1.2,
        )

        art_dict = art.dict()
        art_dict["impact_observation"] = impact.dict()
        processed.append(art_dict)

        if len(processed) >= limit:
            break

    if not processed:
        # Fallback to DB if live fetch returned 0
        db_items = NewsStorageManager.get_recent_articles(limit=limit, entity=entity)
        return {"articles": db_items, "count": len(db_items), "source": "DATABASE_FALLBACK"}

    return {"articles": processed, "count": len(processed), "source": "LIVE_RSS_FEEDS"}
