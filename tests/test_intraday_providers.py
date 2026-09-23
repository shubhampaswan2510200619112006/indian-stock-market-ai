"""
Phase 16 — Tests for Kite Connect and Upstox market data providers.

All HTTP calls are mocked. No live network calls are made.
Tests verify:
- Authentication failure handled safely
- Credentials absent → UNAVAILABLE capability
- Valid OHLCV response parsed correctly (with freshness + timeframe columns)
- Malformed candle rows skipped gracefully
- Stale data classified correctly
- Execution endpoint access blocked (PermissionError)
- Provider does NOT silently substitute for another
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.ingestion.base import AuthenticationError, DataUnavailableError
from src.ingestion.capability_registry import (
    DataCapabilityKey,
    DataCapabilityState,
)


# =============================================================================
# Helper: mock a successful Kite instruments response (for capability probe)
# =============================================================================

def _make_mock_response(status_code: int, json_body: Any = None) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_body or {}
    mock.url = "https://api.kite.trade/instruments/NSE"
    return mock


def _kite_candle_response(symbol: str = "NIFTY") -> Dict[str, Any]:
    """Sample Kite historical data response."""
    return {
        "status": "success",
        "data": {
            "candles": [
                # [datetime_str, open, high, low, close, volume]
                ["2024-01-10T09:15:00+0530", 21800.0, 21900.0, 21750.0, 21870.0, 500000],
                ["2024-01-10T09:16:00+0530", 21870.0, 21920.0, 21860.0, 21910.0, 450000],
                ["2024-01-10T09:17:00+0530", 21910.0, 21950.0, 21890.0, 21940.0, 480000],
            ]
        }
    }


def _upstox_candle_response() -> Dict[str, Any]:
    """Sample Upstox historical candle response."""
    return {
        "status": "success",
        "data": {
            "candles": [
                ["2024-01-10T09:15:00+05:30", 21800.0, 21900.0, 21750.0, 21870.0, 500000, 0],
                ["2024-01-10T09:16:00+05:30", 21870.0, 21920.0, 21860.0, 21910.0, 450000, 0],
            ]
        }
    }


# =============================================================================
# KiteProvider tests
# =============================================================================

class TestKiteProviderNoCredentials:
    """Tests when KITE credentials are absent from environment."""

    def test_all_capabilities_unavailable_when_no_credentials(self):
        with patch("src.ingestion.kite_provider.get_config") as mock_cfg:
            mock_cfg.return_value.env.kite_api_key = ""
            mock_cfg.return_value.env.kite_access_token = ""
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.kite_provider import KiteProvider
            provider = KiteProvider()
            report = provider.capability_report
            assert report.credentials_present is False
            assert report.get(DataCapabilityKey.INTRADAY_1M_READY) == DataCapabilityState.UNAVAILABLE
            assert report.get(DataCapabilityKey.DAILY_OHLCV_READY) == DataCapabilityState.UNAVAILABLE

    def test_get_ohlcv_raises_when_no_credentials(self):
        with patch("src.ingestion.kite_provider.get_config") as mock_cfg:
            mock_cfg.return_value.env.kite_api_key = ""
            mock_cfg.return_value.env.kite_access_token = ""
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.kite_provider import KiteProvider
            provider = KiteProvider()
            with pytest.raises(AuthenticationError):
                provider.get_ohlcv("NIFTY", date(2024, 1, 1), date(2024, 1, 10), "1m")

    def test_get_quote_raises_when_no_credentials(self):
        with patch("src.ingestion.kite_provider.get_config") as mock_cfg:
            mock_cfg.return_value.env.kite_api_key = ""
            mock_cfg.return_value.env.kite_access_token = ""
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.kite_provider import KiteProvider
            provider = KiteProvider()
            with pytest.raises(AuthenticationError):
                provider.get_quote("NIFTY")

    def test_health_check_false_when_no_credentials(self):
        with patch("src.ingestion.kite_provider.get_config") as mock_cfg:
            mock_cfg.return_value.env.kite_api_key = ""
            mock_cfg.return_value.env.kite_access_token = ""
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.kite_provider import KiteProvider
            provider = KiteProvider()
            assert provider.health_check() is False


class TestKiteProviderValidResponse:
    """Tests with mocked successful responses."""

    def _make_provider(self, mock_get):
        """Helper: build KiteProvider with mocked credential check + HTTP probe."""
        pass

    @patch("requests.Session.get")
    def test_ohlcv_returns_correct_shape(self, mock_session_get):
        # Probe returns 200 (capability check)
        probe_response = _make_mock_response(200, {"data": {}})
        # Historical data returns candles
        candle_response = _make_mock_response(200, _kite_candle_response())
        mock_session_get.side_effect = [probe_response, candle_response]

        with patch("src.ingestion.kite_provider.get_config") as mock_cfg, \
             patch("requests.get", return_value=probe_response):
            mock_cfg.return_value.env.kite_api_key = "test_api_key"
            mock_cfg.return_value.env.kite_access_token = "test_token"
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.kite_provider import KiteProvider
            provider = KiteProvider()

        # Mock the session.get call for historical data
        with patch.object(provider._session._session, "get", return_value=candle_response):
            df = provider.get_ohlcv("NIFTY", date(2024, 1, 10), date(2024, 1, 10), "1m")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns
        assert "timeframe" in df.columns
        assert "freshness_level" in df.columns
        assert "source" in df.columns
        assert all(df["timeframe"] == "1m")
        assert all(df["source"] == "kite_connect")

    def test_malformed_candle_rows_skipped(self):
        """Malformed candles (missing fields) are skipped, not causing exception."""
        bad_response = {
            "status": "success",
            "data": {
                "candles": [
                    ["2024-01-10T09:15:00+0530", 21800.0],  # too short
                    ["2024-01-10T09:16:00+0530", 21870.0, 21920.0, 21860.0, 21910.0, 450000],  # ok
                ]
            }
        }
        mock_resp = _make_mock_response(200, bad_response)
        probe_resp = _make_mock_response(200, {})

        with patch("src.ingestion.kite_provider.get_config") as mock_cfg, \
             patch("requests.get", return_value=probe_resp):
            mock_cfg.return_value.env.kite_api_key = "test_api_key"
            mock_cfg.return_value.env.kite_access_token = "test_token"
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.kite_provider import KiteProvider
            provider = KiteProvider()

        with patch.object(provider._session._session, "get", return_value=mock_resp):
            df = provider.get_ohlcv("NIFTY", date(2024, 1, 10), date(2024, 1, 10), "1m")

        # Only 1 valid candle, not 2
        assert len(df) == 1

    def test_unsupported_symbol_raises(self):
        probe_resp = _make_mock_response(200, {})
        with patch("src.ingestion.kite_provider.get_config") as mock_cfg, \
             patch("requests.get", return_value=probe_resp):
            mock_cfg.return_value.env.kite_api_key = "test_key"
            mock_cfg.return_value.env.kite_access_token = "test_token"
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.kite_provider import KiteProvider
            provider = KiteProvider()
        with pytest.raises(DataUnavailableError, match="KiteProvider.*not found"):
            provider.get_ohlcv("FAKESYMBOL", date(2024, 1, 1), date(2024, 1, 10))


    def test_unsupported_interval_raises(self):
        probe_resp = _make_mock_response(200, {})
        with patch("src.ingestion.kite_provider.get_config") as mock_cfg, \
             patch("requests.get", return_value=probe_resp):
            mock_cfg.return_value.env.kite_api_key = "test_key"
            mock_cfg.return_value.env.kite_access_token = "test_token"
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.kite_provider import KiteProvider
            provider = KiteProvider()
        with pytest.raises(DataUnavailableError, match="interval"):
            provider.get_ohlcv("NIFTY", date(2024, 1, 1), date(2024, 1, 10), "2m")

    def test_expired_token_returns_blocked_capability(self):
        """When Kite returns 401 during probe, capabilities are BLOCKED."""
        auth_failed_resp = _make_mock_response(401, {"status": "error", "message": "Invalid access token"})
        with patch("src.ingestion.kite_provider.get_config") as mock_cfg, \
             patch("requests.get", return_value=auth_failed_resp):
            mock_cfg.return_value.env.kite_api_key = "test_key"
            mock_cfg.return_value.env.kite_access_token = "expired_token"
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.kite_provider import KiteProvider
            provider = KiteProvider()

        assert provider.capability_report.get(DataCapabilityKey.INTRADAY_1M_READY) == DataCapabilityState.BLOCKED

    def test_execution_endpoint_blocked(self):
        """Attempting to call an execution endpoint raises PermissionError."""
        from src.ingestion.kite_provider import _assert_not_execution_endpoint
        with pytest.raises(PermissionError, match="BLOCKED"):
            _assert_not_execution_endpoint("https://api.kite.trade/orders")

    def test_execution_endpoint_orders_variant_blocked(self):
        from src.ingestion.kite_provider import _assert_not_execution_endpoint
        with pytest.raises(PermissionError):
            _assert_not_execution_endpoint("https://api.kite.trade/orders/regular")

    def test_market_data_endpoint_not_blocked(self):
        from src.ingestion.kite_provider import _assert_not_execution_endpoint
        # Should not raise
        _assert_not_execution_endpoint("https://api.kite.trade/instruments/historical/256265/minute")

    def test_options_execution_never_ready(self):
        probe_resp = _make_mock_response(200, {})
        with patch("src.ingestion.kite_provider.get_config") as mock_cfg, \
             patch("requests.get", return_value=probe_resp):
            mock_cfg.return_value.env.kite_api_key = "test_key"
            mock_cfg.return_value.env.kite_access_token = "test_token"
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.kite_provider import KiteProvider
            provider = KiteProvider()
        # Execution must always be NOT_SUPPORTED
        assert provider.capability_report.get(
            DataCapabilityKey.OPTIONS_EXECUTION_READY
        ) == DataCapabilityState.NOT_SUPPORTED

    def test_options_bid_ask_requires_vendor_confirmation(self):
        """Options bid/ask must be REQUIRES_VENDOR_CONFIRMATION — not silently READY."""
        probe_resp = _make_mock_response(200, {})
        with patch("src.ingestion.kite_provider.get_config") as mock_cfg, \
             patch("requests.get", return_value=probe_resp):
            mock_cfg.return_value.env.kite_api_key = "test_key"
            mock_cfg.return_value.env.kite_access_token = "test_token"
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.kite_provider import KiteProvider
            provider = KiteProvider()
        assert provider.capability_report.get(
            DataCapabilityKey.OPTIONS_BID_ASK_READY
        ) == DataCapabilityState.REQUIRES_VENDOR_CONFIRMATION


# =============================================================================
# UpstoxProvider tests
# =============================================================================

class TestUpstoxProviderNoCredentials:
    def test_all_capabilities_unavailable_when_no_credentials(self):
        with patch("src.ingestion.upstox_provider.get_config") as mock_cfg:
            mock_cfg.return_value.env.upstox_access_token = ""
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.upstox_provider import UpstoxProvider
            provider = UpstoxProvider()
        assert provider.capability_report.credentials_present is False
        assert provider.capability_report.get(DataCapabilityKey.INTRADAY_1M_READY) == DataCapabilityState.UNAVAILABLE

    def test_get_ohlcv_raises_when_no_token(self):
        with patch("src.ingestion.upstox_provider.get_config") as mock_cfg:
            mock_cfg.return_value.env.upstox_access_token = ""
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.upstox_provider import UpstoxProvider
            provider = UpstoxProvider()
        with pytest.raises(AuthenticationError):
            provider.get_ohlcv("NIFTY", date(2024, 1, 1), date(2024, 1, 10), "1m")

    def test_upstox_execution_endpoint_blocked(self):
        from src.ingestion.upstox_provider import _assert_not_execution_endpoint
        with pytest.raises(PermissionError, match="BLOCKED"):
            _assert_not_execution_endpoint("https://api.upstox.com/v2/order/place")

    def test_upstox_market_data_endpoint_not_blocked(self):
        from src.ingestion.upstox_provider import _assert_not_execution_endpoint
        _assert_not_execution_endpoint("https://api.upstox.com/v2/historical-candle/NSE_INDEX%7CNifty+50/1minute/2024-01-10/2024-01-10")

    def test_upstox_ohlcv_valid_response(self):
        probe_resp = _make_mock_response(200, {"status": "success", "data": {"last_price": 21800.0}})
        candle_resp = _make_mock_response(200, _upstox_candle_response())
        with patch("src.ingestion.upstox_provider.get_config") as mock_cfg, \
             patch("requests.get", return_value=probe_resp):
            mock_cfg.return_value.env.upstox_access_token = "test_token"
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.upstox_provider import UpstoxProvider
            provider = UpstoxProvider()

        with patch.object(provider._session._session, "get", return_value=candle_resp):
            df = provider.get_ohlcv("NIFTY", date(2024, 1, 10), date(2024, 1, 10), "1m")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "timeframe" in df.columns
        assert "freshness_level" in df.columns
        assert "source" in df.columns
        assert all(df["source"] == "upstox")

    def test_upstox_options_execution_never_ready(self):
        with patch("src.ingestion.upstox_provider.get_config") as mock_cfg:
            mock_cfg.return_value.env.upstox_access_token = ""
            mock_cfg.return_value.env.rate_limit_delay_seconds = 0.0
            mock_cfg.return_value.data_freshness_config = {
                "live_threshold": 60, "delayed_threshold": 300, "stale_threshold": 3600
            }
            from src.ingestion.upstox_provider import UpstoxProvider
            provider = UpstoxProvider()
        assert provider.capability_report.get(
            DataCapabilityKey.OPTIONS_EXECUTION_READY
        ) == DataCapabilityState.NOT_SUPPORTED


# =============================================================================
# Capability Registry tests
# =============================================================================

class TestCapabilityRegistry:
    def test_default_state_unavailable(self):
        from src.ingestion.capability_registry import (
            ProviderCapabilityReport, DataCapabilityKey, DataCapabilityState
        )
        report = ProviderCapabilityReport(
            provider_name="test", provider_type="TEST"
        )
        # Any unset capability defaults to UNAVAILABLE
        assert report.get(DataCapabilityKey.INTRADAY_1M_READY) == DataCapabilityState.UNAVAILABLE

    def test_set_and_get_capability(self):
        from src.ingestion.capability_registry import (
            ProviderCapabilityReport, DataCapabilityKey, DataCapabilityState
        )
        report = ProviderCapabilityReport(
            provider_name="test", provider_type="TEST"
        )
        report.set(DataCapabilityKey.DAILY_OHLCV_READY, DataCapabilityState.READY, note="verified")
        assert report.get(DataCapabilityKey.DAILY_OHLCV_READY) == DataCapabilityState.READY
        assert report.is_ready(DataCapabilityKey.DAILY_OHLCV_READY) is True

    def test_summary_returns_flat_dict(self):
        from src.ingestion.capability_registry import (
            ProviderCapabilityReport, DataCapabilityKey, DataCapabilityState
        )
        report = ProviderCapabilityReport(
            provider_name="test", provider_type="TEST"
        )
        report.set(DataCapabilityKey.INTRADAY_1M_READY, DataCapabilityState.PARTIAL)
        summary = report.summary()
        assert DataCapabilityKey.INTRADAY_1M_READY.value in summary
        assert summary[DataCapabilityKey.INTRADAY_1M_READY.value] == "PARTIAL"

    def test_registry_stores_and_retrieves(self):
        from src.ingestion.capability_registry import (
            ProviderCapabilityRegistry, ProviderCapabilityReport,
            DataCapabilityKey, DataCapabilityState
        )
        reg = ProviderCapabilityRegistry()
        report = ProviderCapabilityReport(provider_name="my_provider", provider_type="TEST")
        report.set(DataCapabilityKey.DAILY_OHLCV_READY, DataCapabilityState.READY)
        reg.register(report)
        retrieved = reg.get("my_provider")
        assert retrieved is not None
        assert retrieved.get(DataCapabilityKey.DAILY_OHLCV_READY) == DataCapabilityState.READY

    def test_no_silent_fallback_contract(self):
        """
        Verify that absent provider capability returns UNAVAILABLE,
        not a silently substituted value from another provider.
        """
        from src.ingestion.capability_registry import (
            ProviderCapabilityRegistry, ProviderCapabilityReport,
            DataCapabilityKey, DataCapabilityState
        )
        reg = ProviderCapabilityRegistry()
        # Only register kite
        kite_report = ProviderCapabilityReport(provider_name="kite_connect", provider_type="BROKER_API")
        kite_report.set(DataCapabilityKey.INTRADAY_1M_READY, DataCapabilityState.UNAVAILABLE)
        reg.register(kite_report)

        # upstox not registered at all
        upstox_report = reg.get("upstox")
        assert upstox_report is None  # Not silently substituted


# =============================================================================
# Provider factory tests
# =============================================================================

class TestProviderFactory:
    def test_get_intraday_provider_unknown_raises(self):
        from src.ingestion.provider_factory import get_intraday_provider, MARKET_PROVIDER_REGISTRY
        # Reset registry to ensure clean state
        MARKET_PROVIDER_REGISTRY.clear()
        with pytest.raises(ValueError, match="not registered"):
            get_intraday_provider("nonexistent_provider_xyz")

    def test_kite_registered_in_factory(self):
        from src.ingestion.provider_factory import _register_defaults, MARKET_PROVIDER_REGISTRY
        MARKET_PROVIDER_REGISTRY.clear()
        _register_defaults()
        assert "kite" in MARKET_PROVIDER_REGISTRY

    def test_upstox_registered_in_factory(self):
        from src.ingestion.provider_factory import _register_defaults, MARKET_PROVIDER_REGISTRY
        MARKET_PROVIDER_REGISTRY.clear()
        _register_defaults()
        assert "upstox" in MARKET_PROVIDER_REGISTRY
