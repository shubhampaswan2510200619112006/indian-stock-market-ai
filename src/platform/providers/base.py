"""
Unified Base Data Provider Contract.

Defines the plug-and-play adapter interface that any current or future data vendor
must implement to attach to the research platform.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional


@dataclass
class ProviderMetadata:
    provider_id: str
    provider_name: str
    product_name: str
    source_type: str  # EXCHANGE_DIRECT, AUTHORIZED_VENDOR, BROKER_API, PUBLIC_ENDPOINT
    source_url: str
    retrieval_timestamp: str
    coverage_sessions: int
    date_range_start: str
    date_range_end: str
    timestamp_quality: str  # NANOSECOND, MICROSECOND, MILLISECOND, SECOND, MINUTE, DAILY
    corporate_action_adjusted: bool
    validation_status: str  # VERIFIED, UNVERIFIED, NOT_AVAILABLE
    licensing_metadata: Dict[str, Any] = field(default_factory=dict)
    research_readiness: str = "BLOCKED"  # READY, LIMITED, BLOCKED
    execution_readiness: str = "BLOCKED"  # READY, BLOCKED, NOT_APPLICABLE
    provenance: Dict[str, Any] = field(default_factory=dict)


class BaseDataProvider(ABC):
    """
    Abstract interface for all platform data providers.
    Exposes complete schema, provenance, coverage, and readiness metadata.
    """

    @property
    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        """Returns standard metadata for the provider."""
        ...

    @property
    def provider_name(self) -> str:
        return self.metadata.provider_name

    @property
    def research_readiness(self) -> str:
        return self.metadata.research_readiness

    @property
    def execution_readiness(self) -> str:
        return self.metadata.execution_readiness

    @abstractmethod
    def get_schema(self) -> Dict[str, str]:
        """Returns the dictionary mapping field names to data types."""
        ...

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Runs diagnostics on the data provider adapter."""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Returns a serialized view of provider metadata."""
        return asdict(self.metadata)
