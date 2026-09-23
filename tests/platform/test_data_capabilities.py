"""
Test Data Capabilities Registry.
"""

import pytest
from src.platform.capabilities import CapabilityRegistry, get_capability_registry


def test_capability_registry_initialization():
    reg = CapabilityRegistry()
    caps = reg.all_capabilities()
    assert len(caps) >= 7

    # Ready capabilities
    assert caps["daily_index"].research_readiness == "READY"
    assert caps["daily_index"].available is True
    assert caps["cross_sectional_equities"].research_readiness == "READY"
    assert caps["cross_sectional_equities"].available is True

    # Blocked intraday capabilities
    assert caps["intraday_1m"].research_readiness == "BLOCKED"
    assert caps["intraday_1m"].block_reason == "INSUFFICIENT_VERIFIED_INTRADAY_HISTORY"
    assert caps["intraday_5m"].research_readiness == "BLOCKED"
    assert caps["intraday_5m"].block_reason == "INSUFFICIENT_VERIFIED_INTRADAY_HISTORY"

    # Options capabilities
    assert caps["historical_options_ltp"].research_readiness == "LIMITED"
    assert caps["historical_options_ltp"].execution_readiness == "BLOCKED"
    assert caps["historical_options_bid_ask"].research_readiness == "BLOCKED"
    assert caps["historical_options_bid_ask"].available is False
    assert caps["continuous_options_quote_surface"].execution_readiness == "BLOCKED"
    assert caps["continuous_options_quote_surface"].available is False


def test_singleton_getter():
    r1 = get_capability_registry()
    r2 = get_capability_registry()
    assert r1 is r2
