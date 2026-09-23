"""
Unit tests for Live Market Engine (Phase 7).
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from src.live_market.cache import LiveDataCache
from src.live_market.models import LiveQuote, RealTimeDataStatus
from src.live_market.service import LiveMarketService
from src.live_market.validator import LiveDataValidator


def test_live_quote_validation():
    """Verify quote validator checks OHLC and price sanity."""
    validator = LiveDataValidator()
    now_str = datetime.now(timezone.utc).isoformat()

    # Valid quote dict
    good_quote_dict = {
        "symbol": "NIFTY",
        "provider_symbol": "^NSEI",
        "last_price": 24500.0,
        "previous_close": 24450.0,
        "change": 50.0,
        "change_pct": 0.2,
        "day_high": 24550.0,
        "day_low": 24450.0,
        "volume": 10000,
        "provider_timestamp": now_str,
        "received_timestamp": now_str,
        "normalized_timestamp": now_str,
        "latency_ms": 1500.0,
        "source": "yfinance",
        "status_label": "DELAYED",
    }
    is_valid, quote, err = validator.validate_quote(good_quote_dict)
    assert is_valid is True
    assert quote is not None
    assert quote.last_price == 24500.0

    # Invalid quote dict (price <= 0)
    bad_quote_dict = {
        "symbol": "NIFTY",
        "last_price": -10.0,
        "volume": 0,
    }
    is_valid, quote, err = validator.validate_quote(bad_quote_dict)
    assert is_valid is False
    assert err is not None


def test_live_data_cache():
    """Test TTL cache storing and retrieval."""
    cache = LiveDataCache()
    now_str = datetime.now(timezone.utc).isoformat()

    quote = LiveQuote(
        symbol="RELIANCE",
        provider_symbol="RELIANCE.NS",
        last_price=3000.0,
        change=10.0,
        change_pct=0.33,
        day_high=3010.0,
        day_low=2990.0,
        volume=5000,
        provider_timestamp=now_str,
        received_timestamp=now_str,
        normalized_timestamp=now_str,
        latency_ms=500.0,
        source="TEST",
        status_label=RealTimeDataStatus.NEAR_REAL_TIME,
    )

    cache.set("RELIANCE", quote, ttl_seconds=5, source="TEST")
    val, is_expired = cache.get("RELIANCE")
    assert val is not None
    assert val.last_price == 3000.0
    assert is_expired is False


def test_live_market_service_quote_fetch():
    """Test LiveMarketService fetching a live quote."""
    service = LiveMarketService()
    quote = service.fetch_live_quote("NIFTY")

    assert quote is not None
    assert quote.symbol == "NIFTY"
    assert quote.last_price > 0
