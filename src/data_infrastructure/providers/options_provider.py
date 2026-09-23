"""
Phase 9 — Concrete Live Options Provider Gateway.

Enforces strict truthfulness regarding live Indian options data.
Unless an authenticated, independently verified broker/exchange feed is configured:
- capabilities report options_chain: False, options_quotes: False
- status reports UNAVAILABLE / UNVERIFIED
- ZERO synthetic or theoretical option chains are returned
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from src.data_infrastructure.models import (
    DataStatus,
    OptionChainSnapshotRecord,
    OptionObservation,
)
from src.data_infrastructure.providers.base import OptionsDataProvider
from src.data_infrastructure.providers.verification import ProviderVerificationEngine


class Phase9OptionsProvider(OptionsDataProvider):
    """
    Live Options Provider Gateway.
    Strictly reports UNAVAILABLE until independently verified legitimate data feed is configured.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._provider_name = "NSE_LIVE_OPTIONS_GATEWAY"
        self._api_key = api_key
        self._is_verified = False  # Set to True only upon successful real-market verification

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def capabilities(self) -> Dict[str, bool]:
        return {
            "options_chain": self._is_verified,
            "options_quotes": self._is_verified,
            "bid_ask": self._is_verified,
            "open_interest": self._is_verified,
            "implied_volatility": self._is_verified,
        }

    def health_check(self) -> Dict[str, Any]:
        status = DataStatus.VERIFIED_REAL_TIME.value if self._is_verified else DataStatus.UNAVAILABLE.value
        return {
            "provider_name": self.provider_name,
            "is_healthy": self._is_verified,
            "status_label": status,
            "notes": "Live options provider feed unconfigured or unverified. Zero synthetic chains permitted.",
            "error_count": 0,
        }

    def get_expiries(self, underlying: str) -> List[date]:
        return []

    def get_strikes(self, underlying: str, expiry: date) -> List[float]:
        return []

    def get_option_chain(self, underlying: str, expiry: date) -> Optional[OptionChainSnapshotRecord]:
        # Record unverified failure evidence
        ProviderVerificationEngine.record_verification(
            provider_name=self.provider_name,
            capability="options_chain",
            test_instrument=underlying.upper(),
            observed_provider_timestamp=None,
            observed_received_timestamp=datetime.now(timezone.utc),
            observed_fields={},
            notes="Live options provider feed unverified. Refusing to synthesize fake option chains.",
        )
        return None

    def get_option_quote(self, contract: str) -> Optional[OptionObservation]:
        return None

    def get_option_quotes(self, contracts: List[str]) -> List[OptionObservation]:
        return []

    def get_contract_metadata(self, contract: str) -> Optional[Dict[str, Any]]:
        return None
