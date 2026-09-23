"""
Phase 16 — Data Capability Registry.

Every provider must report its capabilities explicitly using these states.
A capability is NEVER assumed READY merely because an API exists or credentials
are configured.

IMPORTANT:
- No silent fallbacks. If Kite doesn't have required data, that is BLOCKED, not
  silently handled by falling back to Yahoo.
- Capabilities are assessed per-provider, not aggregated into a single "best effort" result.
- REQUIRES_VENDOR_CONFIRMATION = capability exists in theory but has not been
  verified against an actual response from that vendor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


# =============================================================================
# Capability State Enum
# =============================================================================

class DataCapabilityState(str, Enum):
    """
    Explicit state for a single data capability.

    READY                      - Verified working in this session.
    PARTIAL                    - Works but with known gaps (e.g. some symbols missing).
    BLOCKED                    - Credentials present but capability blocked/rejected.
    UNAVAILABLE                - Credentials absent or provider unreachable.
    REQUIRES_VENDOR_CONFIRMATION - API exists but actual data availability unverified.
    NOT_SUPPORTED              - Provider definitively does not offer this capability.
    """
    READY = "READY"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    REQUIRES_VENDOR_CONFIRMATION = "REQUIRES_VENDOR_CONFIRMATION"
    NOT_SUPPORTED = "NOT_SUPPORTED"


# =============================================================================
# Well-known capability keys
# =============================================================================

class DataCapabilityKey(str, Enum):
    """Standard capability identifiers used across providers."""
    INTRADAY_1M_READY = "INTRADAY_1M_READY"
    INTRADAY_5M_READY = "INTRADAY_5M_READY"
    INTRADAY_15M_READY = "INTRADAY_15M_READY"
    DAILY_OHLCV_READY = "DAILY_OHLCV_READY"
    OPTIONS_LTP_READY = "OPTIONS_LTP_READY"
    OPTIONS_BID_ASK_READY = "OPTIONS_BID_ASK_READY"
    OPTIONS_EXECUTION_READY = "OPTIONS_EXECUTION_READY"
    OPTIONS_HISTORICAL_EOD_READY = "OPTIONS_HISTORICAL_EOD_READY"
    OPTIONS_HISTORICAL_INTRADAY_READY = "OPTIONS_HISTORICAL_INTRADAY_READY"
    PROVENANCE_READY = "PROVENANCE_READY"
    LICENSE_READY = "LICENSE_READY"
    DATA_QUALITY_READY = "DATA_QUALITY_READY"
    FII_DII_READY = "FII_DII_READY"
    INDIA_VIX_READY = "INDIA_VIX_READY"
    MACRO_FEATURES_READY = "MACRO_FEATURES_READY"


# =============================================================================
# Capability Report
# =============================================================================

@dataclass
class CapabilityDetail:
    """Detail for a single capability."""
    key: DataCapabilityKey
    state: DataCapabilityState
    note: str = ""
    verified_at: Optional[datetime] = None
    evidence: str = ""  # e.g. "sampled 5 candles from 2024-01-10"


@dataclass
class ProviderCapabilityReport:
    """
    Full capability report for one data provider.

    This is the authoritative record of what a provider CAN actually supply.
    It must NOT be optimistic — unknown = REQUIRES_VENDOR_CONFIRMATION.
    """
    provider_name: str
    provider_type: str           # "BROKER_API", "PUBLIC_API", "FILE_ARCHIVE"
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    credentials_present: bool = False
    credentials_valid: bool = False
    reachable: bool = False
    capabilities: Dict[str, CapabilityDetail] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def get(self, key: DataCapabilityKey) -> DataCapabilityState:
        """Return capability state, defaulting to UNAVAILABLE if not assessed."""
        detail = self.capabilities.get(key.value)
        if detail is None:
            return DataCapabilityState.UNAVAILABLE
        return detail.state

    def set(
        self,
        key: DataCapabilityKey,
        state: DataCapabilityState,
        note: str = "",
        evidence: str = "",
    ) -> None:
        """Record a capability state."""
        self.capabilities[key.value] = CapabilityDetail(
            key=key,
            state=state,
            note=note,
            verified_at=datetime.utcnow(),
            evidence=evidence,
        )

    def summary(self) -> Dict[str, str]:
        """Return a flat dict of capability_key → state_value for logging."""
        return {k: v.state.value for k, v in self.capabilities.items()}

    def is_ready(self, key: DataCapabilityKey) -> bool:
        return self.get(key) == DataCapabilityState.READY

    def any_ready(self) -> bool:
        return any(
            d.state == DataCapabilityState.READY
            for d in self.capabilities.values()
        )


# =============================================================================
# Registry (in-memory, per-process)
# =============================================================================

class ProviderCapabilityRegistry:
    """
    Stores the last-assessed capability report for each provider.

    Does NOT auto-assess. Assessment happens when a provider is instantiated
    or when `assess()` is explicitly called on a provider.
    """

    def __init__(self) -> None:
        self._reports: Dict[str, ProviderCapabilityReport] = {}

    def register(self, report: ProviderCapabilityReport) -> None:
        self._reports[report.provider_name] = report

    def get(self, provider_name: str) -> Optional[ProviderCapabilityReport]:
        return self._reports.get(provider_name)

    def all_reports(self) -> List[ProviderCapabilityReport]:
        return list(self._reports.values())

    def summary(self) -> Dict[str, Dict[str, str]]:
        return {name: r.summary() for name, r in self._reports.items()}


# Singleton registry
_registry = ProviderCapabilityRegistry()


def get_capability_registry() -> ProviderCapabilityRegistry:
    return _registry
