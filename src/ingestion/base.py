"""
Abstract base classes for data providers.

This is the MOST CRITICAL architectural abstraction in the system.
All business logic depends on these interfaces, NEVER on a specific provider.

The nsepython/direct-NSE provider is experimental and free.
Broker APIs (Kite, Dhan, Fyers, etc.) can be added by implementing these ABCs.

A provider must:
- Return validated Pydantic models
- Raise DataUnavailableError if data cannot be fetched (never invent data)
- Carry source and timestamp on every record
- Respect rate limits
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

import pandas as pd

from src.ingestion.schemas import (
    NewsItem,
    OptionChainSnapshot,
    Quote,
)


class DataProviderError(Exception):
    """Base error for all data provider issues."""
    pass


class DataUnavailableError(DataProviderError):
    """Raised when data cannot be retrieved. The system should show UNAVAILABLE, not fake data."""
    pass


class RateLimitError(DataProviderError):
    """Raised when rate limit is hit."""
    pass


class AuthenticationError(DataProviderError):
    """Raised when API credentials are invalid or missing."""
    pass


class MarketDataProvider(ABC):
    """
    Interface for underlying instrument data (prices, OHLCV).

    Implementations: NSEProvider, YFinanceProvider, KiteProvider, etc.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name for UI display and logging."""
        ...

    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        """
        Get the current/latest quote for an underlying.

        Args:
            symbol: Underlying symbol (e.g., "NIFTY", "BANKNIFTY")

        Returns:
            Quote with timestamp, source, and data_quality

        Raises:
            DataUnavailableError: If quote cannot be fetched
        """
        ...

    @abstractmethod
    def get_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data.

        Args:
            symbol: Underlying symbol
            start: Start date (inclusive)
            end: End date (inclusive)
            interval: Candle interval ("1d", "1wk", "1mo")

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
            Empty DataFrame if no data available.

        Raises:
            DataUnavailableError: If data cannot be fetched
        """
        ...

    def health_check(self) -> bool:
        """Check if the provider is reachable. Default: True."""
        return True


class OptionsDataProvider(ABC):
    """
    Interface for options market data (chains, expiries).

    Implementations: NSEOptionsProvider, KiteOptionsProvider, etc.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    def get_option_chain(
        self,
        symbol: str,
        expiry: Optional[date] = None,
    ) -> OptionChainSnapshot:
        """
        Fetch the full option chain for an underlying.

        Args:
            symbol: Underlying symbol (e.g., "NIFTY")
            expiry: Specific expiry date. If None, returns nearest expiry.

        Returns:
            OptionChainSnapshot with all strikes, CE/PE quotes, spot price

        Raises:
            DataUnavailableError: If chain cannot be fetched
        """
        ...

    @abstractmethod
    def get_expiry_dates(self, symbol: str) -> list[date]:
        """
        Get all available expiry dates for an underlying.

        Returns:
            Sorted list of expiry dates (ascending)

        Raises:
            DataUnavailableError: If expiries cannot be fetched
        """
        ...

    def health_check(self) -> bool:
        return True


class NewsDataProvider(ABC):
    """
    Interface for news and event data.
    Phase 1 placeholder — concrete implementations in later phases.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    def get_news(
        self,
        symbol: Optional[str] = None,
        limit: int = 20,
    ) -> list[NewsItem]:
        """
        Fetch recent news.

        Every item MUST have a verifiable source and timestamp.
        Never allow fabricated/hallucinated news.

        Raises:
            DataUnavailableError: If news cannot be fetched
        """
        ...
