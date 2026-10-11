"""
News Storage Manager for Phase 7.
Persists normalized news articles and sentiment evaluations into SQLite database.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.database.models import NewsArticleDB
from src.database.repository import get_session
from src.news.models import NewsArticle


class NewsStorageManager:
    """DB Manager for saving and querying news articles."""

    @staticmethod
    def save_article(article: Any) -> bool:
        session = get_session()
        try:
            if isinstance(article, dict):
                art_id = article.get("article_id")
                title = article.get("title", "")
                url = article.get("url", "")
                source_name = article.get("source_name", "RSS")
                src_auth = article.get("source_authority", "PUBLIC_NEWS_FEED")
                auth_val = src_auth.value if hasattr(src_auth, "value") else str(src_auth)
                pub_at = article.get("published_at")
                rec_at = article.get("received_at")
                proc_at = article.get("processed_at")
                ing_lat = article.get("ingestion_latency_ms", 0.0)
                proc_lat = article.get("processing_latency_ms", 0.0)
                tot_lat = article.get("total_latency_ms", 0.0)
                entity = article.get("entity", "NIFTY")
                sector = article.get("sector", "MARKET")
                evt = article.get("event_type", "OTHER")
                evt_val = evt.value if hasattr(evt, "value") else str(evt)
                sent = article.get("sentiment", "NEUTRAL")
                sent_val = sent.value if hasattr(sent, "value") else str(sent)
                sent_score = article.get("sentiment_score", 0.0)
                mat = article.get("materiality", "ROUTINE")
                mat_val = mat.value if hasattr(mat, "value") else str(mat)
                mat_reason = article.get("materiality_reason", "")
            else:
                art_id = getattr(article, "article_id", None)
                title = getattr(article, "title", "")
                url = getattr(article, "url", "")
                source_name = getattr(article, "source_name", "RSS")
                src_auth = getattr(article, "source_authority", "PUBLIC_NEWS_FEED")
                auth_val = src_auth.value if hasattr(src_auth, "value") else str(src_auth)
                pub_at = getattr(article, "published_at", None)
                rec_at = getattr(article, "received_at", None)
                proc_at = getattr(article, "processed_at", None)
                ing_lat = getattr(article, "ingestion_latency_ms", 0.0)
                proc_lat = getattr(article, "processing_latency_ms", 0.0)
                tot_lat = getattr(article, "total_latency_ms", 0.0)
                entity = getattr(article, "entity", "NIFTY")
                sector = getattr(article, "sector", "MARKET")
                evt = getattr(article, "event_type", "OTHER")
                evt_val = evt.value if hasattr(evt, "value") else str(evt)
                sent = getattr(article, "sentiment", "NEUTRAL")
                sent_val = sent.value if hasattr(sent, "value") else str(sent)
                sent_score = getattr(article, "sentiment_score", 0.0)
                mat = getattr(article, "materiality", "ROUTINE")
                mat_val = mat.value if hasattr(mat, "value") else str(mat)
                mat_reason = getattr(article, "materiality_reason", "")

            if not art_id:
                return False

            existing = session.query(NewsArticleDB).filter(NewsArticleDB.article_id == art_id).first()
            if not existing:
                db_item = NewsArticleDB(
                    article_id=art_id,
                    title=title,
                    url=url,
                    source_name=source_name,
                    source_authority=auth_val,
                    published_at=pub_at,
                    received_at=rec_at,
                    processed_at=proc_at,
                    ingestion_latency_ms=ing_lat,
                    processing_latency_ms=proc_lat,
                    total_latency_ms=tot_lat,
                    entity=entity,
                    sector=sector,
                    event_type=evt_val,
                    sentiment=sent_val,
                    sentiment_score=sent_score,
                    materiality=mat_val,
                    materiality_reason=mat_reason,
                )
                session.add(db_item)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
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

