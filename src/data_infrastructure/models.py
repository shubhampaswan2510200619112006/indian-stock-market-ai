"""
Phase 9 — Data Infrastructure Core Domain Models & Schemas.

Implements:
- Standardized DataStatus vocabulary across the platform.
- Rigorous timestamp architecture (provider, received, processed, request, response).
- Complete observation provenance and non-destructive raw data preservation.
- Strict distinction between PROVIDER_SUPPLIED and LOCALLY_CALCULATED fields.
- Dataset snapshot and data lineage representations.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DataStatus(str, Enum):
    """
    Standardized, authoritative data status vocabulary.
    Used consistently across market data, options, paper trading, and storage.
    """
    VERIFIED_REAL_TIME = "VERIFIED_REAL_TIME"
    VERIFIED_NEAR_REAL_TIME = "VERIFIED_NEAR_REAL_TIME"
    VERIFIED_DELAYED = "VERIFIED_DELAYED"
    HISTORICAL = "HISTORICAL"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"
    UNVERIFIED = "UNVERIFIED"

    @property
    def is_potentially_executable(self) -> bool:
        """Only fresh realtime or fresh delayed observations with quotes are potentially executable."""
        return self in (
            DataStatus.VERIFIED_REAL_TIME,
            DataStatus.VERIFIED_NEAR_REAL_TIME,
            DataStatus.VERIFIED_DELAYED,
        )


class SourceType(str, Enum):
    PROVIDER_SUPPLIED = "PROVIDER_SUPPLIED"
    LOCALLY_CALCULATED = "LOCALLY_CALCULATED"
    UNAVAILABLE = "UNAVAILABLE"


class ObservationTimestamps(BaseModel):
    """
    Multi-point timestamp capture for data provenance and latency measurement.
    """
    provider_timestamp: datetime
    received_timestamp: datetime
    processed_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    exchange_timestamp: Optional[datetime] = None
    request_timestamp: Optional[datetime] = None
    response_timestamp: Optional[datetime] = None

    def validate_ordering(self) -> tuple[bool, str]:
        """
        Validates internal timestamp relationships.
        For delayed/historical data, provider_timestamp < received_timestamp is expected.
        However, received_timestamp <= processed_timestamp must always hold.
        Provider timestamp must not be arbitrarily in the future relative to reception.
        """
        # Ensure UTC tz-awareness for safe comparison
        p_ts = self.provider_timestamp if self.provider_timestamp.tzinfo else self.provider_timestamp.replace(tzinfo=timezone.utc)
        r_ts = self.received_timestamp if self.received_timestamp.tzinfo else self.received_timestamp.replace(tzinfo=timezone.utc)
        proc_ts = self.processed_timestamp if self.processed_timestamp.tzinfo else self.processed_timestamp.replace(tzinfo=timezone.utc)

        # 1. Processing cannot complete before reception
        if proc_ts < r_ts:
            return False, f"processed_timestamp ({proc_ts}) precedes received_timestamp ({r_ts})"

        # 2. Clock skew check: provider timestamp in future relative to reception by > 120s
        clock_skew_sec = (p_ts - r_ts).total_seconds()
        if clock_skew_sec > 120.0:
            return False, f"provider_timestamp ({p_ts}) is {clock_skew_sec:.1f}s in future relative to received_timestamp ({r_ts})"

        return True, "VALID_TIMESTAMPS"

    def calculate_latencies(self) -> Dict[str, Optional[float]]:
        """
        Calculates separate latency components.
        Never collapses the entire difference into 'market latency'.
        """
        latencies: Dict[str, Optional[float]] = {
            "network_request_to_response_ms": None,
            "provider_to_received_latency_ms": None,
            "received_to_processed_latency_ms": None,
        }

        r_ts = self.received_timestamp if self.received_timestamp.tzinfo else self.received_timestamp.replace(tzinfo=timezone.utc)
        p_ts = self.provider_timestamp if self.provider_timestamp.tzinfo else self.provider_timestamp.replace(tzinfo=timezone.utc)
        proc_ts = self.processed_timestamp if self.processed_timestamp.tzinfo else self.processed_timestamp.replace(tzinfo=timezone.utc)

        if self.request_timestamp:
            req_ts = self.request_timestamp if self.request_timestamp.tzinfo else self.request_timestamp.replace(tzinfo=timezone.utc)
            latencies["network_request_to_response_ms"] = round((r_ts - req_ts).total_seconds() * 1000.0, 2)

        latencies["provider_to_received_latency_ms"] = round((r_ts - p_ts).total_seconds() * 1000.0, 2)
        latencies["received_to_processed_latency_ms"] = round((proc_ts - r_ts).total_seconds() * 1000.0, 2)

        return latencies


class MarketObservation(BaseModel):
    """
    Normalized, auditable spot or index observation with complete provenance.
    """
    observation_id: str
    provider: str
    provider_symbol: str
    symbol: str
    timestamps: ObservationTimestamps
    last_price: Optional[float] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    data_status: DataStatus
    validation_status: str = "VALID"
    is_executable: bool = False
    raw_payload: Optional[Dict[str, Any]] = None
    dataset_id: Optional[str] = None
    dataset_version: Optional[str] = None
    ingestion_batch_id: Optional[str] = None


class OptionObservation(BaseModel):
    """
    Timestamped options contract market observation.
    Separates static contract identity from time-varying market observables.
    """
    observation_id: str
    contract_id: str
    contract_symbol: str
    underlying: str
    expiry_date: date
    strike_price: float
    option_type: str  # "CE" or "PE"
    instrument_type: str = "INDEX_OPTION"
    timestamps: ObservationTimestamps

    # Dynamic Market Data
    last_price: Optional[float] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    change_in_oi: Optional[int] = None

    # IV distinction
    iv: Optional[float] = None
    iv_source: SourceType = SourceType.UNAVAILABLE
    iv_calculation_details: Optional[Dict[str, Any]] = None

    # Greeks distinction
    greeks: Optional[Dict[str, float]] = None
    greeks_source: SourceType = SourceType.UNAVAILABLE

    # Metadata
    lot_size: int = 1
    provider: str = "UNKNOWN"
    data_status: DataStatus = DataStatus.UNVERIFIED
    validation_status: str = "VALID"
    is_executable: bool = False
    ingestion_batch_id: Optional[str] = None
    dataset_id: Optional[str] = None
    dataset_version: Optional[str] = None


class OptionChainRow(BaseModel):
    """
    Normalized representation of a single strike row in an option chain snapshot.
    """
    strike_price: float
    ce_ltp: Optional[float] = None
    ce_bid: Optional[float] = None
    ce_ask: Optional[float] = None
    ce_oi: Optional[int] = None
    ce_volume: Optional[int] = None
    ce_iv: Optional[float] = None
    ce_iv_source: SourceType = SourceType.UNAVAILABLE
    ce_delta: Optional[float] = None

    pe_ltp: Optional[float] = None
    pe_bid: Optional[float] = None
    pe_ask: Optional[float] = None
    pe_oi: Optional[int] = None
    pe_volume: Optional[int] = None
    pe_iv: Optional[float] = None
    pe_iv_source: SourceType = SourceType.UNAVAILABLE
    pe_delta: Optional[float] = None


class OptionChainSnapshotRecord(BaseModel):
    """
    Complete point-in-time option chain for an underlying and expiry.
    """
    snapshot_id: str
    underlying: str
    expiry_date: date
    spot_price: float
    days_to_expiry: float
    timestamps: ObservationTimestamps
    provider: str
    data_status: DataStatus
    rows: List[OptionChainRow] = Field(default_factory=list)
    total_ce_oi: int = 0
    total_pe_oi: int = 0
    pcr_oi: Optional[float] = None


class DatasetSnapshotMetadata(BaseModel):
    """
    Immutable metadata record for a historical research dataset snapshot.
    """
    snapshot_id: str
    dataset_id: str
    dataset_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider: str
    date_range_start: date
    date_range_end: date
    observation_count: int
    instruments: List[str]
    ltp_coverage_pct: float
    bid_ask_coverage_pct: float
    oi_coverage_pct: float
    volume_coverage_pct: float
    iv_coverage_pct: float
    quality_status: str
    is_immutable: bool = True
    manifest: Dict[str, Any] = Field(default_factory=dict)


class DataLineageRecord(BaseModel):
    """
    Audit trail connecting downstream artifacts (features, predictions, backtest runs)
    back to their source dataset snapshot and raw observations.
    """
    lineage_id: str
    target_artifact_type: str  # FEATURE_ROW, PREDICTION, BACKTEST_RUN, PAPER_ORDER
    target_artifact_id: str
    dataset_snapshot_id: str
    source_observation_ids: List[str]
    feature_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    lineage_hash: str = ""

    def compute_hash(self) -> str:
        """Computes a cryptographic sha256 hash representing this exact lineage linkage."""
        content = f"{self.target_artifact_type}:{self.target_artifact_id}:{self.dataset_snapshot_id}:{','.join(sorted(self.source_observation_ids))}:{self.feature_version}"
        self.lineage_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return self.lineage_hash
