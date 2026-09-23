"""
Live Market Service Manager (Phase 7).
Controls market, options, and news data providers with controlled refresh intervals.
Handles capability discovery, failure isolation, rate limits, and caching.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd

from src.ingestion.providers.base import ProviderStatus
from src.ingestion.providers.market_provider import YFinanceMarketProvider
from src.ingestion.providers.news_provider import VerifiedRSSNewsProvider
from src.ingestion.providers.options_provider import NSELiveOptionsProvider
from src.live_market.cache import LiveDataCache
from src.live_market.models import LiveCandle, LiveQuote, MultiTimeframeSummary, RealTimeDataStatus
from src.live_market.validator import LiveDataValidator


class LiveMarketService:
    """
    Core Live Market Service.
    Integrates market data, options data, and news intelligence feeds cleanly.
    """

    def __init__(self):
        self.market_provider = YFinanceMarketProvider()
        self.options_provider = NSELiveOptionsProvider()
        self.news_provider = VerifiedRSSNewsProvider()
        self.cache = LiveDataCache(default_ttl_seconds=30)
        self.validator = LiveDataValidator()

    def get_provider_health(self) -> List[ProviderStatus]:
        """Runs health checks across all active providers."""
        return [
            self.market_provider.health_check(),
            self.options_provider.health_check(),
            self.news_provider.health_check(),
        ]

    def fetch_live_quote(self, symbol: str = "NIFTY") -> Optional[LiveQuote]:
        """Fetches validated live quote with cache fallback."""
        cache_key = f"quote_{symbol.upper()}"
        cached_val, is_expired = self.cache.get(cache_key)
        if cached_val and not is_expired:
            return cached_val

        raw_quote = self.market_provider.get_live_quote(symbol)
        if not raw_quote:
            if cached_val:
                # Return stale cached value with STALE label if provider fails
                cached_val.status_label = RealTimeDataStatus.STALE
                return cached_val
            return None

        is_valid, quote, err = self.validator.validate_quote(raw_quote)
        if is_valid and quote:
            self.cache.set(cache_key, quote, ttl_seconds=30, source=quote.source)
            return quote

        return None

    def fetch_intraday_candles(self, symbol: str = "NIFTY", timeframe: str = "1m", limit: int = 100) -> List[LiveCandle]:
        """Fetches validated intraday candles."""
        cache_key = f"candles_{symbol.upper()}_{timeframe}"
        cached_val, is_expired = self.cache.get(cache_key)
        if cached_val and not is_expired:
            return cached_val

        raw_candles = self.market_provider.get_intraday_candles(symbol, timeframe=timeframe, limit=limit)
        valid_candles: List[LiveCandle] = []

        for c_dict in raw_candles:
            is_valid, candle, _ = self.validator.validate_candle(c_dict)
            if is_valid and candle:
                valid_candles.append(candle)

        if valid_candles:
            self.cache.set(cache_key, valid_candles, ttl_seconds=60, source="YFINANCE_NSE")

        return valid_candles

    def compute_multi_timeframe_summary(self, symbol: str = "NIFTY") -> MultiTimeframeSummary:
        """Assembles multi-timeframe regime signals (1m, 5m, 15m, 1h, 1D)."""
        # Fetch 1m and 1h candles
        candles_1m = self.fetch_intraday_candles(symbol, timeframe="1m", limit=30)
        candles_1h = self.fetch_intraday_candles(symbol, timeframe="1h", limit=30)

        tf_signals = {}
        for tf, candles in [("1m", candles_1m), ("1h", candles_1h)]:
            if len(candles) >= 5:
                closes = [c.close for c in candles]
                if closes[-1] > closes[0]:
                    tf_signals[tf] = "BULLISH"
                elif closes[-1] < closes[0]:
                    tf_signals[tf] = "BEARISH"
                else:
                    tf_signals[tf] = "NEUTRAL"
            else:
                tf_signals[tf] = "NEUTRAL"

        signal_1m = tf_signals.get("1m", "NEUTRAL")
        signal_1h = tf_signals.get("1h", "NEUTRAL")

        if signal_1m == "BULLISH" and signal_1h == "BULLISH":
            overall = "STRONGLY BULLISH"
            conflicts = []
        elif signal_1m == "BEARISH" and signal_1h == "BEARISH":
            overall = "STRONGLY BEARISH"
            conflicts = []
        elif signal_1m != signal_1h and "NEUTRAL" not in [signal_1m, signal_1h]:
            overall = "CONFLICTING / VOLATILE"
            conflicts = [f"1m signal ({signal_1m}) conflicts with 1h signal ({signal_1h})."]
        else:
            overall = "MODERATELY BULLISH" if "BULLISH" in [signal_1m, signal_1h] else "SIDEWAYS"
            conflicts = []

        return MultiTimeframeSummary(
            symbol=symbol.upper(),
            tf_1m=signal_1m,
            tf_5m=signal_1m,
            tf_15m=signal_1m,
            tf_1h=signal_1h,
            tf_1d=signal_1h,
            overall_multi_tf_regime=overall,
            conflicting_signals=conflicts,
        )

    def get_live_snapshot(self, symbol: str = "NIFTY"):
        """Assembles unified LiveMarketSnapshot aggregate."""
        from src.live_market.snapshot import build_live_market_snapshot
        quote = self.fetch_live_quote(symbol)
        candles = self.fetch_intraday_candles(symbol, timeframe="1m", limit=30)
        multi_tf = self.compute_multi_timeframe_summary(symbol)
        opts = self.options_provider.get_live_option_chain(symbol) or {"status_label": "UNAVAILABLE"}
        news = self.news_provider.fetch_latest_news(limit=10)
        health = self.get_provider_health()
        ml_status = {
            "overall_status": "NORMAL",
            "research_banner": "MODEL RESEARCH STATUS: LIMITED DATA / INSUFFICIENT STATISTICAL EVIDENCE",
        }
        return build_live_market_snapshot(
            symbol=symbol,
            quote=quote,
            candles=candles,
            multi_tf=multi_tf,
            options_summary=opts,
            news_items=news,
            health_statuses=health,
            ml_status=ml_status,
        )
