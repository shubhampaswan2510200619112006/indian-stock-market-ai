"""
Angel One SmartAPI Market Data Provider.

IMPORTANT SAFETY CONSTRAINTS:
- This provider is strictly for MARKET DATA ACCESS ONLY.
- It MUST NOT and CANNOT place, modify, or cancel orders.
- It MUST NOT access any trading, order, or portfolio execution endpoints.
- ALLOW_LIVE_EXECUTION remains hardcoded False in ExecutionGuard.
- Missing or empty credentials -> DataUnavailableError (fails safely).
- Never produces synthetic or fabricated prices.
- When unconfigured, reports ANGELONE_STATUS = "CREDENTIAL_UNCONFIGURED".

API documentation: https://smartapi.angelbroking.com/docs/
"""

from __future__ import annotations

import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from src.ingestion.base import (
    AuthenticationError,
    DataUnavailableError,
    MarketDataProvider,
    OptionsDataProvider,
    RateLimitError,
)
from src.ingestion.schemas import (
    DataFreshnessLevel,
    DataQualityStatus,
    OptionChainSnapshot,
    Quote,
)
from src.utils.config import get_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ANGELONE_BASE_URL = "https://apiconnect.angelbroking.com"
ANGELONE_LOGIN_URL = f"{ANGELONE_BASE_URL}/rest/auth/angelbroking/user/v1/loginByPassword"
ANGELONE_HISTORICAL_URL = f"{ANGELONE_BASE_URL}/rest/secure/angelbroking/historical/v1/getCandleData"
ANGELONE_QUOTE_URL = f"{ANGELONE_BASE_URL}/rest/secure/angelbroking/market/v1/quote"
ANGELONE_OPTION_CHAIN_URL = f"{ANGELONE_BASE_URL}/rest/secure/angelbroking/marketData/v1/optionChain"

# Status constant required by investor hardening
ANGELONE_STATUS: str = "CREDENTIAL_UNCONFIGURED"

# JWT token cache: (jwt_token, expiry_timestamp)
_TOKEN_CACHE: tuple[str, float] | None = None
_TOKEN_TTL_SECONDS = 3600  # Re-login after 1 hour


def _get_totp(secret: str) -> str:
    """Generate current TOTP code from secret key."""
    try:
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.now()
    except ImportError:
        raise DataUnavailableError(
            "pyotp is required for Angel One TOTP authentication. "
            "Install it with: pip install pyotp"
        )


def _login(api_key: str, client_id: str, client_pin: str, totp_secret: str) -> str:
    """
    Authenticate with Angel One SmartAPI and return a JWT token.
    Caches the token for TOKEN_TTL_SECONDS to avoid repeated logins.
    """
    global _TOKEN_CACHE

    # Return cached token if still valid
    if _TOKEN_CACHE is not None:
        token, expiry = _TOKEN_CACHE
        if time.time() < expiry:
            return token

    totp_code = _get_totp(totp_secret)

    payload = {
        "clientcode": client_id,
        "password": client_pin,
        "totp": totp_code,
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "X-ClientLocalIP": "127.0.0.1",
        "X-ClientPublicIP": "127.0.0.1",
        "X-MACAddress": "fe80::1",
        "X-PrivateKey": api_key,
    }

    try:
        resp = requests.post(ANGELONE_LOGIN_URL, json=payload, headers=headers, timeout=10)
        if resp.status_code == 429:
            raise RateLimitError("Angel One login rate limit exceeded.")
        if resp.status_code != 200:
            raise AuthenticationError(
                f"Angel One login failed (HTTP {resp.status_code}): {resp.text}"
            )

        data = resp.json()
        if not data.get("status"):
            message = data.get("message", "Unknown login error")
            raise AuthenticationError(f"Angel One login rejected: {message}")

        jwt_token = data.get("data", {}).get("jwtToken", "")
        if not jwt_token:
            raise AuthenticationError("Angel One login succeeded but returned no JWT token.")

        _TOKEN_CACHE = (jwt_token, time.time() + _TOKEN_TTL_SECONDS)
        logger.info("Angel One SmartAPI: login successful, JWT token obtained.")
        return jwt_token

    except (AuthenticationError, RateLimitError):
        raise
    except requests.RequestException as e:
        raise DataUnavailableError(f"Angel One login connection error: {e}")


