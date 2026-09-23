"""
Phase 16 — Abstract Interface for Paid Historical Options Data Providers.

IMPORTANT HONESTY CONSTRAINTS:
- This is a stub interface ONLY. No vendor actually provides data here.
- Do NOT assume any vendor (Sensibull, Opstra, TrueData, GDFL, brokers)
  supplies historical bid/ask data unless you have verified it from an actual
  provider response or dataset.
- All unknown capabilities must be marked REQUIRES_VENDOR_CONFIRMATION.
- All unverified capabilities must be marked REQUIRES_VENDOR_CONFIRMATION.
- Use the capability registry pattern from capability_registry.py.

To implement a concrete provider:
1. Subclass PaidHistoricalOptionsProvider
2. Implement all abstract methods
3. Set `verified_bid_ask = True` ONLY after verifying with an actual dataset
4. Register your capability report with get_capability_registry()
5. Set credentials from environment variables only (never hardcode)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from src.ingestion.capability_registry import (
    DataCapabilityKey,
    DataCapabilityState,
    ProviderCapabilityReport,
)
from src.utils.config import get_config



# =============================================================================
# Bid/Ask data status enum
# =============================================================================

class OptionsDataStatus(str, Enum):
    """
    Status of options data fields, applied per-record.

    SETTLEMENT_PRICE_ONLY  - EOD settlement price, no bid/ask (e.g. Bhavcopy)
    LTP_ONLY               - Last traded price available, no bid/ask
    BID_ASK_AVAILABLE      - Full bid/ask present (verified from source)
    DEPTH_AVAILABLE        - Full market depth (bid/ask + sizes + levels)
    UNKNOWN                - Status not assessed
    REQUIRES_VENDOR_CONFIRMATION - Vendor claims this but not verified
    UNAVAILABLE            - Data not available
    """
    SETTLEMENT_PRICE_ONLY = "SETTLEMENT_PRICE_ONLY"
    LTP_ONLY = "LTP_ONLY"
    BID_ASK_AVAILABLE = "BID_ASK_AVAILABLE"
    DEPTH_AVAILABLE = "DEPTH_AVAILABLE"
    UNKNOWN = "UNKNOWN"
    REQUIRES_VENDOR_CONFIRMATION = "REQUIRES_VENDOR_CONFIRMATION"
    UNAVAILABLE = "UNAVAILABLE"


# =============================================================================
# Canonical historical options tick record schema
# =============================================================================

@dataclass
class HistoricalOptionsTick:
    """
    A single historical observation for an options contract.

    Required fields:
        timestamp        - Point-in-time of observation (timezone-aware preferred)
        underlying       - e.g. "NIFTY"
        expiry_date      - Contract expiry date
        strike_price     - Strike price
        option_type      - "CE" or "PE"

    Price fields (any may be None if not provided by vendor):
        ltp              - Last traded price
        bid_price        - Best bid price (None if not available from this source)
        ask_price        - Best ask price (None if not available from this source)
        bid_size         - Bid quantity at best bid (None if not available)
        ask_size         - Ask quantity at best ask (None if not available)

    Depth fields (None unless vendor provides depth):
        bid_depth        - List of (price, qty) tuples for bid side
        ask_depth        - List of (price, qty) tuples for ask side

    Quantity fields:
        volume           - Traded volume
        open_interest    - Open interest

    Provenance:
        source           - Provider identifier (e.g. "OPSTRA", "TRUEDATA")
        data_status      - OptionsDataStatus enum value
        retrieval_ts     - When this record was retrieved from the vendor
        data_quality     - GOOD / PARTIAL / SUSPECT / UNAVAILABLE
    """
    timestamp: datetime
    underlying: str
    expiry_date: date
    strike_price: float
    option_type: str            # "CE" or "PE"

    # Price — NEVER fabricate; None if absent
    ltp: Optional[float] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None

    # Market depth — None unless vendor provides
    bid_depth: Optional[List[tuple]] = None
    ask_depth: Optional[List[tuple]] = None

    # Volume / OI
    volume: Optional[int] = None
    open_interest: Optional[int] = None

    # Provenance (always required)
    source: str = "UNKNOWN"
    data_status: OptionsDataStatus = OptionsDataStatus.UNKNOWN
    retrieval_ts: Optional[datetime] = None
    data_quality: str = "GOOD"

    def has_bid_ask(self) -> bool:
        """True only if BOTH bid and ask are non-None."""
        return self.bid_price is not None and self.ask_price is not None

    def bid_ask_spread(self) -> Optional[float]:
        if self.has_bid_ask():
            return self.ask_price - self.bid_price  # type: ignore[operator]
        return None


# =============================================================================
# Abstract provider interface
# =============================================================================

class PaidHistoricalOptionsProvider(ABC):
    """
    Abstract interface for paid commercial historical options data providers.

    Concrete implementations must:
    - Read API key from environment (PAID_OPTIONS_PROVIDER_KEY)
    - Report honest capability states — never assume READY without verification
    - Set verified_bid_ask = True only after confirming with actual data sample
    - Return OptionsDataStatus on each record to indicate what fields are real

    Known vendors where this might be implemented (UNVERIFIED — each must be
    confirmed against actual API documentation and live data):
    - Opstra (opstra.in)
    - Sensibull (sensibull.com)
    - TrueData (truedata.in)
    - GDFL (Global Data Feed)
    - NSE Pathshala / Data feeds
    """

    # Subclasses must set this to True ONLY after receiving and parsing
    # an actual data sample that confirms bid/ask fields are populated.
    verified_bid_ask: bool = False

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifier, e.g. 'OPSTRA', 'TRUEDATA'."""
        ...

    @abstractmethod
    def get_capability_report(self) -> ProviderCapabilityReport:
        """
        Return current capability report.
        Must be honest about what is actually verified.
        """
        ...

    @abstractmethod
    def get_historical_ticks(
        self,
        underlying: str,
        expiry_date: date,
        strike_price: float,
        option_type: str,
        from_dt: datetime,
        to_dt: datetime,
    ) -> List[HistoricalOptionsTick]:
        """
        Retrieve historical tick/candle data for a specific options contract.

        Args:
            underlying: e.g. "NIFTY"
            expiry_date: Contract expiry
            strike_price: Strike price
            option_type: "CE" or "PE"
            from_dt: Start datetime (inclusive)
            to_dt: End datetime (inclusive)

        Returns:
            List of HistoricalOptionsTick. Each record carries a data_status
            indicating what fields are actually populated.
            Returns empty list if no data available (never raises silently).

        Raises:
            DataUnavailableError: If provider unreachable or credentials invalid.
        """
        ...

    @abstractmethod
    def get_chain_snapshot(
        self,
        underlying: str,
        snapshot_dt: datetime,
        expiry_date: Optional[date] = None,
    ) -> List[HistoricalOptionsTick]:
        """
        Retrieve all strikes for an underlying at a point in time.

        Returns empty list if not available.
        Raises DataUnavailableError on connectivity/auth failure.
        """
        ...


