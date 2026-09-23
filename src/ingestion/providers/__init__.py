"""
Provider Abstraction Package (Phase 7).
"""

from src.ingestion.providers.base import (
    BaseProvider,
    FundamentalsProvider,
    MarketDataProvider,
    NewsDataProvider,
    OptionsDataProvider,
    ProviderCapabilities,
    ProviderStatus,
    ProviderType,
)
from src.ingestion.providers.market_provider import YFinanceMarketProvider
from src.ingestion.providers.news_provider import SourceAuthority, VerifiedRSSNewsProvider
from src.ingestion.providers.options_provider import NSELiveOptionsProvider

__all__ = [
    "BaseProvider",
    "MarketDataProvider",
    "OptionsDataProvider",
    "NewsDataProvider",
    "FundamentalsProvider",
    "ProviderCapabilities",
    "ProviderStatus",
    "ProviderType",
    "YFinanceMarketProvider",
    "NSELiveOptionsProvider",
    "VerifiedRSSNewsProvider",
    "SourceAuthority",
]
