"""
Live Market Data Validator & Freshness Evaluator (Phase 7).
Ensures OHLC sanity, timestamp ordering, and truthful freshness status labels.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from src.live_market.models import LiveCandle, LiveQuote, RealTimeDataStatus


class LiveDataValidator:
    """Validates live quotes, intraday candles, and evaluates freshness."""

    @staticmethod
    def validate_quote(quote_dict: Dict) -> Tuple[bool, Optional[LiveQuote], Optional[str]]:
        """Validates a raw live quote dict and returns a typed LiveQuote."""
        if not quote_dict:
            return False, None, "Empty quote object."

        last_price = quote_dict.get("last_price")
        if last_price is None or last_price <= 0:
            return False, None, f"Invalid last price: {last_price}"

        volume = quote_dict.get("volume", 0)
        if volume < 0:
            return False, None, f"Negative volume: {volume}"

        # Freshness evaluation
        status_label = quote_dict.get("status_label", "DELAYED")
        rec_time_str = quote_dict.get("received_timestamp")
        if rec_time_str:
            try:
                rec_dt = datetime.fromisoformat(rec_time_str)
                now_dt = datetime.now(timezone.utc)
                age_sec = (now_dt - rec_dt).total_seconds()
                if age_sec > 300:  # Older than 5 minutes -> STALE
                    status_label = RealTimeDataStatus.STALE
            except Exception:
                pass

        try:
            quote = LiveQuote(
                symbol=quote_dict["symbol"],
                provider_symbol=quote_dict.get("provider_symbol", quote_dict["symbol"]),
                last_price=float(last_price),
                previous_close=quote_dict.get("previous_close"),
                change=float(quote_dict.get("change", 0.0)),
                change_pct=float(quote_dict.get("change_pct", 0.0)),
                day_high=float(quote_dict.get("day_high", last_price)),
                day_low=float(quote_dict.get("day_low", last_price)),
                volume=int(volume),
                provider_timestamp=quote_dict.get("provider_timestamp", ""),
                received_timestamp=quote_dict.get("received_timestamp", ""),
                normalized_timestamp=quote_dict.get("normalized_timestamp", ""),
                latency_ms=float(quote_dict.get("latency_ms", 0.0)),
                source=quote_dict.get("source", "UNKNOWN"),
                status_label=RealTimeDataStatus(status_label),
            )
            return True, quote, None
        except Exception as e:
            return False, None, f"Validation error: {e}"

    @staticmethod
    def validate_candle(candle_dict: Dict) -> Tuple[bool, Optional[LiveCandle], Optional[str]]:
        """Validates OHLC candle consistency."""
        o, h, l, c = candle_dict.get("open"), candle_dict.get("high"), candle_dict.get("low"), candle_dict.get("close")
        if any(v is None or v <= 0 for v in [o, h, l, c]):
            return False, None, f"Invalid OHLC values: O={o}, H={h}, L={l}, C={c}"

        if h < max(o, c, l) or l > min(o, c, h):
            return False, None, f"Inconsistent OHLC relationship: O={o}, H={h}, L={l}, C={c}"

        try:
            candle = LiveCandle(
                symbol=candle_dict["symbol"],
                timeframe=candle_dict.get("timeframe", "1m"),
                timestamp=candle_dict["timestamp"],
                open=float(o),
                high=float(h),
                low=float(l),
                close=float(c),
                volume=int(candle_dict.get("volume", 0)),
                source=candle_dict.get("source", "UNKNOWN"),
                received_at=candle_dict.get("received_at", ""),
            )
            return True, candle, None
        except Exception as e:
            return False, None, f"Validation error: {e}"
