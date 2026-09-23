"""
Phase 16 — Zerodha Kite Connect Market Data Provider.

IMPORTANT SAFETY CONSTRAINTS:
- This provider is for MARKET DATA ACCESS ONLY.
- It MUST NOT and CANNOT place, modify, or cancel orders.
- It MUST NOT access any trading/execution endpoints.
- ALLOW_LIVE_EXECUTION remains hardcoded False in ExecutionGuard.
- Missing or expired credentials → DataUnavailableError (fail safely).
- If the access token is absent or invalid, the provider reports
  DataCapabilityState.UNAVAILABLE for all capabilities; it does NOT silently
  fall back to another provider.

API documentation: https://kite.trade/docs/connect/v3/
Credentials are loaded exclusively from environment variables / .env file.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

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
# Kite Connect API constants (market data endpoints only)
# ---------------------------------------------------------------------------
KITE_BASE_URL = "https://api.kite.trade"
KITE_HISTORICAL_URL = f"{KITE_BASE_URL}/instruments/historical"
KITE_QUOTE_URL = f"{KITE_BASE_URL}/quote"
KITE_INSTRUMENTS_URL = f"{KITE_BASE_URL}/instruments"

# Instrument tokens for NSE indices (Zerodha Kite internal IDs)
# These are well-known Kite instrument tokens for the major NSE indices.
KITE_INSTRUMENT_TOKENS: Dict[str, int] = {
    "NIFTY": 256265,       # NSE:NIFTY 50
    "BANKNIFTY": 260105,   # NSE:NIFTY BANK
    "FINNIFTY": 257801,    # NSE:NIFTY FIN SERVICE
    "SENSEX": 265,         # BSE:SENSEX
}

# Interval mapping: our canonical intervals → Kite API interval strings
KITE_INTERVAL_MAP: Dict[str, str] = {
    "1m": "minute",
    "3m": "3minute",
    "5m": "5minute",
    "10m": "10minute",
    "15m": "15minute",
    "30m": "30minute",
    "60m": "60minute",
    "1h": "60minute",
    "1d": "day",
}

# Execution endpoint patterns — BLOCKED: never call these
_FORBIDDEN_ENDPOINT_PATTERNS = [
    "/orders",
    "/gtt",
    "/portfolio",
    "/margins",
    "/trades",
]


def _assert_not_execution_endpoint(url: str) -> None:
    """
    Safety guard: raise immediately if any execution endpoint is requested.
    This is belt-and-suspenders protection in addition to ExecutionGuard.
    """
    url_lower = url.lower()
    for pattern in _FORBIDDEN_ENDPOINT_PATTERNS:
        if pattern in url_lower:
            raise PermissionError(
                f"BLOCKED: Kite Provider attempted to call execution endpoint: {url}. "
                f"This provider is for MARKET DATA ONLY. "
                f"ALLOW_LIVE_EXECUTION is hardcoded False."
            )


def _classify_freshness(candle_timestamp: datetime) -> DataFreshnessLevel:
    """Classify a candle's freshness based on its age."""
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


