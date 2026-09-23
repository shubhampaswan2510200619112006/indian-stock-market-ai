"""
Phase 16 — Upstox Market Data Provider.

IMPORTANT SAFETY CONSTRAINTS:
- This provider is for MARKET DATA ACCESS ONLY.
- It MUST NOT and CANNOT place, modify, or cancel orders.
- It MUST NOT access any trading/execution endpoints.
- ALLOW_LIVE_EXECUTION remains hardcoded False in ExecutionGuard.
- Missing or expired credentials → DataUnavailableError (fail safely).
- This is NOT a fallback that silently substitutes for Kite Connect.
  If Kite does not have required data, the answer is BLOCKED, not "use Upstox silently".
  Callers must explicitly choose which provider they want.

API documentation: https://upstox.com/developer/api-documentation/
"""

from __future__ import annotations

import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from urllib.parse import quote as url_quote

from src.ingestion.base import (
    AuthenticationError,
    DataUnavailableError,
    MarketDataProvider,
    RateLimitError,
)
from src.ingestion.capability_registry import (
    DataCapabilityKey,
    DataCapabilityState,
    ProviderCapabilityReport,
    get_capability_registry,
)
from src.ingestion.schemas import (
    DataFreshnessLevel,
    DataQualityStatus,
    Quote,
)
from src.utils.config import get_config
from src.utils.logging_config import get_logger
from src.utils.time_utils import data_age_seconds, now_ist

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Upstox API v2 constants (market data endpoints only)
# ---------------------------------------------------------------------------
UPSTOX_BASE_URL = "https://api.upstox.com/v2"
UPSTOX_HISTORICAL_URL = f"{UPSTOX_BASE_URL}/historical-candle"
UPSTOX_QUOTE_URL = f"{UPSTOX_BASE_URL}/market-quote/quotes"
UPSTOX_LTP_URL = f"{UPSTOX_BASE_URL}/market-quote/ltp"

# Upstox instrument keys for NSE indices
# Format: "NSE_INDEX|<symbol>"
UPSTOX_INSTRUMENT_KEYS: Dict[str, str] = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
    "SENSEX": "BSE_INDEX|SENSEX",
}

# Interval mapping: our canonical → Upstox API interval strings
UPSTOX_INTERVAL_MAP: Dict[str, str] = {
    "1m": "1minute",
    "3m": "3minute",
    "5m": "5minute",
    "10m": "10minute",
    "15m": "15minute",
    "30m": "30minute",
    "60m": "60minute",
    "1h": "60minute",
    "1d": "day",
    "1w": "week",
    "1mo": "month",
}

# Execution endpoint patterns — BLOCKED
_FORBIDDEN_ENDPOINT_PATTERNS = [
    "/order",
    "/trade",
    "/portfolio/positions",
    "/portfolio/holdings",
    "/user/fund",
    "/charges",
]


def _assert_not_execution_endpoint(url: str) -> None:
    url_lower = url.lower()
    for pattern in _FORBIDDEN_ENDPOINT_PATTERNS:
        if pattern in url_lower:
            raise PermissionError(
                f"BLOCKED: Upstox Provider attempted execution endpoint: {url}. "
                f"This provider is MARKET DATA ONLY."
            )


def _classify_freshness(candle_timestamp: datetime) -> DataFreshnessLevel:
    config = get_config()
    fc = config.data_freshness_config
    age = data_age_seconds(candle_timestamp)
    if age < fc.get("live_threshold", 60):
        return DataFreshnessLevel.LIVE
    elif age < fc.get("delayed_threshold", 300):
        return DataFreshnessLevel.DELAYED
    elif age < fc.get("stale_threshold", 3600):
        return DataFreshnessLevel.STALE
    else:
        return DataFreshnessLevel.END_OF_DAY


