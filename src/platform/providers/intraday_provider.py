"""
Intraday Market Data Provider.

Manages 1-minute and 5-minute historical OHLCV data.
Current State: BLOCKED (7 sessions for 1m, 59 sessions for 5m; threshold >= 250 sessions).
Provides pluggable adapter interface to attach qualifying future data without rewriting research code.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import pandas as pd

from src.platform.providers.base import BaseDataProvider, ProviderMetadata


class IntradayProvider(BaseDataProvider):
    """
    Provider for high-resolution intraday candles (1m and 5m).
    Reflects the empirical audit: currently insufficient for confirmatory research.
    """

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root
        self._external_adapter: Optional[Any] = None
        self._metadata = ProviderMetadata(
            provider_id="INTRADAY_PROVIDER",
            provider_name="Yahoo Finance Chart API / Local Intraday Parquet Cache",
            product_name="Intraday 1m & 5m Index Candles",
            source_type="PUBLIC_ENDPOINT",
            source_url="https://finance.yahoo.com",
            retrieval_timestamp="2026-09-09T13:38:00Z",
            coverage_sessions=59,  # 5m max
            date_range_start="2026-01-01",
            date_range_end="2026-03-01",
            timestamp_quality="MINUTE",
            corporate_action_adjusted=False,
            validation_status="VERIFIED_LIMITED",
            licensing_metadata={
                "license_type": "PUBLIC_UNOFFICIAL",
                "commercial_redistribution": False,
                "research_use": True,
            },
            research_readiness="BLOCKED",
            execution_readiness="BLOCKED",
            provenance={
                "audit_origin": "Phase 10B Empirical Ingestion Audit",
                "insufficient_reason": "INSUFFICIENT_HISTORY (<250 sessions required for confirmatory research)",
                "confidence": "HIGH",
            },
        )

    @property
    def metadata(self) -> ProviderMetadata:
        return self._metadata

    def get_schema(self) -> Dict[str, str]:
        return {
            "timestamp": "datetime (ISO 8601)",
            "symbol": "str",
            "interval": "str (1m or 5m)",
            "open": "float",
            "high": "float",
            "low": "float",
            "close": "float",
            "volume": "int",
        }

    def load_intraday_bars(
        self,
        symbol: str,
        interval: str = "5m",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Loads available intraday bars.
        Returns DataFrame tagged with coverage metadata.
        """
        if self._external_adapter is not None:
            return self._external_adapter.load_bars(symbol, interval, start_time, end_time)

        # Look in data/phase10b/intraday/
        cache_path = os.path.join(
            self.workspace_root,
            "data",
            "phase10b",
            "intraday",
            f"{symbol.lower()}_{interval}.parquet",
        )
        if os.path.exists(cache_path):
            return pd.read_parquet(cache_path)

        # Fallback empty dataframe with standard schema
        return pd.DataFrame(columns=["timestamp", "symbol", "interval", "open", "high", "low", "close", "volume"])

    def attach_future_provider(self, adapter: Any) -> None:
        """
        Attaches a qualifying future external provider adapter (e.g. TrueData).
        """
        self._external_adapter = adapter
        # Re-evaluate readiness
        if hasattr(adapter, "get_coverage_sessions") and adapter.get_coverage_sessions() >= 250:
            self._metadata.research_readiness = "READY"
            self._metadata.validation_status = "VERIFIED_EXTERNAL"
            self._metadata.coverage_sessions = adapter.get_coverage_sessions()

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "BLOCKED" if self._metadata.research_readiness == "BLOCKED" else "HEALTHY",
            "coverage_sessions": self._metadata.coverage_sessions,
            "required_sessions": 250,
            "research_readiness": self._metadata.research_readiness,
            "block_reason": "INSUFFICIENT_HISTORY (<250 sessions)",
        }
