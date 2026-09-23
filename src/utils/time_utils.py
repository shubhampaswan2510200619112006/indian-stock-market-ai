"""
Time utilities for Indian market hours, IST handling, and trading calendar.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# NSE market hours
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)
PRE_OPEN_START = time(9, 0)


def now_ist() -> datetime:
    """Current datetime in IST."""
    return datetime.now(IST)


def today_ist() -> date:
    """Current date in IST."""
    return now_ist().date()


def to_ist(dt: datetime) -> datetime:
    """Convert a datetime to IST. If naive, assume IST."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=IST)
    return dt.astimezone(IST)


def is_market_open(dt: Optional[datetime] = None) -> bool:
    """
    Check if NSE is currently open.

    This is a simplified check — does not account for holidays.
    A proper trading calendar should be used for production.
    """
    dt = dt or now_ist()
    dt = to_ist(dt)

    # Weekend check
    if dt.weekday() >= 5:  # Saturday=5, Sunday=6
        return False

    current_time = dt.time()
    return MARKET_OPEN <= current_time <= MARKET_CLOSE


def is_trading_day(d: Optional[date] = None) -> bool:
    """
    Check if a date is a trading day (weekday).

    Does not account for holidays — a proper calendar is needed for production.
    """
    d = d or today_ist()
    return d.weekday() < 5


def calendar_days_to_expiry(expiry: date, from_date: Optional[date] = None) -> int:
    """Calendar days remaining until expiry."""
    from_date = from_date or today_ist()
    delta = expiry - from_date
    return max(delta.days, 0)


def trading_days_to_expiry(expiry: date, from_date: Optional[date] = None) -> int:
    """
    Approximate trading (business) days to expiry.

    Does not account for holidays — a proper calendar is needed for production.
    """
    from_date = from_date or today_ist()
    if expiry <= from_date:
        return 0

    count = 0
    current = from_date
    while current < expiry:
        current += timedelta(days=1)
        if current.weekday() < 5:
            count += 1
    return count


def years_to_expiry(expiry: date, from_date: Optional[date] = None) -> float:
    """
    Time to expiry in years (calendar-day basis / 365).

    Used for option pricing models.
    """
    days = calendar_days_to_expiry(expiry, from_date)
    return days / 365.0


def format_expiry(expiry: date) -> str:
    """Format expiry date as human-readable string: '12-Sep-2025'."""
    return expiry.strftime("%d-%b-%Y")


def parse_nse_date(date_str: str) -> date:
    """
    Parse date strings from NSE API responses.

    NSE uses formats like '12-Sep-2025' or '2025-09-12'.
    """
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d-%B-%Y", "%d %b %Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse NSE date string: '{date_str}'")


def data_age_seconds(timestamp: datetime) -> float:
    """Calculate age of data in seconds from now."""
    now = now_ist()
    ts = to_ist(timestamp)
    return (now - ts).total_seconds()