class UpstoxSession:
    """Manages Upstox v2 API HTTP session for market-data calls only."""

    def __init__(self) -> None:
        config = get_config()
        self._access_token = config.env.upstox_access_token
        self._rate_limit = config.env.rate_limit_delay_seconds
        self._last_request_time: float = 0.0
        self._session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._access_token}",
            "Api-Version": "2.0",
        }

    def _check_credentials(self) -> None:
        if not self._access_token:
            raise AuthenticationError(
                "Upstox access token not configured. "
                "Set UPSTOX_ACCESS_TOKEN in .env. "
                "Provider status: UNAVAILABLE."
            )

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self._rate_limit:
            time.sleep(self._rate_limit - elapsed)
        self._last_request_time = time.monotonic()

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        retries: int = 2,
    ) -> Any:
        """GET to Upstox market-data endpoint; blocks execution endpoints."""
        _assert_not_execution_endpoint(url)
        self._check_credentials()
        self._throttle()

        for attempt in range(retries + 1):
            try:
                resp = self._session.get(
                    url,
                    headers=self._headers(),
                    params=params,
                    timeout=15,
                )
                if resp.status_code == 401:
                    raise AuthenticationError(
                        "Upstox access token invalid or expired. "
                        "Re-authenticate and update UPSTOX_ACCESS_TOKEN."
                    )
                if resp.status_code == 429:
                    raise RateLimitError("Upstox rate limit hit.")
                if resp.status_code == 200:
                    return resp.json()
                resp.raise_for_status()

            except (AuthenticationError, RateLimitError, PermissionError):
                raise
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
                logger.warning(f"Upstox attempt {attempt + 1} failed: {exc}")
                if attempt == retries:
                    raise DataUnavailableError(f"Cannot reach Upstox after {retries + 1} attempts: {exc}")
                time.sleep(2 ** (attempt + 1))
            except requests.exceptions.HTTPError as exc:
                raise DataUnavailableError(f"Upstox HTTP error: {exc}")
            except ValueError as exc:
                raise DataUnavailableError(f"Invalid JSON from Upstox: {exc}")

        raise DataUnavailableError("Upstox request failed after all retries")


