"""
Tests for Phase 9 NSE Market Calendar & Timing Engine.
"""

from datetime import date, datetime, time, timezone
import zoneinfo
import pytest

from src.data_infrastructure.calendar import NSEMarketCalendar, IST


def test_weekend_not_trading_day():
    # Saturday & Sunday
    saturday = date(2025, 3, 15)
    sunday = date(2025, 3, 16)
    assert NSEMarketCalendar.is_trading_day(saturday) is False
    assert NSEMarketCalendar.is_trading_day(sunday) is False


def test_republic_day_holiday():
    republic_day = date(2026, 1, 26)
    assert NSEMarketCalendar.is_trading_day(republic_day) is False


def test_regular_trading_day():
    # Wednesday March 12, 2025 (normal trading day)
    wednesday = date(2025, 3, 12)
    assert NSEMarketCalendar.is_trading_day(wednesday) is True


def test_market_session_states():
    # 09:05 IST on trading day -> PRE_OPEN
    dt_pre_open = datetime(2025, 3, 12, 9, 5, tzinfo=IST)
    assert NSEMarketCalendar.get_session_type(dt_pre_open) == "PRE_OPEN"

    # Pre-open is not continuous fill eligible
    is_fill, reason = NSEMarketCalendar.is_fill_eligible(dt_pre_open)
    assert is_fill is False
    assert reason == "PRE_OPEN_AUCTION_ONLY"

    # 10:30 IST on trading day -> MARKET_OPEN
    dt_open = datetime(2025, 3, 12, 10, 30, tzinfo=IST)
    assert NSEMarketCalendar.get_session_type(dt_open) == "MARKET_OPEN"
    is_fill, reason = NSEMarketCalendar.is_fill_eligible(dt_open)
    assert is_fill is True
    assert reason == "MARKET_OPEN"

    # 18:00 IST -> MARKET_CLOSED
    dt_closed = datetime(2025, 3, 12, 18, 0, tzinfo=IST)
    assert NSEMarketCalendar.get_session_type(dt_closed) == "MARKET_CLOSED"


def test_reference_expiries_registration():
    # Reference data from exchange takes priority over formula
    actual_expiries = [date(2025, 3, 27), date(2025, 4, 24)]
    NSEMarketCalendar.register_reference_expiries("NIFTY", actual_expiries)

    registered = NSEMarketCalendar.get_reference_expiries("NIFTY")
    assert registered == actual_expiries


def test_fallback_monthly_expiry_calculation():
    # Last Thursday of January 2025 was Jan 30
    exp = NSEMarketCalendar.calculate_fallback_monthly_expiry(2025, 1)
    assert exp == date(2025, 1, 30)
