"""
Tests for Phase 9 Data Providers & 15-Dimension Scorecard.
"""

from datetime import date
import pytest

from src.data_infrastructure.providers.base import (
    BaseDataProvider,
    MarketDataProvider,
    OptionsDataProvider,
    HistoricalOptionsDataProvider,
)
from src.data_infrastructure.providers.market_provider import Phase9YFinanceProvider
from src.data_infrastructure.providers.options_provider import Phase9OptionsProvider
from src.data_infrastructure.providers.bhavcopy_provider import NSEBhavcopyHistoricalProvider
from src.data_infrastructure.providers.scorecard import (
    build_bhavcopy_scorecard,
    build_yfinance_scorecard,
)
from src.data_infrastructure.providers.verification import ProviderVerificationEngine


def test_market_provider_capabilities_and_health():
    provider = Phase9YFinanceProvider()
    caps = provider.capabilities()

    assert caps["live_quotes"] is True
    assert caps["bid_ask"] is False  # Honest disclosure: Free tier lacks Bid/Ask
    assert caps["options_chain"] is False

    health = provider.health_check()
    assert "provider_name" in health
    assert health["provider_name"] == "YFINANCE"
    assert "latency_ms" in health


def test_yfinance_scorecard_evaluates_hard_failures():
    scorecard = build_yfinance_scorecard()
    assert scorecard.provider_name == "YFINANCE"
    assert len(scorecard.dimensions) == 15
    assert scorecard.weighted_score > 0.0

    # Must fail execution suitability due to missing Bid/Ask
    assert scorecard.is_suitable_for_execution is False
    assert any("NO_EXECUTABLE_BID_ASK" in hf for hf in scorecard.hard_failures)

    # But suitable for historical research
    assert scorecard.is_suitable_for_historical_research is True


def test_bhavcopy_scorecard_evaluates_hard_failures():
    scorecard = build_bhavcopy_scorecard()
    assert scorecard.provider_name == "NSE_BHAVCOPY_ARCHIVE"
    assert len(scorecard.dimensions) == 15

    # EOD Settlement lacks Bid/Ask -> cannot be used for execution research
    assert scorecard.is_suitable_for_execution is False
    assert any("NO_BID_ASK" in hf for hf in scorecard.hard_failures)
    assert scorecard.is_suitable_for_historical_research is True


def test_live_options_provider_reports_unverified():
    provider = Phase9OptionsProvider()
    caps = provider.capabilities()
    assert caps["options_chain"] is False

    health = provider.health_check()
    assert health["is_healthy"] is False
    assert health["status_label"] == "UNAVAILABLE"

    # Zero fake chains generated
    chain = provider.get_option_chain("NIFTY", date.today())
    assert chain is None


def test_provider_verification_engine_records_evidence():
    rec = ProviderVerificationEngine.record_verification(
        provider_name="TEST_PROVIDER",
        capability="market_quotes",
        test_instrument="NIFTY",
        observed_provider_timestamp=None,
        observed_received_timestamp=None,
        observed_fields={"ltp": 23000.0},
        notes="Automated test verification.",
    )
    assert rec["verification_id"].startswith("VERIF-")
    assert rec["result"] == "PASS"
    assert rec["provider_name"] == "TEST_PROVIDER"