class UpstoxProvider(MarketDataProvider):
    """
    Upstox v2 market data provider.

    Capabilities:
    - Minute-level OHLCV for NIFTY, BANKNIFTY, FINNIFTY (when token is valid)
    - Daily OHLCV
    - Live LTP

    NOT a silent fallback for Kite. Callers must explicitly pick this provider.
    Capability state is assessed on __init__ and recorded in the registry.
    """

    def __init__(self) -> None:
        self._session = UpstoxSession()
        self._capability_report = self._assess_capabilities()
        get_capability_registry().register(self._capability_report)

    @property
    def provider_name(self) -> str:
        return "upstox"

    def _assess_capabilities(self) -> ProviderCapabilityReport:
        config = get_config()
        has_token = bool(config.env.upstox_access_token)

        report = ProviderCapabilityReport(
            provider_name="upstox",
            provider_type="BROKER_API",
            credentials_present=has_token,
            credentials_valid=False,
            reachable=False,
        )

        no_creds_state = DataCapabilityState.UNAVAILABLE
        no_creds_note = "UPSTOX_ACCESS_TOKEN not configured in .env"

        if not has_token:
            for key in [
                DataCapabilityKey.INTRADAY_1M_READY,
                DataCapabilityKey.INTRADAY_5M_READY,
                DataCapabilityKey.INTRADAY_15M_READY,
                DataCapabilityKey.DAILY_OHLCV_READY,
                DataCapabilityKey.OPTIONS_LTP_READY,
            ]:
                report.set(key, no_creds_state, note=no_creds_note)
            report.notes.append(no_creds_note)
        else:
            # Try lightweight probe
            try:
                probe = requests.get(
                    f"{UPSTOX_BASE_URL}/market-quote/ltp",
                    headers=self._session._headers(),
                    params={"instrument_key": "NSE_INDEX|Nifty 50"},
                    timeout=5,
                )
                _assert_not_execution_endpoint(probe.url)
                if probe.status_code == 200:
                    report.reachable = True
                    report.credentials_valid = True
                    for key in [
                        DataCapabilityKey.INTRADAY_1M_READY,
                        DataCapabilityKey.INTRADAY_5M_READY,
                        DataCapabilityKey.INTRADAY_15M_READY,
                        DataCapabilityKey.DAILY_OHLCV_READY,
                        DataCapabilityKey.OPTIONS_LTP_READY,
                    ]:
                        report.set(key, DataCapabilityState.READY,
                                   note="Verified via Upstox LTP probe (200 OK)")
                elif probe.status_code in (401, 403):
                    report.reachable = True
                    for key in [
                        DataCapabilityKey.INTRADAY_1M_READY,
                        DataCapabilityKey.DAILY_OHLCV_READY,
                    ]:
                        report.set(key, DataCapabilityState.BLOCKED,
                                   note="Upstox 401/403 — token may have expired")
                else:
                    for key in [
                        DataCapabilityKey.INTRADAY_1M_READY,
                        DataCapabilityKey.DAILY_OHLCV_READY,
                    ]:
                        report.set(key, DataCapabilityState.UNAVAILABLE,
                                   note=f"Upstox probe returned HTTP {probe.status_code}")
            except PermissionError:
                raise
            except Exception as exc:
                logger.warning(f"Upstox capability check failed: {exc}")
                for key in [
                    DataCapabilityKey.INTRADAY_1M_READY,
                    DataCapabilityKey.DAILY_OHLCV_READY,
                ]:
                    report.set(key, DataCapabilityState.UNAVAILABLE, note=str(exc))

        # Options bid/ask and execution: explicit statements
        report.set(
            DataCapabilityKey.OPTIONS_BID_ASK_READY,
            DataCapabilityState.REQUIRES_VENDOR_CONFIRMATION,
            note="Upstox provides real-time market depth; historical bid/ask archive unverified",
        )
        report.set(
            DataCapabilityKey.OPTIONS_EXECUTION_READY,
            DataCapabilityState.NOT_SUPPORTED,
            note="BLOCKED: market data provider only; execution hardcoded disabled",
        )
        report.set(DataCapabilityKey.PROVENANCE_READY, DataCapabilityState.READY,
                   note="All candles carry source='upstox' and candle_timestamp")
        return report

    @property
    def capability_report(self) -> ProviderCapabilityReport:
        return self._capability_report

    def get_quote(self, symbol: str) -> Quote:
        """Get current LTP for an index from Upstox."""
        instrument_key = UPSTOX_INSTRUMENT_KEYS.get(symbol.upper())
        if instrument_key is None:
            raise DataUnavailableError(
                f"UpstoxProvider: symbol '{symbol}' not in instrument key map. "
                f"Supported: {list(UPSTOX_INSTRUMENT_KEYS.keys())}"
            )

        data = self._session.get(UPSTOX_LTP_URL, params={"instrument_key": instrument_key})
        quote_data = (data.get("data", {}) or {}).get(instrument_key, {})
        if not quote_data:
            raise DataUnavailableError(f"Upstox: no LTP data for {symbol}")

        ltp = quote_data.get("last_price")
        if ltp is None:
            raise DataUnavailableError(f"Upstox LTP for {symbol} missing last_price")

        return Quote(
            symbol=symbol.upper(),
            last_price=float(ltp),
            timestamp=now_ist(),
            source=self.provider_name,
            data_quality=DataQualityStatus.GOOD,
        )

    def get_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV candles from Upstox.

        Returns DataFrame with columns:
            date, open, high, low, close, volume, timeframe, freshness_level, source
        """
        instrument_key = UPSTOX_INSTRUMENT_KEYS.get(symbol.upper())
        if instrument_key is None:
            raise DataUnavailableError(
                f"UpstoxProvider: '{symbol}' not supported. "
                f"Supported: {list(UPSTOX_INSTRUMENT_KEYS.keys())}"
            )

        upstox_interval = UPSTOX_INTERVAL_MAP.get(interval)
        if upstox_interval is None:
            raise DataUnavailableError(
                f"UpstoxProvider: interval '{interval}' not supported. "
                f"Supported: {list(UPSTOX_INTERVAL_MAP.keys())}"
            )

        # Upstox historical URL: /historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
        url = f"{UPSTOX_HISTORICAL_URL}/{url_quote(instrument_key, safe='')}/{upstox_interval}/{end.isoformat()}/{start.isoformat()}"

        try:
            response = self._session.get(url)
        except (AuthenticationError, DataUnavailableError):
            raise

        candles = (response.get("data", {}) or {}).get("candles", [])
        if not candles:
            logger.warning(f"UpstoxProvider: no candles for {symbol} {interval} {start}–{end}")
            return pd.DataFrame(
                columns=["date", "open", "high", "low", "close", "volume", "timeframe", "freshness_level", "source"]
            )

        rows = []
        for c in candles:
            if len(c) < 6:
                continue
            try:
                ts = pd.to_datetime(c[0])
                freshness = _classify_freshness(ts.to_pydatetime())
                rows.append({
                    "date": ts,
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": int(c[5]),
                    "timeframe": interval,
                    "freshness_level": freshness.value,
                    "source": self.provider_name,
                })
            except (ValueError, TypeError, IndexError) as exc:
                logger.warning(f"UpstoxProvider: malformed candle skipped: {c!r} — {exc}")
                continue

        if not rows:
            return pd.DataFrame(
                columns=["date", "open", "high", "low", "close", "volume", "timeframe", "freshness_level", "source"]
            )

        df = pd.DataFrame(rows)
        df = df.sort_values("date").reset_index(drop=True)
        return df

    def health_check(self) -> bool:
        return self._capability_report.credentials_valid and self._capability_report.reachable
