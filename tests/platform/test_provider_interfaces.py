"""
Test Plug-and-Play Provider Interfaces and Adapters.
"""

import pytest
from src.platform.providers.daily_provider import DailyProvider
from src.platform.providers.intraday_provider import IntradayProvider
from src.platform.providers.equity_panel_provider import EquityPanelProvider
from src.platform.providers.options_quote_provider import OptionsQuoteProvider


def test_daily_provider_contract():
    provider = DailyProvider()
    meta = provider.metadata
    assert meta.provider_id == "DAILY_INDEX_PROVIDER"
    assert meta.research_readiness == "READY"
    assert meta.coverage_sessions >= 250

    schema = provider.get_schema()
    assert "close" in schema
    assert "volume" in schema

    hc = provider.health_check()
    assert hc["status"] == "HEALTHY"


def test_intraday_provider_blocked_state():
    provider = IntradayProvider()
    meta = provider.metadata
    assert meta.provider_id == "INTRADAY_PROVIDER"
    assert meta.research_readiness == "BLOCKED"
    assert meta.coverage_sessions < 250

    hc = provider.health_check()
    assert hc["status"] == "BLOCKED"
    assert "INSUFFICIENT_HISTORY" in hc["block_reason"]


def test_intraday_provider_adapter_attachment():
    provider = IntradayProvider()

    class MockQualifyingTrueDataAdapter:
        def get_coverage_sessions(self):
            return 500

        def load_bars(self, sym, interval, s, e):
            import pandas as pd
            return pd.DataFrame({"timestamp": ["2026-01-01"], "close": [22000.0]})

    provider.attach_future_provider(MockQualifyingTrueDataAdapter())
    assert provider.metadata.research_readiness == "READY"
    assert provider.metadata.coverage_sessions == 500


def test_equity_panel_provider():
    provider = EquityPanelProvider()
    assert provider.metadata.research_readiness == "READY"
    assert provider.metadata.provenance["constituents_count"] == 50
    panel = provider.load_panel(["RELIANCE"])
    assert not panel.empty


def test_options_quote_provider():
    provider = OptionsQuoteProvider()
    assert provider.metadata.research_readiness == "LIMITED"
    assert provider.metadata.execution_readiness == "BLOCKED"
    assert provider.metadata.provenance["genuine_paired_bid_ask"] == 0
