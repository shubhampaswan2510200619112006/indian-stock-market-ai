"""
Abstract base class for Historical Options Data Providers.

PROVIDER ABSTRACTION:
Allows importing historical option chains (EOD or intraday) from CSV, Parquet, broker archives,
or commercial vendors into the existing schema WITHOUT modifying:
- strategy engine
- pricing engine
- IV engine
- Greeks engine
- backtesting engine
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from src.ingestion.schemas import OptionChainSnapshot, OptionQuote


class HistoricalDataQualityReport(BaseModel):
    """Quality and completeness audit report for a historical options dataset."""
    symbol: str
    data_source: str
    granularity: str                     # "EOD", "1MIN", "5MIN", "15MIN"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_quote_records: int = 0
    total_contracts_count: int = 0
    unique_expiries_count: int = 0
    unique_strikes_count: int = 0
    missing_ltp_pct: float = 0.0
    missing_bid_ask_pct: float = 0.0
    missing_oi_pct: float = 0.0
    missing_volume_pct: float = 0.0
    duplicate_records_count: int = 0
    timestamp_gaps_count: int = 0
    is_suitable_for_backtesting: bool = False
    audit_notes: List[str] = Field(default_factory=list)


class HistoricalOptionsDataProvider(ABC):
    """
    Interface for importing and loading historical option chains.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier (e.g., 'CSV_ARCHIVE', 'DHAN_HISTORICAL')."""
        ...

    @abstractmethod
    def load_historical_quotes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> List[OptionQuote]:
        """
        Loads timestamped historical option quotes for a given symbol and date range.
        """
        ...

    @abstractmethod
    def get_historical_chain_snapshot(
        self,
        symbol: str,
        timestamp: datetime,
    ) -> Optional[OptionChainSnapshot]:
        """
        Constructs a point-in-time OptionChainSnapshot timestamped at exactly T.
        """
        ...

    @abstractmethod
    def audit_dataset_quality(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> HistoricalDataQualityReport:
        """
        Performs a data quality audit over the requested historical range.
        """
        ...
