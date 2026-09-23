"""
Provider Abstraction Layer & Capabilities Discovery (Phase 7).
Defines abstract interfaces for Market, Options, News, and Fundamentals Providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ProviderType(str, Enum):
    MARKET_DATA = "MARKET_DATA"
    OPTIONS_DATA = "OPTIONS_DATA"
    NEWS_DATA = "NEWS_DATA"
    FUNDAMENTALS_DATA = "FUNDAMENTALS_DATA"


@dataclass
class ProviderCapabilities:
    live_quotes: bool = False
    intraday_candles: bool = False
    historical_candles: bool = False
    options_chain: bool = False
    options_quotes: bool = False
    bid_ask: bool = False
    volume: bool = False
    open_interest: bool = False
    change_in_oi: bool = False
    implied_volatility: bool = False
    news: bool = False
    fundamentals: bool = False


@dataclass
class ProviderStatus:
    provider_name: str
    provider_type: ProviderType
    is_healthy: bool
    status_label: str  # e.g., REAL_TIME, NEAR_REAL_TIME, DELAYED, STALE, UNAVAILABLE, ERROR
    last_successful_request: Optional[datetime] = None
    latency_ms: float = 0.0
    error_count: int = 0
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)


class BaseProvider(ABC):
    """Abstract Base Class for all external data providers."""

    def __init__(self, provider_name: str, provider_type: ProviderType):
        self.provider_name = provider_name
        self.provider_type = provider_type
        self._health = ProviderStatus(
            provider_name=provider_name,
            provider_type=provider_type,
            is_healthy=True,
            status_label="UNAVAILABLE",
        )

    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Returns the capabilities supported by this provider instance."""
        pass

    @abstractmethod
    def health_check(self) -> ProviderStatus:
        """Evaluates health, latency, and status label."""
        pass


class MarketDataProvider(BaseProvider):
    """Abstract interface for live & intraday market data providers."""

    def __init__(self, provider_name: str):
        super().__init__(provider_name=provider_name, provider_type=ProviderType.MARKET_DATA)

    @abstractmethod
    def get_live_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_intraday_candles(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> List[Dict[str, Any]]:
        pass


class OptionsDataProvider(BaseProvider):
    """Abstract interface for live option chain and options quote providers."""

    def __init__(self, provider_name: str):
        super().__init__(provider_name=provider_name, provider_type=ProviderType.OPTIONS_DATA)

    @abstractmethod
    def get_live_option_chain(self, underlying: str) -> Optional[Dict[str, Any]]:
        pass


class NewsDataProvider(BaseProvider):
    """Abstract interface for financial news & announcement providers."""

    def __init__(self, provider_name: str):
        super().__init__(provider_name=provider_name, provider_type=ProviderType.NEWS_DATA)

    @abstractmethod
    def fetch_latest_news(self, limit: int = 50) -> List[Dict[str, Any]]:
        pass


class FundamentalsProvider(BaseProvider):
    """Abstract interface for corporate fundamentals & earnings release data."""

    def __init__(self, provider_name: str):
        super().__init__(provider_name=provider_name, provider_type=ProviderType.FUNDAMENTALS_DATA)

    @abstractmethod
    def get_company_overview(self, symbol: str) -> Optional[Dict[str, Any]]:
        pass
