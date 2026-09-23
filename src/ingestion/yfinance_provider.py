"""
Yahoo Finance data provider for historical underlying price data.

Uses yfinance for OHLCV history. Not suitable for live options data.
This is a FALLBACK provider for price history when NSE historical data
is unavailable via the direct API.

Limitations:
- Delayed data (typically 15-minute delay)
- No intraday options data
- No option chain data (use NSE provider for that)
- May have gaps or missing data
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import pandas as pd

from src.ingestion.base import (
    DataUnavailableError,
    MarketDataProvider,
)
from src.ingestion.schemas import (
    DataQualityStatus,
    Quote,
)
from src.utils.config import get_config
from src.utils.logging_config import get_logger
from src.utils.time_utils import now_ist

logger = get_logger(__name__)


class YFinanceProvider(MarketDataProvider):
    """
    Yahoo Finance provider for historical underlying price data.

    Maps our internal symbols to yfinance symbols:
    - NIFTY → ^NSEI
    - BANKNIFTY → ^NSEBANK
    - Individual stocks → SYMBOL.NS
    """

    @property
    def provider_name(self) -> str:
        return "yfinance"

    def _get_yf_symbol(self, symbol: str) -> str:
        """Map internal symbol to yfinance symbol."""
        config = get_config()
        underlying = config.get_underlying(symbol)
        if underlying and underlying.get("yfinance_symbol"):
            return underlying["yfinance_symbol"]

        # Fallback mapping
        symbol_map = {
            "NIFTY": "^NSEI",
            "NIFTY50": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
        }
        return symbol_map.get(symbol.upper(), f"{symbol.upper()}.NS")

    def get_quote(self, symbol: str) -> Quote:
        """Get latest quote from yfinance. Note: may be delayed."""
        try:
            import yfinance as yf
        except ImportError:
            raise DataUnavailableError("yfinance not installed. Run: pip install yfinance")

        yf_symbol = self._get_yf_symbol(symbol)

        try:
            ticker = yf.Ticker(yf_symbol)
            info = ticker.fast_info

            last_price = getattr(info, "last_price", None)
            if last_price is None:
                # Try history fallback
                hist = ticker.history(period="1d")
                if not hist.empty:
                    last_price = float(hist["Close"].iloc[-1])
                else:
                    raise DataUnavailableError(f"No price data for {symbol} ({yf_symbol})")

            prev_close = getattr(info, "previous_close", None) or getattr(info, "regularMarketPreviousClose", None)
            change = None
            change_pct = None
            if prev_close and last_price:
                change = last_price - prev_close
                change_pct = (change / prev_close) * 100

            return Quote(
                symbol=symbol.upper(),
                last_price=float(last_price),
                change=change,
                change_pct=change_pct,
                open=getattr(info, "open", None),
                high=getattr(info, "day_high", None),
                low=getattr(info, "day_low", None),
                close=prev_close,
                timestamp=now_ist(),
                source=self.provider_name,
                # yfinance data is typically delayed
                data_quality=DataQualityStatus.GOOD,
            )
        except DataUnavailableError:
            raise
        except Exception as e:
            logger.error(f"yfinance quote error for {symbol}: {e}")
            raise DataUnavailableError(f"Cannot get quote for {symbol}: {e}")

    def get_ohlcv(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Get historical OHLCV from yfinance."""
        try:
            import yfinance as yf
        except ImportError:
            raise DataUnavailableError("yfinance not installed. Run: pip install yfinance")

        yf_symbol = self._get_yf_symbol(symbol)

        try:
            ticker = yf.Ticker(yf_symbol)
            # yfinance end date is exclusive, add 1 day
            hist = ticker.history(
                start=start.isoformat(),
                end=(end + timedelta(days=1)).isoformat(),
                interval=interval,
            )

            if hist.empty:
                logger.warning(f"No historical data from yfinance for {symbol}")
                return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

            # Normalize column names
            df = hist.reset_index()
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]

            # Rename 'date' column if it's named differently
            if "date" not in df.columns and "datetime" in df.columns:
                df = df.rename(columns={"datetime": "date"})

            # Ensure date column is date type
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"]).dt.date

            # Select relevant columns
            result_cols = ["date", "open", "high", "low", "close", "volume"]
            available_cols = [c for c in result_cols if c in df.columns]
            df = df[available_cols].copy()

            return df

        except Exception as e:
            logger.error(f"yfinance OHLCV error for {symbol}: {e}")
            raise DataUnavailableError(f"Cannot get OHLCV for {symbol}: {e}")

    def get_india_vix(self) -> Optional[float]:
        """Fetch current India VIX level from yfinance (^INDIAVIX). Returns None if unavailable."""
        try:
            import yfinance as yf
            ticker = yf.Ticker("^INDIAVIX")
            info = ticker.fast_info
            price = getattr(info, "last_price", None)
            if price is None:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = float(hist["Close"].iloc[-1])
            return float(price) if price is not None else None
        except Exception as e:
            logger.warning(f"India VIX data unavailable from yfinance: {e}")
            return None

    def health_check(self) -> bool:
        """Check if yfinance is working."""
        try:
            import yfinance as yf
            ticker = yf.Ticker("^NSEI")
            info = ticker.fast_info
            return getattr(info, "last_price", None) is not None
        except Exception:
            return False

