"""
Tests for Phase 10A Market Calendar & Exchange Session Validator.
"""

from datetime import date, datetime, time
import zoneinfo
import pytest

from src.research.phase10a.validation.calendar_validator import NSECalendarValidator, IST


def test_standard_trading_days():
    """Verify standard trading days are correctly identified."""
    # Monday 2024-01-15 is a standard trading day
    assert NSECalendarValidator.is_trading_day(date(2024, 1, 15)) is True
    # Saturday 2024-01-13 is a weekend (not trading day)
    assert NSECalendarValidator.is_trading_day(date(2024, 1, 13)) is False
    # Sunday 2024-01-14 is a weekend
    assert NSECalendarValidator.is_trading_day(date(2024, 1, 14)) is False


def test_official_nse_holidays():
    """Verify official exchange holidays are not trading days."""
    # Republic Day 2024-01-26
    assert NSECalendarValidator.is_trading_day(date(2024, 1, 26)) is False
    # Independence Day 2024-08-15
    assert NSECalendarValidator.is_trading_day(date(2024, 8, 15)) is False
    # Mahatma Gandhi Jayanti 2024-10-02
    assert NSECalendarValidator.is_trading_day(date(2024, 10, 2)) is False


def test_muhurat_trading_session():
    """Verify Diwali Muhurat evening session is identified with correct hours."""
    muhurat_2024 = date(2024, 11, 1)
    assert NSECalendarValidator.is_trading_day(muhurat_2024) is True
    hours = NSECalendarValidator.get_session_hours(muhurat_2024)
    assert hours == (time(18, 0), time(19, 0))


def test_timestamp_validation_in_session():
    """Verify timestamp validation rejects out-of-session hours and accepts in-session hours."""
    # 10:30 IST on trading day -> Valid
    ts_valid = datetime(2024, 1, 15, 10, 30, tzinfo=IST)
    is_valid, msg = NSECalendarValidator.validate_timestamp_in_session(ts_valid)
    assert is_valid is True
    assert msg == "VALID_SESSION_TIMESTAMP"

    # 08:30 IST (Pre-market early) -> Invalid
    ts_early = datetime(2024, 1, 15, 8, 30, tzinfo=IST)
    is_valid_early, _ = NSECalendarValidator.validate_timestamp_in_session(ts_early)
    assert is_valid_early is False

    # 16:00 IST (Post-market) -> Invalid
    ts_late = datetime(2024, 1, 15, 16, 0, tzinfo=IST)
    is_valid_late, _ = NSECalendarValidator.validate_timestamp_in_session(ts_late)
    assert is_valid_late is False

    # 11:00 IST on Holiday (Republic Day) -> Invalid
    ts_holiday = datetime(2024, 1, 26, 11, 0, tzinfo=IST)
    is_valid_hol, _ = NSECalendarValidator.validate_timestamp_in_session(ts_holiday)
    assert is_valid_hol is False