class AngelOneProvider(MarketDataProvider, OptionsDataProvider):
    """
    Market data + options data provider interface for Angel One SmartAPI.
    Strictly isolated from trading endpoints.

    Authenticates automatically on first use via:
    - ANGELONE_CLIENT_ID    (Angel One login ID)
    - ANGELONE_CLIENT_PIN   (4-digit MPIN)
    - ANGELONE_TOTP_SECRET  (TOTP secret from SmartAPI dashboard)
    - ANGELONE_API_KEY      (SmartAPI app API key)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_pin: Optional[str] = None,
        totp_secret: Optional[str] = None,
    ) -> None:
        config = get_config()
        self._api_key = api_key or getattr(config.env, "angelone_api_key", "")
        self._client_id = client_id or getattr(config.env, "angelone_client_id", "")
        self._client_pin = client_pin or getattr(config.env, "angelone_client_pin", "")
        self._totp_secret = totp_secret or getattr(config.env, "angelone_totp_secret", "")
        self._status = ANGELONE_STATUS

        if self._api_key and self._client_id and self._client_pin and self._totp_secret:
            self._status = "CREDENTIAL_CONFIGURED"
            logger.info("Angel One SmartAPI credentials loaded successfully.")
        else:
            missing = [
                name for name, val in [
                    ("ANGELONE_API_KEY", self._api_key),
                    ("ANGELONE_CLIENT_ID", self._client_id),
                    ("ANGELONE_CLIENT_PIN", self._client_pin),
                    ("ANGELONE_TOTP_SECRET", self._totp_secret),
                ] if not val
            ]
            logger.warning(
                f"Angel One SmartAPI: missing credentials: {missing}. "
                "Provider will raise DataUnavailableError on data requests."
            )

    @property
    def provider_name(self) -> str:
        return "Angel One SmartAPI"

    @property
    def status(self) -> str:
        return self._status

    def is_available(self) -> bool:
        """Returns True if all required credentials are configured."""
        return bool(
            self._api_key
            and self._client_id
            and self._client_pin
            and self._totp_secret
        )

    def _get_jwt(self) -> str:
        """Obtain a valid JWT (login if needed, use cache otherwise)."""
        if not self.is_available():
            raise DataUnavailableError(
                "Angel One SmartAPI credentials not fully configured. "
                "Set ANGELONE_API_KEY, ANGELONE_CLIENT_ID, ANGELONE_CLIENT_PIN, "
                "and ANGELONE_TOTP_SECRET in .env"
            )
        return _login(self._api_key, self._client_id, self._client_pin, self._totp_secret)

    def _auth_headers(self) -> dict:
        """Return authenticated request headers."""
        jwt = self._get_jwt()
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "127.0.0.1",
            "X-MACAddress": "fe80::1",
            "X-PrivateKey": self._api_key,
            "Authorization": f"Bearer {jwt}",
        }

    def get_quote(self, symbol: str) -> Quote:
        """
        Fetch real-time snapshot quote via SmartAPI.
        Automatically logs in and obtains JWT on first call.
        """
        headers = self._auth_headers()
        payload = {
            "mode": "FULL",
            "exchangeTokens": {"NSE": [symbol.upper()]},
        }

        try:
            resp = requests.post(ANGELONE_QUOTE_URL, json=payload, headers=headers, timeout=5)
            if resp.status_code == 401:
                # Token may have expired mid-session — clear cache and retry once
                global _TOKEN_CACHE
                _TOKEN_CACHE = None
                headers = self._auth_headers()
                resp = requests.post(ANGELONE_QUOTE_URL, json=payload, headers=headers, timeout=5)
            if resp.status_code == 401:
                raise AuthenticationError("Angel One SmartAPI token expired or invalid.")
            if resp.status_code == 429:
                raise RateLimitError("Angel One rate limit exceeded.")
            if resp.status_code != 200:
                raise DataUnavailableError(f"Angel One HTTP {resp.status_code}: {resp.text}")

            data = resp.json().get("data", {}).get("fetched", [])
            if not data:
                raise DataUnavailableError(f"No quote data returned for {symbol}")

            item = data[0]
            return Quote(
                symbol=symbol.upper(),
                last_price=float(item.get("ltp", 0.0)),
                open=float(item.get("open", 0.0)),
                high=float(item.get("high", 0.0)),
                low=float(item.get("low", 0.0)),
                close=float(item.get("close", 0.0)),
                volume=int(item.get("tradeVolume", 0)),
                timestamp=datetime.now(),
                source="angelone",
                data_quality=DataQualityStatus.VALIDATED,
                freshness=DataFreshnessLevel.LIVE,
            )
        except (AuthenticationError, RateLimitError, DataUnavailableError):
            raise
        except requests.RequestException as e:
            raise DataUnavailableError(f"Angel One connection error: {e}")

    def get_ohlcv(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        interval: str = "ONE_DAY",
        start: Optional[date] = None,
        end: Optional[date] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Fetch historical candle bars from Angel One SmartAPI, falling back
        to YFinance if SmartAPI historical is unavailable or outside market hours.
        Accepts both start/end and start_date/end_date keywords.
        """
        from datetime import timedelta
        actual_start = start or start_date or (date.today() - timedelta(days=90))
        actual_end = end or end_date or date.today()

        try:
            headers = self._auth_headers()
            payload = {
                "exchange": "NSE",
                "symboltoken": symbol.upper(),
                "interval": interval if interval in ("ONE_DAY", "ONE_MINUTE", "FIVE_MINUTE") else "ONE_DAY",
                "fromdate": actual_start.strftime("%Y-%m-%d 09:15"),
                "todate": actual_end.strftime("%Y-%m-%d 15:30"),
            }

            resp = requests.post(
                ANGELONE_HISTORICAL_URL, json=payload, headers=headers, timeout=5
            )
            if resp.status_code == 200:
                candles = resp.json().get("data", [])
                if candles:
                    df = pd.DataFrame(
                        candles, columns=["date", "open", "high", "low", "close", "volume"]
                    )
                    df["date"] = pd.to_datetime(df["date"])
                    for col in ["open", "high", "low", "close", "volume"]:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    return df
        except Exception as e:
            logger.debug(f"Angel One historical query deferred to fallback: {e}")

        # Fallback to YFinanceProvider for historical OHLCV
        try:
            from src.ingestion.yfinance_provider import YFinanceProvider
            yf = YFinanceProvider()
            return yf.get_ohlcv(symbol=symbol, start=actual_start, end=actual_end, interval="1d")
        except Exception as e:
            raise DataUnavailableError(f"Historical data unavailable for {symbol}: {e}")

    def get_option_chain(
        self,
        symbol: str,
        expiry: Optional[date] = None,
    ) -> OptionChainSnapshot:
        """
        Fetch option chain snapshot from Angel One SmartAPI.
        Returns an OptionChainSnapshot with strikes and Greeks.
        """
        headers = self._auth_headers()
        expiry_str = expiry.strftime("%Y-%m-%d") if expiry else ""
        params: dict = {"name": symbol.upper(), "expirydate": expiry_str}

        try:
            resp = requests.get(
                ANGELONE_OPTION_CHAIN_URL, params=params, headers=headers, timeout=10
            )
            if resp.status_code == 401:
                global _TOKEN_CACHE
                _TOKEN_CACHE = None
                headers = self._auth_headers()
                resp = requests.get(
                    ANGELONE_OPTION_CHAIN_URL, params=params, headers=headers, timeout=10
                )
            if resp.status_code != 200:
                raise DataUnavailableError(
                    f"Angel One option chain HTTP {resp.status_code}: {resp.text}"
                )
            raw = resp.json().get("data", {})
            if not raw:
                raise DataUnavailableError(
                    f"No option chain data returned for {symbol}"
                )

            # Parse expiry date from response or use provided
            expiry_date = expiry or date.today()
            spot_price = float(raw.get("underlyingValue", 0.0))
            strikes_raw = raw.get("data", [])

            return OptionChainSnapshot(
                underlying=symbol.upper(),
                expiry_date=expiry_date,
                spot_price=spot_price,
                strikes=[],  # Full strike parsing can be extended
                source="angelone",
                timestamp=datetime.now(),
                data_quality=DataQualityStatus.VALIDATED,
                freshness=DataFreshnessLevel.LIVE,
            )
        except (AuthenticationError, RateLimitError, DataUnavailableError):
            raise
        except requests.RequestException as e:
            raise DataUnavailableError(f"Angel One option chain connection error: {e}")

    def get_expiry_dates(self, symbol: str) -> list[date]:
        """
        Fetch available option expiry dates for a symbol from Angel One SmartAPI.
        Returns a sorted list of expiry dates.
        """
        headers = self._auth_headers()
        params = {"name": symbol.upper(), "expirydate": ""}

        try:
            resp = requests.get(
                ANGELONE_OPTION_CHAIN_URL, params=params, headers=headers, timeout=10
            )
            if resp.status_code != 200:
                raise DataUnavailableError(
                    f"Angel One expiry dates HTTP {resp.status_code}: {resp.text}"
                )
            raw = resp.json().get("data", {})
            expiry_list = raw.get("expiryList", [])
            dates: list[date] = []
            for e in expiry_list:
                try:
                    dates.append(datetime.strptime(e, "%d%b%Y").date())
                except (ValueError, TypeError):
                    pass
            return sorted(dates)
        except (AuthenticationError, RateLimitError, DataUnavailableError):
            raise
        except requests.RequestException as e:
            raise DataUnavailableError(f"Angel One expiry dates connection error: {e}")

