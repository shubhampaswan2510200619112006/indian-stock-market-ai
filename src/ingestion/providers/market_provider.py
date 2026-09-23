"""
YFinance Market Data Provider (Phase 7).
Implements MarketDataProvider for live/intraday quotes and candles.
Explicitly labels status as NEAR_REAL_TIME or DELAYED.
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import yfinance as yf

from src.ingestion.providers.base import MarketDataProvider, ProviderCapabilities, ProviderStatus, ProviderType


class YFinanceMarketProvider(MarketDataProvider):
    """
    Market data provider backed by yfinance.
    Note: YFinance data for Indian exchanges (NSE/BSE) is typically delayed by 15 minutes.
    Data is explicitly tagged as DELAYED or NEAR_REAL_TIME.
    """

    SYMBOL_MAP = {
        "NIFTY": "^NSEI",
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
        super().__init__(provider_name="YFinanceMarketProvider")

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            live_quotes=True,
            intraday_candles=True,
            historical_candles=True,
            volume=True,
            options_chain=False,  # NSE options chain on yfinance is unreliable/unsupported
            options_quotes=False,
            bid_ask=False,
            open_interest=False,
            news=True,
        )

    def health_check(self) -> ProviderStatus:
        start = time.time()
        try:
            ticker = yf.Ticker("^NSEI")
            _ = ticker.fast_info.get("lastPrice")
            lat = (time.time() - start) * 1000.0
            self._health.is_healthy = True
            self._health.status_label = "DELAYED"  # Honest disclosure: 15-min exchange delay
            self._health.last_successful_request = datetime.now(timezone.utc)
            self._health.latency_ms = round(lat, 2)
            self._health.capabilities = self.capabilities()
        except Exception:
            self._health.is_healthy = False
            self._health.status_label = "ERROR"
            self._health.error_count += 1
        return self._health

    def get_live_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        yf_symbol = self.SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}.NS")
        try:
            start_t = time.time()
            ticker = yf.Ticker(yf_symbol)
            info = ticker.fast_info
            price = info.get("lastPrice") or info.get("regularMarketPrice")
            prev_close = info.get("previousClose")

            if price is None:
                return None

            now_utc = datetime.now(timezone.utc)
            lat = (time.time() - start_t) * 1000.0

            day_high_val = info.get("dayHigh")
            day_low_val = info.get("dayLow")
            day_high = float(day_high_val if day_high_val is not None else price)
            day_low = float(day_low_val if day_low_val is not None else price)
            vol_val = info.get("lastVolume")
            volume = int(vol_val if vol_val is not None else 0)

            return {
                "symbol": symbol.upper(),
                "provider_symbol": yf_symbol,
                "last_price": float(price),
                "previous_close": float(prev_close) if prev_close else None,
                "change": float(price - prev_close) if prev_close else 0.0,
                "change_pct": float((price - prev_close) / prev_close * 100.0) if prev_close else 0.0,
                "day_high": day_high,
                "day_low": day_low,
                "volume": volume,
                "provider_timestamp": now_utc.isoformat(),
                "received_timestamp": now_utc.isoformat(),
                "normalized_timestamp": now_utc.isoformat(),
                "latency_ms": round(lat, 2),
                "source": "YFINANCE_NSE",
                "status_label": "DELAYED",  # Truthful label
            }
        except Exception:
            return None

    def get_intraday_candles(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> List[Dict[str, Any]]:
        yf_symbol = self.SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}.NS")
        tf_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m", "1d": "1d", "1D": "1d"}
        interval = tf_map.get(timeframe, "1m")
        period = "1d" if interval in ["1m", "5m", "15m"] else "5d"

        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                return []

            candles = []
            now_utc = datetime.now(timezone.utc)
            for idx, row in df.tail(limit).iterrows():
                candles.append({
                    "symbol": symbol.upper(),
                    "timeframe": timeframe,
                    "timestamp": idx.isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "source": "YFINANCE_NSE",
                    "received_at": now_utc.isoformat(),
                })
            return candles
        except Exception:
            return []