class KiteSession:
    """
    Manages a Kite Connect HTTP session for market-data calls.

    - Reads api_key and access_token from environment (never hardcoded).
    - Raises AuthenticationError if credentials are absent or rejected.
    - Raises DataUnavailableError on network failure.
    - NEVER calls any execution endpoint.
    """

    def __init__(self) -> None:
        config = get_config()
        self._api_key = config.env.kite_api_key
        self._access_token = config.env.kite_access_token
        self._rate_limit = config.env.rate_limit_delay_seconds
        self._last_request_time: float = 0.0
        self._session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        return {
            "X-Kite-Version": "3",
            "Authorization": f"token {self._api_key}:{self._access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _check_credentials(self) -> None:
        if not self._api_key or not self._access_token:
            raise AuthenticationError(
                "Kite Connect credentials not configured. "
                "Set KITE_API_KEY and KITE_ACCESS_TOKEN in .env. "
                "Access token must be refreshed daily via OAuth. "
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
        """
        Make a GET request to a Kite MARKET DATA endpoint.
        Blocks all execution endpoints at the network layer.
        """
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

                if resp.status_code == 403:
                    raise AuthenticationError(
                        "Kite Connect access token invalid or expired. "
                        "Re-authenticate and set KITE_ACCESS_TOKEN in .env."
                    )
                if resp.status_code == 429:
                    raise RateLimitError("Kite Connect rate limit hit. Increase RATE_LIMIT_DELAY_SECONDS.")
                if resp.status_code == 200:
                    return resp.json()

                resp.raise_for_status()

            except (AuthenticationError, RateLimitError, PermissionError):
                raise
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                logger.warning(f"Kite request attempt {attempt + 1} failed: {e}")
                if attempt == retries:
                    raise DataUnavailableError(
                        f"Cannot reach Kite Connect after {retries + 1} attempts: {e}"
                    )
                time.sleep(2 ** (attempt + 1))
            except requests.exceptions.HTTPError as e:
                raise DataUnavailableError(f"Kite HTTP error: {e}")
            except ValueError as e:
                raise DataUnavailableError(f"Invalid JSON from Kite: {e}")

        raise DataUnavailableError("Kite request failed after all retries")


class KiteProvider(MarketDataProvider):
    """
    Zerodha Kite Connect market data provider.

    Capabilities:
    - Minute-level OHLCV for NIFTY, BANKNIFTY, FINNIFTY (when token is valid)
    - Daily OHLCV
    - Live quotes (index level)

    NOT provided (never in scope):
    - Order placement, modification, or cancellation
    - Access to trading endpoints
    - Options chain with bid/ask (options LTP only via separate Kite endpoint)

    Capability state is assessed on __init__ and recorded in the registry.
    """

    def __init__(self) -> None:
        self._session = KiteSession()
        self._capability_report = self._assess_capabilities()
        get_capability_registry().register(self._capability_report)

    @property
    def provider_name(self) -> str:
        return "kite_connect"

    def _assess_capabilities(self) -> ProviderCapabilityReport:
        """
        Assess what this provider can actually supply right now.
        Does NOT assume READY — checks credentials and reachability.
        """
        config = get_config()
        has_key = bool(config.env.kite_api_key)
        has_token = bool(config.env.kite_access_token)

        report = ProviderCapabilityReport(
            provider_name="kite_connect",
            provider_type="BROKER_API",
            credentials_present=has_key and has_token,
            credentials_valid=False,
            reachable=False,
        )

        if not (has_key and has_token):
            for key in [
                DataCapabilityKey.INTRADAY_1M_READY,
                DataCapabilityKey.INTRADAY_5M_READY,
                DataCapabilityKey.INTRADAY_15M_READY,
                DataCapabilityKey.DAILY_OHLCV_READY,
                DataCapabilityKey.OPTIONS_LTP_READY,
            ]:
                report.set(
                    key,
                    DataCapabilityState.UNAVAILABLE,
                    note="KITE_API_KEY or KITE_ACCESS_TOKEN not configured in .env",
                )
            report.notes.append(
                "No credentials: set KITE_API_KEY and KITE_ACCESS_TOKEN in .env "
                "(access token refreshes daily via OAuth)"
            )
            # Options bid/ask: explicitly not supported via standard Kite API
            report.set(
                DataCapabilityKey.OPTIONS_BID_ASK_READY,
                DataCapabilityState.REQUIRES_VENDOR_CONFIRMATION,
                note="Kite Connect provides order book depth; historical bid/ask availability unverified.",
            )
            report.set(
                DataCapabilityKey.OPTIONS_EXECUTION_READY,
                DataCapabilityState.NOT_SUPPORTED,
                note="BLOCKED: This provider is for market data only. Execution is hardcoded disabled.",
            )
            return report

        # Credentials present — try a lightweight reachability check
        try:
            test_resp = requests.get(
                f"{KITE_BASE_URL}/instruments/NSE",
                headers=self._session._headers(),
                timeout=5,
            )
            _assert_not_execution_endpoint(f"{KITE_BASE_URL}/instruments/NSE")
            if test_resp.status_code == 200:
                report.reachable = True
                report.credentials_valid = True
                for key in [
                    DataCapabilityKey.INTRADAY_1M_READY,
                    DataCapabilityKey.INTRADAY_5M_READY,
                    DataCapabilityKey.INTRADAY_15M_READY,
                    DataCapabilityKey.DAILY_OHLCV_READY,
                ]:
                    report.set(key, DataCapabilityState.READY,
                               note="Credentials verified; Kite Connect responded 200")
                report.set(
                    DataCapabilityKey.OPTIONS_LTP_READY,
                    DataCapabilityState.READY,
                    note="LTP available via Kite quote endpoint",
                )
                report.set(
                    DataCapabilityKey.OPTIONS_BID_ASK_READY,
                    DataCapabilityState.REQUIRES_VENDOR_CONFIRMATION,
                    note="Kite provides full market depth; historical bid/ask archive unverified",
                )
            elif test_resp.status_code in (401, 403):
                report.reachable = True
                report.credentials_valid = False
                for key in [
                    DataCapabilityKey.INTRADAY_1M_READY,
                    DataCapabilityKey.INTRADAY_5M_READY,
                    DataCapabilityKey.DAILY_OHLCV_READY,
                ]:
                    report.set(key, DataCapabilityState.BLOCKED,
                               note="Kite returned 401/403 — access token may have expired")
            else:
                for key in [
                    DataCapabilityKey.INTRADAY_1M_READY,
                    DataCapabilityKey.INTRADAY_5M_READY,
                    DataCapabilityKey.DAILY_OHLCV_READY,
                ]:
                    report.set(key, DataCapabilityState.UNAVAILABLE,
                               note=f"Kite returned HTTP {test_resp.status_code}")
        except PermissionError:
            raise
        except Exception as exc:
            logger.warning(f"KiteProvider capability assessment failed: {exc}")
            for key in [
                DataCapabilityKey.INTRADAY_1M_READY,
                DataCapabilityKey.INTRADAY_5M_READY,
                DataCapabilityKey.DAILY_OHLCV_READY,
            ]:
                report.set(key, DataCapabilityState.UNAVAILABLE,
                           note=f"Reachability check failed: {exc}")

        report.set(
            DataCapabilityKey.OPTIONS_EXECUTION_READY,
            DataCapabilityState.NOT_SUPPORTED,
            note="BLOCKED: market data provider only; execution hardcoded disabled",
        )
        report.set(DataCapabilityKey.PROVENANCE_READY, DataCapabilityState.READY,
                   note="All candles carry source='kite_connect' and candle_timestamp")
        return report

    @property
    def capability_report(self) -> ProviderCapabilityReport:
        return self._capability_report

    # -------------------------------------------------------------------------
    # MarketDataProvider implementation
    # -------------------------------------------------------------------------

    def get_quote(self, symbol: str) -> Quote:
        """
        Get current index quote from Kite.
        Fails with DataUnavailableError if credentials absent/invalid.
        """
        token = KITE_INSTRUMENT_TOKENS.get(symbol.upper())
        if token is None:
            raise DataUnavailableError(
                f"Symbol '{symbol}' not in KiteProvider instrument token map. "
                f"Supported: {list(KITE_INSTRUMENT_TOKENS.keys())}"
            )

        try:
            data = self._session.get(
                KITE_QUOTE_URL,
                params={"i": f"NSE:{symbol.upper()}"},
            )
        except (AuthenticationError, DataUnavailableError):
            raise

        instrument_key = f"NSE:{symbol.upper()}"
        quote_data = data.get("data", {}).get(instrument_key, {})
        if not quote_data:
            raise DataUnavailableError(f"No quote data from Kite for {symbol}")

        last_price = quote_data.get("last_price")
        if last_price is None:
            raise DataUnavailableError(f"Kite quote for {symbol} has no last_price")

        ohlc = quote_data.get("ohlc", {})
        now = now_ist()

        return Quote(
            symbol=symbol.upper(),
            last_price=float(last_price),
            change=_safe_float(quote_data.get("change")),
            change_pct=_safe_float(quote_data.get("change_percent")),
            open=_safe_float(ohlc.get("open")),
            high=_safe_float(ohlc.get("high")),
            low=_safe_float(ohlc.get("low")),
            close=_safe_float(ohlc.get("close")),
            volume=_safe_int(quote_data.get("volume")),
            timestamp=now,
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
        Fetch OHLCV candles from Kite Connect historical data API.

        Returns DataFrame with columns:
            date/datetime, open, high, low, close, volume, timeframe, freshness_level, source

        Each candle carries:
        - timeframe: the requested interval string
        - freshness_level: LIVE/DELAYED/STALE/END_OF_DAY based on candle age
        - source: 'kite_connect'

        Raises DataUnavailableError if credentials are absent or data unavailable.
        Raises AuthenticationError if credentials are invalid.
        """
        token = KITE_INSTRUMENT_TOKENS.get(symbol.upper())
        if token is None:
            raise DataUnavailableError(
                f"KiteProvider: symbol '{symbol}' not found. "
                f"Supported: {list(KITE_INSTRUMENT_TOKENS.keys())}"
            )

        kite_interval = KITE_INTERVAL_MAP.get(interval)
        if kite_interval is None:
            raise DataUnavailableError(
                f"KiteProvider: interval '{interval}' not supported. "
                f"Supported: {list(KITE_INTERVAL_MAP.keys())}"
            )

        url = f"{KITE_HISTORICAL_URL}/{token}/{kite_interval}"
        params = {
            "from": start.isoformat(),
            "to": end.isoformat(),
            "continuous": "0",
            "oi": "0",
        }

        try:
            response = self._session.get(url, params=params)
        except (AuthenticationError, DataUnavailableError):
            raise

        candles = response.get("data", {}).get("candles", [])
        if not candles:
            logger.warning(f"KiteProvider: no candles returned for {symbol} {interval} {start}–{end}")
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
                logger.warning(f"KiteProvider: malformed candle row skipped: {c!r} — {exc}")
                continue

        if not rows:
            return pd.DataFrame(
                columns=["date", "open", "high", "low", "close", "volume", "timeframe", "freshness_level", "source"]
            )

        df = pd.DataFrame(rows)
        df = df.sort_values("date").reset_index(drop=True)
        return df

    def health_check(self) -> bool:
        """Return True only if credentials are present and Kite is reachable."""
        return (
            self._capability_report.credentials_valid
            and self._capability_report.reachable
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val: Any) -> Optional[float]:
    if val is None or val == "" or val == "-":
        return None
    try:
        r = float(val)
        return r if r == r else None  # NaN guard
    except (ValueError, TypeError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    if val is None or val == "" or val == "-":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None
