"""
NSE direct-access data provider (EXPERIMENTAL).

WARNING: This provider accesses NSE's public-facing web API endpoints.
- It is NOT an official API and NOT production-grade.
- NSE can change endpoints, block IPs, or require CAPTCHAs at any time.
- Rate limiting is enforced to respect NSE's infrastructure.
- For production use, switch to a licensed broker API (Kite, Dhan, etc.)
  by implementing the MarketDataProvider / OptionsDataProvider interfaces.

This provider:
- Manages NSE session cookies (required for API access)
- Fetches live option chain data
- Fetches index quotes
- Parses NSE JSON responses into validated Pydantic models
- Returns DataUnavailableError on failure (never invents data)
"""

from __future__ import annotations

import time
from datetime import date, datetime
from typing import Any, Optional

import pandas as pd
import requests

from src.ingestion.base import (
    DataUnavailableError,
    MarketDataProvider,
    OptionsDataProvider,
    RateLimitError,
)
from src.ingestion.schemas import (
    DataQualityStatus,
    Exchange,
    InstrumentType,
    Moneyness,
    OptionChainSnapshot,
    OptionQuote,
    OptionStrikeRow,
    OptionType,
    Quote,
)
from src.utils.config import get_config
from src.utils.logging_config import get_logger
from src.utils.time_utils import now_ist, parse_nse_date

logger = get_logger(__name__)

# NSE endpoints (public, subject to change)
NSE_BASE_URL = "https://www.nseindia.com"
NSE_OPTION_CHAIN_INDEX_URL = f"{NSE_BASE_URL}/api/option-chain-indices"
NSE_OPTION_CHAIN_EQUITY_URL = f"{NSE_BASE_URL}/api/option-chain-equities"
NSE_QUOTE_INDEX_URL = f"{NSE_BASE_URL}/api/allIndices"

# Browser-like headers (required by NSE)
NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/option-chain",
    "Connection": "keep-alive",
}


class NSESession:
    """
    Manages NSE session with cookie handling and rate limiting.

    NSE requires a valid session cookie obtained by first visiting the main page.
    """

    def __init__(self, rate_limit_seconds: float = 2.0):
        self._session = requests.Session()
        self._session.headers.update(NSE_HEADERS)
        self._last_request_time: float = 0.0
        self._rate_limit = rate_limit_seconds
        self._cookies_valid = False

    def _ensure_cookies(self) -> None:
        """Visit NSE homepage to obtain session cookies."""
        if self._cookies_valid:
            return
        try:
            self._throttle()
            resp = self._session.get(NSE_BASE_URL, timeout=10)
            resp.raise_for_status()
            self._cookies_valid = True
            logger.debug("NSE session cookies obtained")
        except Exception as e:
            logger.warning(f"Failed to obtain NSE cookies: {e}")
            self._cookies_valid = False

    def _throttle(self) -> None:
        """Enforce configurable rate limit between requests."""
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self._rate_limit:
            wait = self._rate_limit - elapsed
            logger.debug(f"Rate limiting: waiting {wait:.1f}s")
            time.sleep(wait)
        self._last_request_time = time.monotonic()

    def get(self, url: str, params: Optional[dict] = None, retries: int = 2) -> dict:
        """
        Make a GET request to NSE API with session management.

        Returns parsed JSON dict.
        Raises DataUnavailableError on failure.
        """
        self._ensure_cookies()

        for attempt in range(retries + 1):
            try:
                self._throttle()
                resp = self._session.get(url, params=params, timeout=15)

                if resp.status_code == 401 or resp.status_code == 403:
                    logger.warning("NSE session expired, refreshing cookies...")
                    self._cookies_valid = False
                    self._ensure_cookies()
                    continue

                if resp.status_code == 429:
                    raise RateLimitError("NSE rate limit hit. Increase RATE_LIMIT_DELAY_SECONDS.")

                resp.raise_for_status()
                return resp.json()

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                logger.warning(f"NSE request failed (attempt {attempt + 1}): {e}")
                if attempt == retries:
                    raise DataUnavailableError(f"Cannot reach NSE after {retries + 1} attempts: {e}")
                time.sleep(2 * (attempt + 1))  # Backoff

            except requests.exceptions.HTTPError as e:
                logger.error(f"NSE HTTP error: {e}")
                raise DataUnavailableError(f"NSE HTTP error: {e}")

            except ValueError as e:
                raise DataUnavailableError(f"Invalid JSON from NSE: {e}")

        raise DataUnavailableError("NSE request failed after all retries")