# =============================================================================
# Null/stub implementation (used when no paid provider is configured)
# =============================================================================

class NoPaidProviderConfigured(PaidHistoricalOptionsProvider):
    """
    Stub implementation returned when no paid provider is configured.

    All capabilities are UNAVAILABLE / REQUIRES_VENDOR_CONFIRMATION.
    This makes it explicit that bid/ask data is not available — no silent failure.
    """

    verified_bid_ask = False

    @property
    def provider_name(self) -> str:
        return "NO_PAID_PROVIDER"

    def get_capability_report(self) -> ProviderCapabilityReport:
        report = ProviderCapabilityReport(
            provider_name="NO_PAID_PROVIDER",
            provider_type="NONE",
            credentials_present=False,
            credentials_valid=False,
            reachable=False,
        )
        report.set(
            DataCapabilityKey.OPTIONS_BID_ASK_READY,
            DataCapabilityState.UNAVAILABLE,
            note=(
                "No paid historical options provider configured. "
                "Set PAID_OPTIONS_PROVIDER_KEY and PAID_OPTIONS_PROVIDER_NAME in .env. "
                "Vendor capability is REQUIRES_VENDOR_CONFIRMATION until verified."
            ),
        )
        report.set(
            DataCapabilityKey.OPTIONS_HISTORICAL_EOD_READY,
            DataCapabilityState.UNAVAILABLE,
            note="Use NSE Bhavcopy for free EOD data (SETTLEMENT_PRICE_ONLY).",
        )
        report.set(
            DataCapabilityKey.OPTIONS_HISTORICAL_INTRADAY_READY,
            DataCapabilityState.REQUIRES_VENDOR_CONFIRMATION,
            note=(
                "Sensibull, Opstra, TrueData, GDFL may provide historical intraday options data. "
                "This has NOT been verified. Capability = REQUIRES_VENDOR_CONFIRMATION."
            ),
        )
        return report

    def get_historical_ticks(self, *args: Any, **kwargs: Any) -> List[HistoricalOptionsTick]:
        from src.ingestion.base import DataUnavailableError
        raise DataUnavailableError(
            "No paid historical options provider configured. "
            "Historical bid/ask options data requires a commercial subscription. "
            "See PAID_OPTIONS_PROVIDER_KEY in .env.example."
        )

    def get_chain_snapshot(self, *args: Any, **kwargs: Any) -> List[HistoricalOptionsTick]:
        from src.ingestion.base import DataUnavailableError
        raise DataUnavailableError(
            "No paid historical options provider configured."
        )


def get_paid_options_provider() -> PaidHistoricalOptionsProvider:
    """
    Return the configured paid historical options provider.

    Returns NoPaidProviderConfigured if PAID_OPTIONS_PROVIDER_NAME is not set.
    """
    config = get_config()
    provider_name = config.env.paid_options_provider_name.strip()

    if not provider_name:
        return NoPaidProviderConfigured()

    # Future: registry of concrete implementations
    # known_providers = {"OPSTRA": OpstraProvider, "TRUEDATA": TrueDataProvider}
    # if provider_name.upper() in known_providers:
    #     return known_providers[provider_name.upper()]()

    from src.ingestion.base import DataUnavailableError
    raise DataUnavailableError(
        f"Paid options provider '{provider_name}' is not implemented. "
        f"To implement it, subclass PaidHistoricalOptionsProvider in "
        f"src/ingestion/paid_options_interface.py."
    )
