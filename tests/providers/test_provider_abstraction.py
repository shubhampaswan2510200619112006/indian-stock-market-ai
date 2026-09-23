"""
Unit tests for Ingestion Provider Abstraction layer (Phase 7).
"""

from __future__ import annotations

import pytest

from src.ingestion.providers.base import ProviderCapabilities, ProviderStatus, ProviderType
from src.ingestion.providers.market_provider import YFinanceMarketProvider
from src.ingestion.providers.news_provider import VerifiedRSSNewsProvider
from src.ingestion.providers.options_provider import NSELiveOptionsProvider


def test_provider_capabilities_structure():
    """Verify ProviderCapabilities initialization."""
    caps = ProviderCapabilities(
        live_quotes=True,
        intraday_candles=True,
        historical_candles=True,
        volume=True,
    )
    assert caps.live_quotes is True
    assert caps.intraday_candles is True
    assert caps.options_chain is False


def test_yfinance_market_provider():
    """Test YFinanceMarketProvider capability reporting and quote fetch."""
    provider = YFinanceMarketProvider()
    caps = provider.capabilities()
    assert caps.live_quotes is True
    assert caps.intraday_candles is True

    quote = provider.get_live_quote("NIFTY")
    assert quote is not None
    assert quote["symbol"] == "NIFTY"
    assert quote["last_price"] > 0


def test_options_provider_unavailability():
    """Verify options provider reports UNAVAILABLE truthfully when unconfigured."""
    provider = NSELiveOptionsProvider()
    caps = provider.capabilities()
    assert caps.options_chain is False

    chain = provider.get_live_option_chain("NIFTY")
    assert chain is not None
    assert chain["status_label"] == "UNAVAILABLE"


def test_news_provider_rss_fetch():
    """Test VerifiedRSSNewsProvider fetching articles."""
    provider = VerifiedRSSNewsProvider()
    caps = provider.capabilities()
    assert caps.news is True

    articles = provider.fetch_latest_news()
    assert isinstance(articles, list)
