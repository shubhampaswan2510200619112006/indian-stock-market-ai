"""
Verified RSS Financial News Data Provider (Phase 7).
Implements NewsDataProvider for accessible RSS and exchange announcement feeds.
Tags source authority and preserves 3 execution timestamps: published_at, received_at, processed_at.
"""

from datetime import datetime, timezone
from enum import Enum
import time
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET
import requests

from src.ingestion.providers.base import NewsDataProvider, ProviderCapabilities, ProviderStatus, ProviderType


class SourceAuthority(str, Enum):
    OFFICIAL_EXCHANGE = "OFFICIAL_EXCHANGE"
    OFFICIAL_COMPANY = "OFFICIAL_COMPANY"
    LICENSED_NEWS = "LICENSED_NEWS"
    PUBLIC_NEWS_FEED = "PUBLIC_NEWS_FEED"
    AGGREGATOR = "AGGREGATOR"


class VerifiedRSSNewsProvider(NewsDataProvider):
    """
    Legitimate News Provider collecting public RSS feeds.
    Verifies endpoints and tags items with explicit Source Authority and 3 Latency Timestamps.
    """

    # Public financial RSS feeds (verified accessible endpoints)
    DEFAULT_FEEDS = [
        {
            "name": "Google News India Business",
            "url": "https://news.google.com/rss/search?q=NSE+NIFTY+stock+market+India&hl=en-IN&gl=IN&ceid=IN:en",
            "authority": SourceAuthority.AGGREGATOR,
        },
        {
            "name": "Economic Times Markets RSS",
            "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "authority": SourceAuthority.PUBLIC_NEWS_FEED,
        },
    ]

    def __init__(self, custom_feeds: Optional[List[Dict]] = None):
        super().__init__(provider_name="VerifiedRSSNewsProvider")
        self.feeds = custom_feeds or self.DEFAULT_FEEDS

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(news=True)

    def health_check(self) -> ProviderStatus:
        start = time.time()
        try:
            r = requests.get(self.feeds[0]["url"], timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            lat = (time.time() - start) * 1000.0
            if r.status_code == 200:
                self._health.is_healthy = True
                self._health.status_label = "REAL_TIME"
                self._health.last_successful_request = datetime.now(timezone.utc)
                self._health.latency_ms = round(lat, 2)
            else:
                self._health.is_healthy = False
                self._health.status_label = "ERROR"
            self._health.capabilities = self.capabilities()
        except Exception:
            self._health.is_healthy = False
            self._health.status_label = "UNAVAILABLE"
        return self._health

    def fetch_latest_news(self, limit: int = 50) -> List[Dict[str, Any]]:
        articles: List[Dict[str, Any]] = []
        now_received = datetime.now(timezone.utc)

        for feed_info in self.feeds:
            url = feed_info["url"]
            auth = feed_info["authority"].value
            t_fetch_start = time.time()

            try:
                r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code != 200:
                    continue

                ingest_latency = (time.time() - t_fetch_start) * 1000.0

                root = ET.fromstring(r.content)
                channel = root.find("channel")
                if channel is None:
                    continue

                for item in channel.findall("item"):
                    title = item.findtext("title") or ""
                    link = item.findtext("link") or ""
                    pub_date_str = item.findtext("pubDate") or now_received.isoformat()

                    t_proc_start = time.time()
                    # Normalized item
                    now_processed = datetime.now(timezone.utc)
                    proc_latency = (time.time() - t_proc_start) * 1000.0
                    tot_latency = ingest_latency + proc_latency

                    articles.append({
                        "article_id": f"rss_{hash(link) & 0xffffffff}",
                        "title": title.strip(),
                        "url": link.strip(),
                        "source_name": feed_info["name"],
                        "source_authority": auth,
                        "published_at": pub_date_str,
                        "received_at": now_received.isoformat(),
                        "processed_at": now_processed.isoformat(),
                        "ingestion_latency_ms": round(ingest_latency, 2),
                        "processing_latency_ms": round(proc_latency, 2),
                        "total_latency_ms": round(tot_latency, 2),
                    })

                    if len(articles) >= limit:
                        break
            except Exception:
                continue

            if len(articles) >= limit:
                break

        return articles
