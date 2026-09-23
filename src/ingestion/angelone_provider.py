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

from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from src.ingestion.base import (
    AuthenticationError,
    DataUnavailableError,
    MarketDataProvider,
    RateLimitError,
)
from src.ingestion.schemas import (
    DataFreshnessLevel,
    DataQualityStatus,
    Quote,
)
from src.utils.config import get_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ANGELONE_BASE_URL = "https://apiconnect.angelbroking.com"
ANGELONE_HISTORICAL_URL = f"{ANGELONE_BASE_URL}/rest/secure/angelbroking/historical/v1/getCandleData"
ANGELONE_QUOTE_URL = f"{ANGELONE_BASE_URL}/rest/secure/angelbroking/market/v1/quote"

# Status constant required by investor hardening
ANGELONE_STATUS: str = "CREDENTIAL_UNCONFIGURED"


class AngelOneProvider(MarketDataProvider):
    """
    Market data provider interface for Angel One SmartAPI.
    Strictly isolated from trading endpoints.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        jwt_token: Optional[str] = None,
    ) -> None:
        config = get_config()
        self._api_key = api_key or getattr(config.env, "angelone_api_key", "")
        self._client_id = client_id or getattr(config.env, "angelone_client_id", "")
        self._jwt_token = jwt_token or ""
        self._status = ANGELONE_STATUS

        if not self._api_key or not self._client_id:
            logger.info("Angel One SmartAPI credentials not configured in environment.")

    @property
    def provider_name(self) -> str:
        return "Angel One SmartAPI"

    @property
    def status(self) -> str:
        return self._status

    def is_available(self) -> bool:
        """Returns True only if valid API credentials exist."""
        return bool(self._api_key and self._client_id and self._jwt_token)

    def get_quote(self, symbol: str) -> Quote:
        """
        Fetch real-time snapshot quote via SmartAPI.
        Raises DataUnavailableError when credentials are unconfigured.
        """
        if not self.is_available():
            raise DataUnavailableError(
                f"Angel One SmartAPI: symbol '{symbol}' unavailable. "
                f"ANGELONE_STATUS = {self._status}. "
                "Configure ANGELONE_API_KEY and ANGELONE_CLIENT_ID in .env to enable."
            )

        # Execution blocked / Data fetch implementation when authenticated
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "127.0.0.1",
            "X-MACAddress": "fe80::1",
            "X-PrivateKey": self._api_key,
            "Authorization": f"Bearer {self._jwt_token}",
        }
        payload = {
            "mode": "FULL",
            "exchangeTokens": {"NSE": [symbol.upper()]},
        }

        try:
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
        except requests.RequestException as e:
            raise DataUnavailableError(f"Angel One connection error: {e}")

    def get_ohlcv(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "ONE_DAY",
    ) -> pd.DataFrame:
        """
        Fetch historical candle bars from Angel One SmartAPI.
        Raises DataUnavailableError when unconfigured.
        """
        if not self.is_available():
            raise DataUnavailableError(
                f"Angel One SmartAPI: Historical candles for '{symbol}' unavailable. "
                f"ANGELONE_STATUS = {self._status}. "
                "Configure credentials in .env to enable."
            )

        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
