"""
News Storage Manager for Phase 7.
Persists normalized news articles and sentiment evaluations into SQLite database.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.database.models import NewsArticleDB
from src.database.repository import get_session
from src.news.models import NewsArticle


class NewsStorageManager:
    """DB Manager for saving and querying news articles."""

    @staticmethod
    def save_article(article: NewsArticle) -> None:
        session = get_session()
        try:
            existing = session.query(NewsArticleDB).filter(NewsArticleDB.article_id == article.article_id).first()
            if not existing:
                db_item = NewsArticleDB(
                    article_id=article.article_id,
                    title=article.title,
                    url=article.url,
                    source_name=article.source_name,
                    source_authority=article.source_authority.value,
                    published_at=article.published_at,
                    received_at=article.received_at,
                    processed_at=article.processed_at,
                    ingestion_latency_ms=article.ingestion_latency_ms,
                    processing_latency_ms=article.processing_latency_ms,
                    total_latency_ms=article.total_latency_ms,
                    entity=article.entity,
                    sector=article.sector,
                    event_type=article.event_type.value,
                    sentiment=article.sentiment.value,
                    sentiment_score=article.sentiment_score,
                    materiality=article.materiality.value,
                    materiality_reason=article.materiality_reason,
                )
                session.add(db_item)
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    @staticmethod
    def get_recent_articles(
        limit: int = 50,
        entity: Optional[str] = None,
        ticker: Optional[str] = None,  # alias for entity
        category=None,
        materiality=None,
    ) -> List[Dict]:
        session = get_session()
        # Allow `ticker` as a legacy alias for `entity`
        resolved_entity = entity or ticker
        try:
            q = session.query(NewsArticleDB)
            if resolved_entity:
                q = q.filter(NewsArticleDB.entity == resolved_entity.upper())
            if category is not None:
                q = q.filter(NewsArticleDB.event_type == category.value)
            if materiality is not None:
                q = q.filter(NewsArticleDB.materiality == materiality.value)
            rows = q.order_by(NewsArticleDB.id.desc()).limit(limit).all()

            return [
                {
                    "article_id": r.article_id,
                    "title": r.title,
                    "url": r.url,
                    "source_name": r.source_name,
                    "source_authority": r.source_authority,
                    "published_at": r.published_at,
                    "received_at": r.received_at,
                    "processed_at": r.processed_at,
                    "total_latency_ms": r.total_latency_ms,
                    "entity": r.entity,
                    "sector": r.sector,
                    "event_type": r.event_type,
                    "sentiment": r.sentiment,
                    "materiality": r.materiality,
                }
                for r in rows
            ]
        except Exception:
            try:
                from src.database.connection import init_db
                init_db()
            except Exception:
                pass
            return []
        finally:
            session.close()