class NSEProvider(MarketDataProvider, OptionsDataProvider):
    """
    Combined market data + options data provider using direct NSE API access.

    EXPERIMENTAL — not production-grade. See module docstring for warnings.
    """

    def __init__(self):
        config = get_config()
        rate_limit = config.env.rate_limit_delay_seconds
        self._nse = NSESession(rate_limit_seconds=rate_limit)

    @property
    def provider_name(self) -> str:
        return "nse_direct"

    # -----------------------------------------------------------------
    # MarketDataProvider
    # -----------------------------------------------------------------

    def get_quote(self, symbol: str) -> Quote:
        """Get the latest quote for an index from NSE."""
        try:
            data = self._nse.get(NSE_QUOTE_INDEX_URL)
        except DataUnavailableError:
            raise

        # Find the index in the response
        indices = data.get("data", [])
        index_data = None
        for idx in indices:
            idx_key = idx.get("indexSymbol", "") or idx.get("index", "")
            if idx_key.upper().replace(" ", "") == symbol.upper().replace(" ", ""):
                index_data = idx
                break

        # Also try matching by name
        if not index_data:
            symbol_map = {
                "NIFTY": "NIFTY 50",
                "NIFTY50": "NIFTY 50",
                "BANKNIFTY": "NIFTY BANK",
                "FINNIFTY": "NIFTY FIN SERVICE",
            }
            target_name = symbol_map.get(symbol.upper(), symbol)
            for idx in indices:
                if idx.get("index", "").upper() == target_name.upper():
                    index_data = idx
                    break

        if not index_data:
            raise DataUnavailableError(f"Index '{symbol}' not found in NSE response")

        return Quote(
            symbol=symbol.upper(),
            last_price=float(index_data.get("last", 0)),
            change=_safe_float(index_data.get("variation")),
            change_pct=_safe_float(index_data.get("percentChange")),
            open=_safe_float(index_data.get("open")),
            high=_safe_float(index_data.get("high")),
            low=_safe_float(index_data.get("low")),
            close=_safe_float(index_data.get("previousClose")),
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
        NSE direct API does not provide historical OHLCV easily.
        Use YFinanceProvider for historical data instead.
        """
        raise DataUnavailableError(
            f"NSE direct provider does not support historical OHLCV. "
            f"Use yfinance provider for historical data."
        )

    # -----------------------------------------------------------------
    # OptionsDataProvider
    # -----------------------------------------------------------------

    def get_option_chain(
        self,
        symbol: str,
        expiry: Optional[date] = None,
    ) -> OptionChainSnapshot:
        """Fetch the full option chain from NSE."""
        config = get_config()
        underlying_cfg = config.get_underlying(symbol)

        # Determine URL based on instrument type
        instrument_type = "INDEX"
        if underlying_cfg:
            instrument_type = underlying_cfg.get("instrument_type", "INDEX")
            nse_symbol = underlying_cfg.get("nse_symbol", symbol)
        else:
            nse_symbol = symbol

        if instrument_type == "INDEX":
            url = NSE_OPTION_CHAIN_INDEX_URL
        else:
            url = NSE_OPTION_CHAIN_EQUITY_URL

        try:
            data = self._nse.get(url, params={"symbol": nse_symbol})
        except DataUnavailableError:
            raise

        return self._parse_option_chain(data, symbol, expiry)

    def get_expiry_dates(self, symbol: str) -> list[date]:
        """Get all available expiry dates from the option chain response."""
        config = get_config()
        underlying_cfg = config.get_underlying(symbol)
        instrument_type = "INDEX"
        if underlying_cfg:
            instrument_type = underlying_cfg.get("instrument_type", "INDEX")
            nse_symbol = underlying_cfg.get("nse_symbol", symbol)
        else:
            nse_symbol = symbol

        url = NSE_OPTION_CHAIN_INDEX_URL if instrument_type == "INDEX" else NSE_OPTION_CHAIN_EQUITY_URL

        try:
            data = self._nse.get(url, params={"symbol": nse_symbol})
        except DataUnavailableError:
            raise

        expiry_strings = data.get("records", {}).get("expiryDates", [])
        expiries = []
        for exp_str in expiry_strings:
            try:
                expiries.append(parse_nse_date(exp_str))
            except ValueError:
                logger.warning(f"Could not parse expiry date: {exp_str}")
        return sorted(expiries)

    def health_check(self) -> bool:
        """Check if NSE is reachable."""
        try:
            self._nse._ensure_cookies()
            return self._nse._cookies_valid
        except Exception:
            return False

    # -----------------------------------------------------------------
    # Parsing
    # -----------------------------------------------------------------

    def _parse_option_chain(
        self,
        data: dict,
        symbol: str,
        target_expiry: Optional[date],
    ) -> OptionChainSnapshot:
        """Parse NSE option chain JSON into our schema."""
        records = data.get("records", {})
        all_data = records.get("data", [])
        expiry_strings = records.get("expiryDates", [])

        # Get underlying value (spot price)
        underlying_value = _safe_float(
            records.get("underlyingValue")
            or data.get("filtered", {}).get("data", [{}])[0].get("CE", {}).get("underlyingValue")
            if data.get("filtered", {}).get("data") else None
        )

        # Try to get spot from the data rows if not in records
        if not underlying_value:
            for row in all_data:
                for side in ["CE", "PE"]:
                    uv = row.get(side, {}).get("underlyingValue")
                    if uv:
                        underlying_value = float(uv)
                        break
                if underlying_value:
                    break

        if not underlying_value:
            raise DataUnavailableError(f"Cannot determine spot price for {symbol}")

        # Parse available expiries
        available_expiries = []
        for exp_str in expiry_strings:
            try:
                available_expiries.append(parse_nse_date(exp_str))
            except ValueError:
                continue

        # Determine target expiry
        if target_expiry:
            selected_expiry = target_expiry
        elif available_expiries:
            selected_expiry = available_expiries[0]  # Nearest
        else:
            raise DataUnavailableError(f"No expiry dates found for {symbol}")

        selected_expiry_str = None
        for exp_str in expiry_strings:
            try:
                if parse_nse_date(exp_str) == selected_expiry:
                    selected_expiry_str = exp_str
                    break
            except ValueError:
                continue

        # Filter data for selected expiry
        expiry_data = [
            row for row in all_data
            if row.get("expiryDate") == selected_expiry_str
        ]

        if not expiry_data:
            # If exact string match fails, try date comparison
            expiry_data = []
            for row in all_data:
                try:
                    row_expiry = parse_nse_date(row.get("expiryDate", ""))
                    if row_expiry == selected_expiry:
                        expiry_data.append(row)
                except ValueError:
                    continue

        # Parse strikes
        now = now_ist()
        strikes: list[OptionStrikeRow] = []
        total_ce_oi = 0
        total_pe_oi = 0
        total_ce_vol = 0
        total_pe_vol = 0

        for row in expiry_data:
            strike_price = float(row.get("strikePrice", 0))
            ce_data = row.get("CE")
            pe_data = row.get("PE")

            ce_quote = self._parse_option_side(ce_data, symbol, strike_price, selected_expiry, OptionType.CE, now) if ce_data else None
            pe_quote = self._parse_option_side(pe_data, symbol, strike_price, selected_expiry, OptionType.PE, now) if pe_data else None

            if ce_quote and ce_quote.open_interest:
                total_ce_oi += ce_quote.open_interest
            if pe_quote and pe_quote.open_interest:
                total_pe_oi += pe_quote.open_interest
            if ce_quote and ce_quote.volume:
                total_ce_vol += ce_quote.volume
            if pe_quote and pe_quote.volume:
                total_pe_vol += pe_quote.volume

            strikes.append(OptionStrikeRow(
                strike_price=strike_price,
                expiry_date=selected_expiry,
                ce=ce_quote,
                pe=pe_quote,
            ))

        # Sort by strike
        strikes.sort(key=lambda s: s.strike_price)

        # Determine ATM strike (closest to spot)
        atm_strike = None
        if strikes:
            atm_strike = min(strikes, key=lambda s: abs(s.strike_price - underlying_value)).strike_price

        return OptionChainSnapshot(
            underlying=symbol.upper(),
            expiry_date=selected_expiry,
            spot_price=underlying_value,
            strikes=strikes,
            total_ce_oi=total_ce_oi if total_ce_oi > 0 else None,
            total_pe_oi=total_pe_oi if total_pe_oi > 0 else None,
            total_ce_volume=total_ce_vol if total_ce_vol > 0 else None,
            total_pe_volume=total_pe_vol if total_pe_vol > 0 else None,
            atm_strike=atm_strike,
            available_expiries=available_expiries,
            timestamp=now,
            source=self.provider_name,
            data_quality=DataQualityStatus.GOOD,
        )

    def _parse_option_side(
        self,
        data: dict,
        underlying: str,
        strike: float,
        expiry: date,
        option_type: OptionType,
        timestamp: datetime,
    ) -> OptionQuote:
        """Parse one side (CE or PE) of a strike row from NSE JSON."""
        ltp = _safe_float(data.get("lastPrice"))
        bid = _safe_float(data.get("bidprice"))
        ask = _safe_float(data.get("askprice"))
        volume = _safe_int(data.get("totalTradedVolume"))
        oi = _safe_int(data.get("openInterest"))
        change_oi = _safe_int(data.get("changeinOpenInterest"))
        iv = _safe_float(data.get("impliedVolatility"))

        # Compute bid-ask spread
        bid_ask_spread = None
        bid_ask_spread_pct = None
        if bid is not None and ask is not None and ask > 0:
            bid_ask_spread = ask - bid
            mid = (ask + bid) / 2
            if mid > 0:
                bid_ask_spread_pct = (bid_ask_spread / mid) * 100

        # Volume/OI ratio
        vol_oi = None
        if volume is not None and oi is not None and oi > 0:
            vol_oi = volume / oi

        # Determine data quality
        quality = DataQualityStatus.GOOD
        missing_count = sum(1 for v in [ltp, volume, oi] if v is None)
        if missing_count >= 2:
            quality = DataQualityStatus.PARTIAL
        elif missing_count == 1:
            quality = DataQualityStatus.PARTIAL

        return OptionQuote(
            underlying=underlying.upper(),
            option_type=option_type,
            strike_price=strike,
            expiry_date=expiry,
            last_price=ltp,
            bid_price=bid,
            ask_price=ask,
            volume=volume,
            open_interest=oi,
            change_in_oi=change_oi,
            implied_volatility=iv,
            bid_ask_spread=bid_ask_spread,
            bid_ask_spread_pct=bid_ask_spread_pct,
            volume_oi_ratio=vol_oi,
            timestamp=timestamp,
            source="nse_direct",
            data_quality=quality,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val: Any) -> Optional[float]:
    """Convert to float, return None if not possible."""
    if val is None or val == "" or val == "-":
        return None
    try:
        result = float(val)
        return result if not (result != result) else None  # NaN check
    except (ValueError, TypeError):
        return None


def _safe_int(val: Any) -> Optional[int]:
    """Convert to int, return None if not possible."""
    if val is None or val == "" or val == "-":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None
