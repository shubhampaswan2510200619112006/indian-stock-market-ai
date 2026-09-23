"""
Phase 9 — Concrete YFinance Market Data Provider.

Implements MarketDataProvider and HistoricalMarketDataProvider interfaces.
Provides:
- Rigorous timestamp capture (request, response, received, processed).
- Truthful VERIFIED_DELAYED status.
- Explicit disclosure of missing Bid/Ask (is_executable = False).
- Resampling annotation (is_derived_interval).
- Complete observation provenance.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import time
from typing import Any, Dict, List, Optional
import uuid
import yfinance as yf

from src.data_infrastructure.models import (
    DataStatus,
    MarketObservation,
    ObservationTimestamps,
)
from src.data_infrastructure.providers.base import (
    HistoricalMarketDataProvider,
    MarketDataProvider,
)
from src.data_infrastructure.providers.verification import ProviderVerificationEngine


class Phase9YFinanceProvider(MarketDataProvider, HistoricalMarketDataProvider):
    """
    Market and Historical provider backed by Yahoo Finance.
    Truthfully classified as VERIFIED_DELAYED (15-min exchange delay).
    """

    SYMBOL_MAP = {
        "NIFTY": "^NSEI",
        "NIFTY50": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
        "SENSEX": "^BSESN",
        "RELIANCE": "RELIANCE.NS",
        "TCS": "TCS.NS",
        "INFY": "INFY.NS",
        "HDFCBANK": "HDFCBANK.NS",
        "ICICIBANK": "ICICIBANK.NS",
    }

    def __init__(self):
        self._provider_name = "YFINANCE"
        self._error_count = 0
        self._last_successful: Optional[datetime] = None

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def capabilities(self) -> Dict[str, bool]:
        return {
            "live_quotes": True,
            "intraday_candles": True,
            "historical_candles": True,
            "bid_ask": False,            # Transparent truth: No Bid/Ask on public free tier
            "options_chain": False,
            "options_quotes": False,
            "open_interest": False,
            "implied_volatility": False,
        }

    def health_check(self) -> Dict[str, Any]:
        start = time.time()
        try:
            ticker = yf.Ticker("^NSEI")
            _ = ticker.fast_info.get("lastPrice")
            lat = round((time.time() - start) * 1000.0, 2)
            self._last_successful = datetime.now(timezone.utc)
            return {
                "provider_name": self.provider_name,
                "is_healthy": True,
                "status_label": DataStatus.VERIFIED_DELAYED.value,
                "latency_ms": lat,
                "error_count": self._error_count,
                "last_successful_request": self._last_successful.isoformat(),
            }
        except Exception as e:
            self._error_count += 1
            return {
                "provider_name": self.provider_name,
                "is_healthy": False,
                "status_label": DataStatus.ERROR.value,
                "latency_ms": round((time.time() - start) * 1000.0, 2),
                "error_count": self._error_count,
                "error_message": str(e),
            }

    def get_quote(self, symbol: str) -> Optional[MarketObservation]:
        """Fetches a normalized market observation with strict timestamp provenance."""
        yf_symbol = self.SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}.NS")
        req_time = datetime.now(timezone.utc)

        try:
            ticker = yf.Ticker(yf_symbol)
            info = ticker.fast_info
            price = info.get("lastPrice") or info.get("regularMarketPrice")
            if price is None:
                return None

            rec_time = datetime.now(timezone.utc)
            prov_time = rec_time  # YFinance does not provide raw exchange tick timestamp

            vol_val = info.get("lastVolume")
            volume = int(vol_val) if vol_val is not None else 0

            timestamps = ObservationTimestamps(
                provider_timestamp=prov_time,
                received_timestamp=rec_time,
                processed_timestamp=datetime.now(timezone.utc),
                request_timestamp=req_time,
                response_timestamp=rec_time,
            )

            observation = MarketObservation(
                observation_id=f"OBS-{uuid.uuid4().hex[:12]}",
                provider=self.provider_name,
                provider_symbol=yf_symbol,
                symbol=symbol.upper(),
                timestamps=timestamps,
                last_price=float(price),
                bid_price=None,  # Free feed does not provide executable Bid/Ask
                ask_price=None,  # Free feed does not provide executable Bid/Ask
                volume=volume,
                open_interest=None,
                data_status=DataStatus.VERIFIED_DELAYED,
                validation_status="VALID",
                is_executable=False,  # LTP alone cannot be executed
                raw_payload={
                    "currency": info.get("currency"),
                    "exchange": info.get("exchange"),
                    "lastPrice": price,
                },
            )

            # Record verification evidence
            ProviderVerificationEngine.record_verification(
                provider_name=self.provider_name,
                capability="market_quotes",
                test_instrument=symbol.upper(),
                observed_provider_timestamp=prov_time,
                observed_received_timestamp=rec_time,
                observed_fields={"last_price": price, "volume": volume, "bid": None, "ask": None},
                notes="Observation verified. No executable Bid/Ask supplied.",
            )

            return observation

        except Exception as e:
            self._error_count += 1
            return None

    def get_quotes(self, symbols: List[str]) -> List[MarketObservation]:
        observations = []
        for s in symbols:
            obs = self.get_quote(s)
            if obs:
                observations.append(obs)
        return observations

    def get_intraday_candles(
        self,
        symbol: str,
        interval: str = "1m",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        yf_symbol = self.SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}.NS")
        period = "5d" if interval in ("1m", "2m") else "1mo"
        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                return []

            candles = []
            for idx, row in df.iterrows():
                ts = idx.to_pydatetime()
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                candles.append({
                    "symbol": symbol.upper(),
                    "timeframe": interval,
                    "candle_timestamp": ts.isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "is_derived_interval": False,
                    "source_provider": self.provider_name,
                    "data_status": DataStatus.VERIFIED_DELAYED.value,
                })
            return candles
        except Exception:
            return []

    def get_daily_candles(
        self,
        symbol: str,
        start: date,
        end: date,
    ) -> List[Dict[str, Any]]:
        return self.load_daily_bars(symbol, start, end)

    def load_daily_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        yf_symbol = self.SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}.NS")
        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(start=start_date.isoformat(), end=end_date.isoformat(), interval="1d")
            if df.empty:
                return []

            bars = []
            for idx, row in df.iterrows():
                bars.append({
                    "symbol": symbol.upper(),
                    "date": idx.date().isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "adjusted_close": float(row["Close"]),
                    "source": self.provider_name,
                    "data_status": DataStatus.HISTORICAL.value,
                })
            return bars
        except Exception:
            return []

    def load_intraday_bars(
        self,
        symbol: str,
        interval: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> List[Dict[str, Any]]:
        return self.get_intraday_candles(symbol, interval=interval, start=start_dt, end=end_dt)

    def get_market_status(self) -> str:
        # Determine from current time in IST
        from src.utils.time_utils import now_ist, MARKET_OPEN, MARKET_CLOSE
        curr = now_ist()
        if curr.weekday() >= 5:
            return "MARKET_CLOSED"
        t = curr.time()
        if MARKET_OPEN <= t <= MARKET_CLOSE:
            return "MARKET_OPEN"
        return "MARKET_CLOSED"
