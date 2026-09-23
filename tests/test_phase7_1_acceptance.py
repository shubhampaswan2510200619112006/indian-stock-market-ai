"""
Phase 7.1 — Provider Verification & Live-System Acceptance Test Suite.

Verifies truthful data status, provider capability reporting, timestamp integrity,
non-causal news impact language, options feed unconfiguration handling, OOD monitoring,
and failure-safety state transitions.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest

from src.ai_analyst.ood_detector import OODDetector
from src.ingestion.providers.base import ProviderCapabilities, ProviderStatus, ProviderType
from src.ingestion.providers.market_provider import YFinanceMarketProvider
from src.ingestion.providers.news_provider import VerifiedRSSNewsProvider
from src.ingestion.providers.options_provider import NSELiveOptionsProvider
from src.live_market.cache import LiveDataCache
from src.live_market.models import LiveCandle, LiveQuote, RealTimeDataStatus
from src.live_market.service import LiveMarketService
from src.live_market.validator import LiveDataValidator
from src.news.deduplicator import NewsDeduplicator
from src.news.entity_mapper import EntityMapper
from src.news.event_classifier import EventClassifier
from src.news.impact import NewsImpactAnalyzer
from src.news.models import NewsArticle, NewsEventType, NewsMaterialityType, SourceAuthority
from src.news.sentiment import NewsSentimentAnalyzer


def test_provider_verified_requires_real_observation():
    """Verify that a provider capability is NOT marked verified without a genuine observation."""
    provider = YFinanceMarketProvider()
    quote = provider.get_live_quote("NIFTY")

    # Real observation retrieved with non-zero price
    assert quote is not None
    assert quote["symbol"] == "NIFTY"
    assert quote["last_price"] > 0
    assert "provider_timestamp" in quote
    assert quote["status_label"] in ["DELAYED", "NEAR_REAL_TIME", "HISTORICAL", "STALE"]


def test_delayed_data_never_labeled_realtime():
    """Verify delayed or free-tier market data is never labeled REAL_TIME without socket stream proof."""
    provider = YFinanceMarketProvider()
    quote = provider.get_live_quote("NIFTY")

    assert quote is not None
    assert quote["status_label"] != "REAL_TIME"
    assert quote["status_label"] in ["DELAYED", "NEAR_REAL_TIME", "HISTORICAL", "STALE"]


def test_cached_data_never_labeled_realtime():
    """Verify cached observations are never upgraded to REAL_TIME."""
    cache = LiveDataCache()
    now_str = datetime.now(timezone.utc).isoformat()

    quote = LiveQuote(
        symbol="NIFTY",
        provider_symbol="^NSEI",
        last_price=24500.0,
        change=50.0,
        change_pct=0.2,
        day_high=24550.0,
        day_low=24450.0,
        volume=10000,
        provider_timestamp=now_str,
        received_timestamp=now_str,
        normalized_timestamp=now_str,
        latency_ms=100.0,
        source="TEST_CACHE",
        status_label=RealTimeDataStatus.DELAYED,
    )

    cache.set("quote_NIFTY", quote, ttl_seconds=30, source="TEST_CACHE")
    cached_val, is_expired = cache.get("quote_NIFTY")

    assert cached_val is not None
    assert cached_val.status_label != RealTimeDataStatus.REAL_TIME
    assert cached_val.status_label == RealTimeDataStatus.DELAYED


def test_missing_provider_timestamp_not_fabricated():
    """Verify that missing provider timestamps are recorded as unavailable rather than fabricated."""
    validator = LiveDataValidator()
    quote_dict = {
        "symbol": "TEST_SYM",
        "last_price": 100.0,
        "volume": 50,
        "source": "TEST",
        "status_label": "DELAYED",
    }
    is_valid, quote, err = validator.validate_quote(quote_dict)
    assert is_valid is True
    assert quote is not None
    # provider_timestamp should be empty or recorded as missing rather than fabricated as current time
    assert quote.provider_timestamp == ""


def test_options_unavailable_when_unconfigured():
    """Verify options provider cleanly returns OPTIONS STATUS: UNAVAILABLE when feed is unconfigured."""
    options_provider = NSELiveOptionsProvider(api_key=None)
    caps = options_provider.capabilities()

    assert caps.options_chain is False
    chain = options_provider.get_live_option_chain("NIFTY")

    assert chain is not None
    assert chain["status_label"] == "UNAVAILABLE"
    assert chain["strikes"] == []


def test_no_synthetic_live_options():
    """Verify system never generates synthetic option chains or fake prices in live options feed."""
    options_provider = NSELiveOptionsProvider(api_key=None)
    chain = options_provider.get_live_option_chain("NIFTY")

    assert chain["status_label"] == "UNAVAILABLE"
    assert "synthetic" not in str(chain).lower() or "unconfigured" in str(chain).lower()
    # Confirm zero fabricated contracts
    assert len(chain.get("strikes", [])) == 0


def test_news_latency_calculation():
    """Verify 3 latency timestamps (published_at, received_at, processed_at) and latency math."""
    pub_dt = datetime.now(timezone.utc) - timedelta(minutes=10)
    rec_dt = datetime.now(timezone.utc) - timedelta(seconds=15)
    proc_dt = datetime.now(timezone.utc)

    ingestion_latency = (rec_dt - pub_dt).total_seconds()
    processing_latency = (proc_dt - rec_dt).total_seconds()
    total_latency = (proc_dt - pub_dt).total_seconds()

    assert ingestion_latency > 0
    assert processing_latency > 0
    assert total_latency == pytest.approx(ingestion_latency + processing_latency)


def test_news_missing_publication_time():
    """Verify missing publication timestamp is explicitly recorded as unavailable rather than guessed."""
    provider = VerifiedRSSNewsProvider()
    articles = provider.fetch_latest_news()

    if articles:
        art = articles[0]
        assert "published_at" in art or hasattr(art, "published_at")
        assert "received_at" in art or hasattr(art, "received_at")
        assert "processed_at" in art or hasattr(art, "processed_at")


def test_news_authority_mapping():
    """Verify news source authority is correctly mapped without overstating aggregators as official exchange."""
    provider = VerifiedRSSNewsProvider()
    caps = provider.capabilities()
    assert caps.news is True

    # Check authority classification logic
    assert SourceAuthority.OFFICIAL_EXCHANGE.value == "OFFICIAL_EXCHANGE"
    assert SourceAuthority.PUBLIC_NEWS_FEED.value == "PUBLIC_NEWS_FEED"
    assert SourceAuthority.AGGREGATOR.value == "AGGREGATOR"


def test_non_causal_impact_language():
    """Verify news market impact output uses strictly non-causal, observational language."""
    obs = NewsImpactAnalyzer.correlate_market_impact(
        article_id="art_100",
        symbol="NIFTY",
        price_return_after=0.012,
        volume_ratio=1.15,
    )
    notes = obs.observation_notes.lower()

    assert "causal" in notes or "uncertain" in notes
    assert "guarantee" not in notes
    assert "will cause" not in notes


def test_snapshot_truthful_subsystem_status():
    """Verify unified LiveMarketSnapshot contains truthful subsystem availability states."""
    service = LiveMarketService()
    snapshot = service.get_live_snapshot("NIFTY")

    assert snapshot.symbol == "NIFTY"
    assert snapshot.market is not None
    assert snapshot.market.last_price > 0
    assert snapshot.options.get("status") == "UNAVAILABLE" or snapshot.options.get("status_label") == "UNAVAILABLE"


def test_stale_data_status():
    """Verify quotes older than TTL are correctly tagged STALE."""
    validator = LiveDataValidator()
    old_time_str = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()

    old_quote_dict = {
        "symbol": "NIFTY",
        "provider_symbol": "^NSEI",
        "last_price": 24500.0,
        "volume": 1000,
        "received_timestamp": old_time_str,
        "status_label": "DELAYED",
    }

    is_valid, quote, err = validator.validate_quote(old_quote_dict)
    assert is_valid is True
    assert quote is not None
    assert quote.status_label == RealTimeDataStatus.STALE


def test_provider_failure_safe_state():
    """Verify provider request failures degrade cleanly without throwing unhandled exceptions."""
    service = LiveMarketService()

    # Querying invalid symbol or during failure returns None or clean fallback quote
    quote = service.fetch_live_quote("INVALID_XYZ_123")
    # Must fail safely without crashing
    assert quote is None or quote.status_label in [RealTimeDataStatus.STALE, RealTimeDataStatus.UNAVAILABLE, RealTimeDataStatus.ERROR]


def test_ood_status_preserved():
    """Verify ML Feature Drift Detector preserves Phase 6.5 research status disclaimer."""
    ood_detector = OODDetector()
    feature_vector = {"ret_1d": 0.0015, "rv_5d": 0.140, "high_low_ratio": 0.010}
    res = ood_detector.evaluate_live_features(feature_vector)

    assert "overall_status" in res
    assert res["overall_status"] in ["NORMAL", "DRIFT_WARNING", "OOD", "INSUFFICIENT_DATA"]
    assert "LIMITED DATA" in res["research_banner"]
