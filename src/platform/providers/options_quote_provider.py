"""
Historical Options Data Provider.

Manages options chains, settlement prices, LTP, and Bid/Ask quotes.
Separates:
- Settlement & LTP Research: LIMITED (Permitted for IV/theoretical volatility research)
- Options Execution Backtesting: BLOCKED (0 genuine paired quotes, 0% continuous surface)
Enforces Options Quality Levels (L0–L4).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import pandas as pd

from src.platform.providers.base import BaseDataProvider, ProviderMetadata


class OptionsQuoteProvider(BaseDataProvider):
    """
    Provider for options data with explicit quality classification.
    Settlement/IV research is supported; trade execution modelling is strictly gated.
    """

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root
        self._external_adapter: Optional[Any] = None
        self._metadata = ProviderMetadata(
            provider_id="OPTIONS_QUOTE_PROVIDER",
            provider_name="NSE Bhavcopy Derivatives & Options Parquet Store",
            product_name="Historical Index Options Settlement & Quotes",
            source_type="EXCHANGE_DIRECT",
            source_url="https://www.nseindia.com/all-reports",
            retrieval_timestamp="2026-09-09T13:38:00Z",
            coverage_sessions=504,
            date_range_start="2024-01-01",
            date_range_end="2026-03-01",
            timestamp_quality="DAILY",
            corporate_action_adjusted=False,
            validation_status="VERIFIED_PARTIAL",
            licensing_metadata={
                "license_type": "PUBLIC_EXCHANGE_DISSEMINATION",
                "commercial_redistribution": False,
                "research_use": True,
            },
            research_readiness="LIMITED",  # Valid for IV / theoretical volatility
            execution_readiness="BLOCKED",  # Execution backtesting blocked
            provenance={
                "total_records": 17607,
                "genuine_paired_bid_ask": 0,
                "synthetic_paired_fixtures": 117,
                "continuous_executable_surface_pct": 0.0,
                "options_quality_level": "LEVEL_0",
                "confidence": "HIGH",
            },
        )

    @property
    def metadata(self) -> ProviderMetadata:
        return self._metadata

    def get_schema(self) -> Dict[str, str]:
        return {
            "timestamp": "str (ISO 8601)",
            "underlying": "str",
            "expiry": "str (YYYY-MM-DD)",
            "strike": "float",
            "option_type": "str (CE or PE)",
            "close": "float",
            "settle_price": "float",
            "volume": "int",
            "open_interest": "int",
            "bid": "float (Optional / UNAVAILABLE in current baseline)",
            "ask": "float (Optional / UNAVAILABLE in current baseline)",
        }

    def load_options_records(self, symbol: str = "NIFTY") -> pd.DataFrame:
        """
        Loads options settlement records from local store.
        """
        if self._external_adapter is not None:
            return self._external_adapter.load_records(symbol)

        cache_path = os.path.join(self.workspace_root, "data", "options_cache.parquet")
        if os.path.exists(cache_path):
            return pd.read_parquet(cache_path)

        # Fallback empty dataframe with standard schema
        return pd.DataFrame(columns=[
            "timestamp", "underlying", "expiry", "strike", "option_type",
            "close", "settle_price", "volume", "open_interest", "bid", "ask"
        ])

    def attach_future_options_feed(self, adapter: Any) -> None:
        """
        Attaches a qualifying future options data feed (e.g. NSE Data & Analytics).
        """
        self._external_adapter = adapter
        if hasattr(adapter, "get_options_quality_level"):
            lvl = adapter.get_options_quality_level()
            if lvl in ["LEVEL_3", "LEVEL_4"]:
                self._metadata.execution_readiness = "READY"
                self._metadata.research_readiness = "READY"
                self._metadata.validation_status = "VERIFIED_RESEARCH_GRADE"

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "LIMITED_TO_SETTLEMENT_IV",
            "records_count": self._metadata.provenance.get("total_records", 17607),
            "genuine_paired_quotes": self._metadata.provenance.get("genuine_paired_bid_ask", 0),
            "continuous_surface_pct": self._metadata.provenance.get("continuous_executable_surface_pct", 0.0),
            "options_quality_level": self._metadata.provenance.get("options_quality_level", "LEVEL_0"),
            "execution_readiness": "BLOCKED",
            "research_readiness": "LIMITED",
        }
