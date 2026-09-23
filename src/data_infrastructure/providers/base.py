"""
Phase 9 — Provider Abstraction Interfaces.

Defines pluggable, vendor-agnostic abstract interfaces for:
- MarketDataProvider (live/delayed spot and index quotes)
- OptionsDataProvider (live/delayed options chain and quote feeds)
- HistoricalMarketDataProvider (historical daily and intraday candles)
- HistoricalOptionsDataProvider (historical options settlement and intraday quotes)
- ReferenceDataProvider (calendar, instruments, corporate actions)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from src.data_infrastructure.models import (
    DataStatus,
    MarketObservation,
    OptionChainSnapshotRecord,
    OptionObservation,
)


class BaseDataProvider(ABC):
    """Base interface for all data providers in Phase 9."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique vendor/system identifier (e.g., 'YFINANCE', 'NSE_BHAVCOPY')."""
        ...

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Category: MARKET_DATA, OPTIONS_DATA, HISTORICAL_DATA, REFERENCE_DATA."""
        ...

    @abstractmethod
    def capabilities(self) -> Dict[str, bool]:
        """Dictionary of supported capabilities with boolean flags."""
        ...

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Health diagnostics including liveness, latency, error count, and status."""
        ...

    def licensing_info(self) -> Dict[str, Any]:
        """Truthful licensing and usage rights metadata."""
        return {
            "provider": self.provider_name,
            "licensing_status": "UNVERIFIED",
            "commercial_use_permitted": False,
            "redistribution_permitted": False,
            "attribution_required": True,
            "notes": "Public/default tier with unverified legal distribution rights.",
        }


class MarketDataProvider(BaseDataProvider):
    """Interface for real-time and delayed spot / index market observations."""

    @property
    def provider_type(self) -> str:
        return "MARKET_DATA"

    @abstractmethod
    def get_quote(self, symbol: str) -> Optional[MarketObservation]:
        """Fetches normalized market observation with complete provenance."""
        ...

    @abstractmethod
    def get_quotes(self, symbols: List[str]) -> List[MarketObservation]:
        """Fetches multiple normalized quotes in batch."""
        ...

    @abstractmethod
    def get_intraday_candles(
        self,
        symbol: str,
        interval: str = "1m",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Fetches genuine intraday candles from provider."""
        ...

    @abstractmethod
    def get_daily_candles(
        self,
        symbol: str,
        start: date,
        end: date,
    ) -> List[Dict[str, Any]]:
        """Fetches genuine daily OHLCV candles."""
        ...

    @abstractmethod
    def get_market_status(self) -> str:
        """Returns provider-observed market session state."""
        ...


class OptionsDataProvider(BaseDataProvider):
    """Interface for live and near-live option chains and contract observations."""

    @property
    def provider_type(self) -> str:
        return "OPTIONS_DATA"

    @abstractmethod
    def get_expiries(self, underlying: str) -> List[date]:
        """Returns available expiration dates for underlying."""
        ...

    @abstractmethod
    def get_strikes(self, underlying: str, expiry: date) -> List[float]:
        """Returns available strikes for underlying and expiration."""
        ...

    @abstractmethod
    def get_option_chain(self, underlying: str, expiry: date) -> Optional[OptionChainSnapshotRecord]:
        """Constructs a normalized point-in-time option chain snapshot."""
        ...

    @abstractmethod
    def get_option_quote(self, contract: str) -> Optional[OptionObservation]:
        """Fetches normalized quote for a specific option contract."""
        ...

    @abstractmethod
    def get_option_quotes(self, contracts: List[str]) -> List[OptionObservation]:
        """Fetches quotes for multiple option contracts."""
        ...

    @abstractmethod
    def get_contract_metadata(self, contract: str) -> Optional[Dict[str, Any]]:
        """Returns static contract specification."""
        ...


class HistoricalMarketDataProvider(BaseDataProvider):
    """Interface for loading historical equity and index series."""

    @property
    def provider_type(self) -> str:
        return "HISTORICAL_MARKET_DATA"

    @abstractmethod
    def load_daily_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """Loads historical daily OHLCV records."""
        ...

    @abstractmethod
    def load_intraday_bars(
        self,
        symbol: str,
        interval: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> List[Dict[str, Any]]:
        """Loads historical intraday candles."""
        ...


class HistoricalOptionsDataProvider(BaseDataProvider):
    """Interface for loading historical options datasets and bhavcopy archives."""

    @property
    def provider_type(self) -> str:
        return "HISTORICAL_OPTIONS_DATA"

    @abstractmethod
    def load_historical_option_quotes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> List[OptionObservation]:
        """Loads point-in-time historical option quotes."""
        ...

    @abstractmethod
    def get_historical_chain_snapshot(
        self,
        symbol: str,
        timestamp: datetime,
    ) -> Optional[OptionChainSnapshotRecord]:
        """Constructs historical option chain timestamped at exact point in time."""
        ...

    @abstractmethod
    def audit_dataset_quality(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Performs data quality and completeness audit over historical range."""
        ...


class ReferenceDataProvider(BaseDataProvider):
    """Interface for exchange reference data, instruments, calendars, and corporate actions."""

    @property
    def provider_type(self) -> str:
        return "REFERENCE_DATA"

    @abstractmethod
    def get_calendar(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Returns trading session schedule for date range."""
        ...

    @abstractmethod
    def get_corporate_actions(self, symbol: str) -> List[Dict[str, Any]]:
        """Returns corporate actions and adjustment factors."""
        ...

    @abstractmethod
    def get_instrument_master(self) -> List[Dict[str, Any]]:
        """Returns active tradable instruments specification."""
        ...
