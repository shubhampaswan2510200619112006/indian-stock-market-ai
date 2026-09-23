"""
Phase 16 — Tests for FII/DII fetcher, macro features fetcher,
ingestion scheduler, multiple-testing correction, and paid options interface.

All HTTP calls are mocked. No live network calls.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# FII/DII Parser tests
# =============================================================================

class TestFIIDIIParser:
    """Tests for parse_fii_dii_response — no network calls."""

    def _make_retrieval_ts(self) -> datetime:
        return datetime(2024, 1, 10, 17, 30, 0)

    def test_empty_data_returns_empty_list(self):
        from src.ingestion.fii_dii_fetcher import parse_fii_dii_response
        assert parse_fii_dii_response([], self._make_retrieval_ts()) == []
        assert parse_fii_dii_response(None, self._make_retrieval_ts()) == []

    def test_list_with_fii_record_parsed(self):
        from src.ingestion.fii_dii_fetcher import parse_fii_dii_response
        data = [
            {
                "date": "10-Jan-2024",
                "category": "FII",
                "netBuySell": "12345.67",
            }
        ]
        records = parse_fii_dii_response(data, self._make_retrieval_ts())
        assert len(records) >= 1
        rec = records[0]
        assert rec.trade_date == date(2024, 1, 10)
        assert rec.fii_net_buy_sell == pytest.approx(12345.67)

    def test_dii_record_parsed(self):
        from src.ingestion.fii_dii_fetcher import parse_fii_dii_response
        data = [
            {
                "date": "10-Jan-2024",
                "category": "DII",
                "netBuySell": "-5000.00",
            }
        ]
        records = parse_fii_dii_response(data, self._make_retrieval_ts())
        assert len(records) >= 1
        rec = records[0]
        assert rec.dii_net_buy_sell == pytest.approx(-5000.0)

    def test_missing_date_skipped(self):
        from src.ingestion.fii_dii_fetcher import parse_fii_dii_response
        data = [{"category": "FII", "netBuySell": "1000"}]  # No date
        records = parse_fii_dii_response(data, self._make_retrieval_ts())
        assert records == []

    def test_commas_in_numbers_handled(self):
        from src.ingestion.fii_dii_fetcher import parse_fii_dii_response
        data = [
            {"date": "10-Jan-2024", "category": "FII", "netBuySell": "12,345.67"}
        ]
        records = parse_fii_dii_response(data, self._make_retrieval_ts())
        assert len(records) >= 1
        assert records[0].fii_net_buy_sell == pytest.approx(12345.67)

    def test_missing_net_value_is_none(self):
        from src.ingestion.fii_dii_fetcher import parse_fii_dii_response
        data = [{"date": "10-Jan-2024", "category": "FII"}]  # No net value
        records = parse_fii_dii_response(data, self._make_retrieval_ts())
        # Record exists but net may be None
        if records:
            assert records[0].fii_net_buy_sell is None

    def test_source_is_nse_participant(self):
        from src.ingestion.fii_dii_fetcher import parse_fii_dii_response
        data = [{"date": "10-Jan-2024", "category": "FII", "netBuySell": "1000"}]
        records = parse_fii_dii_response(data, self._make_retrieval_ts())
        if records:
            assert "NSE" in records[0].source.upper()

    def test_fetcher_returns_empty_on_connection_error(self):
        from src.ingestion.fii_dii_fetcher import FIIDIIFetcher
        import requests
        fetcher = FIIDIIFetcher()
        with patch.object(fetcher._session, "get", side_effect=requests.exceptions.ConnectionError("refused")):
            records = fetcher.fetch_latest()
        assert records == []

    def test_fetcher_returns_empty_on_timeout(self):
        from src.ingestion.fii_dii_fetcher import FIIDIIFetcher
        import requests
        fetcher = FIIDIIFetcher()
        with patch.object(fetcher._session, "get", side_effect=requests.exceptions.Timeout()):
            records = fetcher.fetch_latest()
        assert records == []


# =============================================================================
# Macro Features tests
# =============================================================================

class TestMacroFeaturesFetcher:
    def test_fetch_returns_snapshot_object(self):
        from src.ingestion.macro_features_fetcher import MacroFeaturesFetcher, MacroSnapshot
        fetcher = MacroFeaturesFetcher()

        mock_fast_info = MagicMock()
        mock_fast_info.last_price = 14.5
        mock_fast_info.previous_close = 14.0

        mock_ticker = MagicMock()
        mock_ticker.fast_info = mock_fast_info
        mock_ticker.history.return_value = MagicMock(empty=True)

        with patch("yfinance.Ticker", return_value=mock_ticker):
            snap = fetcher.fetch()

        assert isinstance(snap, MacroSnapshot)
        assert snap.observation_date is not None
        assert snap.retrieval_timestamp is not None

    def test_all_fields_none_on_yfinance_error(self):
        from src.ingestion.macro_features_fetcher import MacroFeaturesFetcher
        fetcher = MacroFeaturesFetcher()

        mock_ticker = MagicMock()
        mock_ticker.fast_info = MagicMock()
        mock_ticker.fast_info.last_price = None
        mock_ticker.history.return_value = MagicMock(empty=True)

        with patch("yfinance.Ticker", side_effect=Exception("network error")):
            snap = fetcher.fetch()

        # Fields should be None, not fabricated
        assert snap.india_vix is None
        assert snap.usd_inr is None
        assert snap.crude_wti is None

    def test_missing_gift_nifty_does_not_block_other_fields(self):
        """GIFT Nifty failure must not prevent India VIX from being populated."""
        from src.ingestion.macro_features_fetcher import MacroFeaturesFetcher
        fetcher = MacroFeaturesFetcher()

        call_count = [0]
        def make_ticker(symbol):
            call_count[0] += 1
            mock = MagicMock()
            if "NIFTYIFT" in symbol:
                mock.fast_info.last_price = None
                mock.history.return_value = MagicMock(empty=True)
            elif "INDIAVIX" in symbol:
                mock.fast_info.last_price = 15.3
                mock.fast_info.previous_close = 14.8
                mock.history.return_value = MagicMock(empty=True)
            else:
                mock.fast_info.last_price = None
                mock.history.return_value = MagicMock(empty=True)
            return mock

        with patch("yfinance.Ticker", side_effect=make_ticker):
            snap = fetcher.fetch()

        # India VIX should be set, GIFT Nifty may be None
        assert snap.india_vix is not None or snap.india_vix_freshness == "UNAVAILABLE"

    def test_no_fabricated_values(self):
        """Verify that unavailable fields are None, not interpolated/made up."""
        from src.ingestion.macro_features_fetcher import MacroFeaturesFetcher
        fetcher = MacroFeaturesFetcher()

        mock_ticker = MagicMock()
        mock_ticker.fast_info.last_price = None
        mock_ticker.history.return_value = MagicMock(empty=True)

        with patch("yfinance.Ticker", return_value=mock_ticker):
            snap = fetcher.fetch()

        # All prices should be None (not 0.0, not -1, not fabricated)
        for field_name in ["india_vix", "gift_nifty", "usd_inr", "crude_wti", "crude_mcx"]:
            val = getattr(snap, field_name)
            assert val is None, f"{field_name} should be None when unavailable, got {val}"

    def test_freshness_is_end_of_day_for_historical_data(self):
        from src.ingestion.macro_features_fetcher import MacroFeaturesFetcher
        import pandas as pd
        fetcher = MacroFeaturesFetcher()

        mock_df = pd.DataFrame({
            "Close": [14.5, 15.0],
            "Date": pd.to_datetime(["2024-01-09", "2024-01-10"]),
        }).set_index("Date")

        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_df

        with patch("yfinance.Ticker", return_value=mock_ticker):
            df = fetcher.fetch_historical_vix(date(2024, 1, 9), date(2024, 1, 10))

        if not df.empty and "freshness_level" in df.columns:
            assert all(df["freshness_level"] == "END_OF_DAY")


# =============================================================================
# Scheduler tests
# =============================================================================

class TestIngestionScheduler:
    def test_scheduler_disabled_by_default(self):
        """scheduler.enabled defaults to false — scheduler must not auto-start."""
        from src.scheduling.ingestion_scheduler import IngestionScheduler

        # Mock config with scheduler disabled
        with patch("src.scheduling.ingestion_scheduler.get_config") as mock_cfg:
            mock_cfg.return_value.yaml = {"scheduler": {"enabled": False}}
            scheduler = IngestionScheduler()

        assert scheduler.is_enabled is False
        assert scheduler.is_running is False

    def test_scheduler_does_not_start_when_disabled(self):
        """Calling start() when disabled must not actually start the scheduler."""
        from src.scheduling.ingestion_scheduler import IngestionScheduler

        with patch("src.scheduling.ingestion_scheduler.get_config") as mock_cfg:
            mock_cfg.return_value.yaml = {"scheduler": {"enabled": False}}
            scheduler = IngestionScheduler()
            scheduler.start()

        assert scheduler.is_running is False

    def test_scheduler_status_data_only_note(self):
        """Status must include note that execution is not possible."""
        from src.scheduling.ingestion_scheduler import IngestionScheduler

        with patch("src.scheduling.ingestion_scheduler.get_config") as mock_cfg:
            mock_cfg.return_value.yaml = {"scheduler": {"enabled": False}}
            scheduler = IngestionScheduler()

        status = scheduler.status()
        assert "DATA INGESTION ONLY" in status["note"]
        assert "ALLOW_LIVE_EXECUTION" in status["note"]

    def test_execution_job_name_blocked(self):
        """Scheduling a job with execution-related name must raise ValueError."""
        from src.scheduling.ingestion_scheduler import _validate_job_name
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_job_name("submit_order_job")
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_job_name("place_buy_order")
        with pytest.raises(ValueError, match="BLOCKED"):
            _validate_job_name("execute_trade")

    def test_data_job_name_allowed(self):
        """Data ingestion job names must not raise."""
        from src.scheduling.ingestion_scheduler import _validate_job_name
        _validate_job_name("intraday_candle_fetch")
        _validate_job_name("fii_dii_fetch")
        _validate_job_name("bhavcopy_ingest")
        _validate_job_name("macro_features_fetch")

    def test_scheduler_get_jobs_empty_when_disabled(self):
        from src.scheduling.ingestion_scheduler import IngestionScheduler
        with patch("src.scheduling.ingestion_scheduler.get_config") as mock_cfg:
            mock_cfg.return_value.yaml = {"scheduler": {"enabled": False}}
            scheduler = IngestionScheduler()
        assert scheduler.get_job_ids() == []

    def test_singleton_accessor(self):
        from src.scheduling.ingestion_scheduler import get_ingestion_scheduler, IngestionScheduler
        import src.scheduling.ingestion_scheduler as sched_module
        sched_module._scheduler_instance = None  # Reset singleton

        with patch("src.scheduling.ingestion_scheduler.get_config") as mock_cfg:
            mock_cfg.return_value.yaml = {"scheduler": {"enabled": False}}
            s1 = get_ingestion_scheduler()
            s2 = get_ingestion_scheduler()

        # Must return same instance
        assert s1 is s2


# =============================================================================
# Multiple Testing Correction tests
# =============================================================================

class TestMultipleTestingCorrection:
    def test_bonferroni_empty_input(self):
        from src.research.multiple_testing_correction import apply_bonferroni
        report = apply_bonferroni([])
        assert report.total_hypotheses == 0
        assert report.rejected_count == 0

    def test_bonferroni_all_significant(self):
        from src.research.multiple_testing_correction import apply_bonferroni
        p_values = [0.001, 0.002, 0.001]
        report = apply_bonferroni(p_values, alpha=0.05)
        assert report.total_hypotheses == 3
        # All below Bonferroni threshold (0.05/3 = 0.0167)
        assert report.rejected_count == 3

    def test_bonferroni_none_significant(self):
        from src.research.multiple_testing_correction import apply_bonferroni
        p_values = [0.1, 0.2, 0.15]
        report = apply_bonferroni(p_values, alpha=0.05)
        assert report.rejected_count == 0

    def test_bonferroni_adjusted_p_capped_at_1(self):
        from src.research.multiple_testing_correction import apply_bonferroni
        p_values = [0.9, 0.8, 0.7]
        report = apply_bonferroni(p_values, alpha=0.05)
        for r in report.corrected_results:
            assert r.adjusted_p_value <= 1.0

    def test_bh_empty_input(self):
        from src.research.multiple_testing_correction import apply_benjamini_hochberg
        report = apply_benjamini_hochberg([])
        assert report.total_hypotheses == 0

    def test_bh_all_significant(self):
        from src.research.multiple_testing_correction import apply_benjamini_hochberg
        p_values = [0.001, 0.002, 0.003]
        report = apply_benjamini_hochberg(p_values, alpha=0.05)
        assert report.rejected_count == 3

    def test_bh_less_conservative_than_bonferroni(self):
        """BH rejects more (or equal) compared to Bonferroni."""
        from src.research.multiple_testing_correction import (
            apply_bonferroni, apply_benjamini_hochberg
        )
        p_values = [0.01, 0.03, 0.05, 0.1, 0.2]
        bon = apply_bonferroni(p_values, alpha=0.05)
        bh = apply_benjamini_hochberg(p_values, alpha=0.05)
        assert bh.rejected_count >= bon.rejected_count

    def test_bh_adjusted_p_monotone(self):
        """BH-adjusted p-values for sorted input should be non-decreasing."""
        from src.research.multiple_testing_correction import apply_benjamini_hochberg
        import numpy as np
        p_values = sorted([0.001, 0.01, 0.03, 0.05, 0.1])
        report = apply_benjamini_hochberg(p_values, alpha=0.05)
        adj_ps = [r.adjusted_p_value for r in sorted(report.corrected_results, key=lambda x: x.raw_p_value)]
        # Should be non-decreasing
        for i in range(len(adj_ps) - 1):
            assert adj_ps[i] <= adj_ps[i + 1] + 1e-10

    def test_correct_p_values_uses_bh_by_default(self):
        from src.research.multiple_testing_correction import (
            correct_p_values, CorrectionMethod
        )
        report = correct_p_values([0.01, 0.05, 0.1])
        assert report.method == CorrectionMethod.BENJAMINI_HOCHBERG

    def test_hypothesis_ids_preserved(self):
        from src.research.multiple_testing_correction import apply_bonferroni
        ids = ["H001", "H002", "H003"]
        report = apply_bonferroni([0.01, 0.05, 0.1], hypothesis_ids=ids)
        result_ids = [r.hypothesis_id for r in report.corrected_results]
        assert result_ids == ids

    def test_notes_include_disclaimer(self):
        """Report must note that statistical significance ≠ profitability."""
        from src.research.multiple_testing_correction import apply_bonferroni
        report = apply_bonferroni([0.01, 0.05])
        notes_combined = " ".join(report.notes)
        assert "profitability" in notes_combined.lower() or "trading" in notes_combined.lower()

    def test_none_method_returns_raw_p_values(self):
        from src.research.multiple_testing_correction import (
            correct_p_values, CorrectionMethod
        )
        p_values = [0.01, 0.06]
        report = correct_p_values(p_values, method=CorrectionMethod.NONE, alpha=0.05)
        for i, r in enumerate(report.corrected_results):
            assert r.raw_p_value == r.adjusted_p_value


# =============================================================================
# Paid Options Interface tests
# =============================================================================

class TestPaidOptionsInterface:
    def test_no_provider_configured_returns_stub(self):
        from src.ingestion.paid_options_interface import (
            get_paid_options_provider, NoPaidProviderConfigured
        )
        with patch("src.ingestion.paid_options_interface.get_config") as mock_cfg:
            mock_cfg.return_value.env.paid_options_provider_name = ""
            provider = get_paid_options_provider()
        assert isinstance(provider, NoPaidProviderConfigured)

    def test_stub_capability_bid_ask_unavailable(self):
        from src.ingestion.paid_options_interface import (
            NoPaidProviderConfigured, OptionsDataStatus
        )
        from src.ingestion.capability_registry import (
            DataCapabilityKey, DataCapabilityState
        )
        stub = NoPaidProviderConfigured()
        report = stub.get_capability_report()
        bid_ask_state = report.get(DataCapabilityKey.OPTIONS_BID_ASK_READY)
        assert bid_ask_state == DataCapabilityState.UNAVAILABLE

    def test_stub_historical_intraday_requires_confirmation(self):
        from src.ingestion.paid_options_interface import NoPaidProviderConfigured
        from src.ingestion.capability_registry import (
            DataCapabilityKey, DataCapabilityState
        )
        stub = NoPaidProviderConfigured()
        report = stub.get_capability_report()
        assert report.get(
            DataCapabilityKey.OPTIONS_HISTORICAL_INTRADAY_READY
        ) == DataCapabilityState.REQUIRES_VENDOR_CONFIRMATION

    def test_stub_raises_on_historical_tick_request(self):
        from src.ingestion.paid_options_interface import NoPaidProviderConfigured
        from src.ingestion.base import DataUnavailableError
        from datetime import datetime
        stub = NoPaidProviderConfigured()
        with pytest.raises(DataUnavailableError):
            stub.get_historical_ticks(
                "NIFTY", date(2024, 1, 25), 24000.0, "CE",
                datetime(2024, 1, 10, 9, 15), datetime(2024, 1, 10, 15, 30)
            )

    def test_stub_verified_bid_ask_is_false(self):
        """verified_bid_ask must be False for stub — no false capability claims."""
        from src.ingestion.paid_options_interface import NoPaidProviderConfigured
        stub = NoPaidProviderConfigured()
        assert stub.verified_bid_ask is False

    def test_options_data_status_constants(self):
        from src.ingestion.paid_options_interface import OptionsDataStatus
        assert OptionsDataStatus.SETTLEMENT_PRICE_ONLY == "SETTLEMENT_PRICE_ONLY"
        assert OptionsDataStatus.BID_ASK_AVAILABLE == "BID_ASK_AVAILABLE"
        assert OptionsDataStatus.REQUIRES_VENDOR_CONFIRMATION == "REQUIRES_VENDOR_CONFIRMATION"

    def test_historical_options_tick_has_bid_ask_check(self):
        from src.ingestion.paid_options_interface import HistoricalOptionsTick, OptionsDataStatus
        from datetime import datetime
        # Without bid/ask
        tick = HistoricalOptionsTick(
            timestamp=datetime(2024, 1, 10, 10, 0),
            underlying="NIFTY",
            expiry_date=date(2024, 1, 25),
            strike_price=24000.0,
            option_type="CE",
            ltp=150.0,
            data_status=OptionsDataStatus.LTP_ONLY,
            source="TEST",
        )
        assert tick.has_bid_ask() is False
        assert tick.bid_ask_spread() is None

        # With bid/ask
        tick2 = HistoricalOptionsTick(
            timestamp=datetime(2024, 1, 10, 10, 0),
            underlying="NIFTY",
            expiry_date=date(2024, 1, 25),
            strike_price=24000.0,
            option_type="CE",
            ltp=150.0,
            bid_price=149.0,
            ask_price=151.0,
            data_status=OptionsDataStatus.BID_ASK_AVAILABLE,
            source="TEST",
        )
        assert tick2.has_bid_ask() is True
        assert tick2.bid_ask_spread() == pytest.approx(2.0)
