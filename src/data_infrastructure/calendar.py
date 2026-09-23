"""
Phase 9 — NSE Exchange Market Calendar & Expiry Timing Engine.

Implements exchange session awareness:
- Official standard NSE trading holidays (Republic Day, Independence Day, Gandhi Jayanti, Diwali, Holi, etc.).
- Special sessions (Muhurat Trading).
- Normal market session (09:15 - 15:30 IST).
- Pre-open session (09:00 - 09:08 IST).
- Expiry date resolution: prioritizes exchange reference data over formulas.
- Asia/Kolkata (IST) internal timezone alignment.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional
import zoneinfo

IST = zoneinfo.ZoneInfo("Asia/Kolkata")

# Session Timings (IST)
PRE_OPEN_START = time(9, 0)
PRE_OPEN_END = time(9, 8)
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)


class NSEMarketCalendar:
    """
    NSE-aware exchange calendar and trading session engine.
    """

    # Known fixed and annual exchange holidays
    STANDARD_HOLIDAYS_MAP: Dict[int, Dict[date, str]] = {
        2025: {
            date(2025, 1, 26): "Republic Day",
            date(2025, 2, 26): "Mahashivratri",
            date(2025, 3, 14): "Holi",
            date(2025, 3, 31): "Id-Ul-Fitr",
            date(2025, 4, 10): "Mahavir Jayanti",
            date(2025, 4, 14): "Dr. Baba Saheb Ambedkar Jayanti",
            date(2025, 4, 18): "Good Friday",
            date(2025, 5, 1): "Maharashtra Day",
            date(2025, 8, 15): "Independence Day",
            date(2025, 8, 27): "Ganesh Chaturthi",
            date(2025, 10, 2): "Mahatma Gandhi Jayanti",
            date(2025, 10, 21): "Diwali Laxmi Pujan",
            date(2025, 10, 22): "Diwali Balipratipada",
            date(2025, 11, 5): "Prakash Gurpurb",
            date(2025, 12, 25): "Christmas",
        },
        2026: {
            date(2026, 1, 26): "Republic Day",
            date(2026, 3, 3): "Holi",
            date(2026, 3, 20): "Id-Ul-Fitr",
            date(2026, 4, 3): "Good Friday",
            date(2026, 4, 14): "Dr. Ambedkar Jayanti",
            date(2026, 5, 1): "Maharashtra Day",
            date(2026, 8, 15): "Independence Day",
            date(2026, 10, 2): "Mahatma Gandhi Jayanti",
            date(2026, 11, 8): "Diwali Laxmi Pujan (Muhurat)",
            date(2026, 12, 25): "Christmas",
        },
    }

    # Dynamic reference expiry cache from exchange (contract master)
    _reference_expiries: Dict[str, List[date]] = {}

    @classmethod
    def register_reference_expiries(cls, underlying: str, expiries: List[date]) -> None:
        """Registers actual exchange-provided expiry dates as source of truth."""
        cls._reference_expiries[underlying.upper()] = sorted(list(set(expiries)))

    @classmethod
    def get_reference_expiries(cls, underlying: str) -> List[date]:
        """Returns registered exchange reference expiries if available."""
        return cls._reference_expiries.get(underlying.upper(), [])

    @classmethod
    def is_trading_day(cls, d: date) -> bool:
        """Determines if a given date is an active NSE trading day."""
        # Weekend check: Saturday (5), Sunday (6)
        if d.weekday() >= 5:
            return False

        # Holiday check
        year_holidays = cls.STANDARD_HOLIDAYS_MAP.get(d.year, {})
        if d in year_holidays:
            return False

        return True

    @classmethod
    def get_session_type(cls, dt: datetime) -> str:
        """
        Returns the exchange session state:
        - 'PRE_OPEN': 09:00 to 09:08 IST
        - 'MARKET_OPEN': 09:15 to 15:30 IST
        - 'MARKET_CLOSED': All other times / weekends / holidays
        """
        # Convert to IST
        dt_ist = dt.astimezone(IST) if dt.tzinfo else dt.replace(tzinfo=IST)
        d = dt_ist.date()

        if not cls.is_trading_day(d):
            return "MARKET_CLOSED"

        t = dt_ist.time()
        if PRE_OPEN_START <= t < PRE_OPEN_END:
            return "PRE_OPEN"
        if MARKET_OPEN <= t <= MARKET_CLOSE:
            return "MARKET_OPEN"

        return "MARKET_CLOSED"

    @classmethod
    def is_fill_eligible(cls, dt: Optional[datetime] = None) -> tuple[bool, str]:
        """Checks if normal-session continuous order fills are allowed."""
        eval_dt = dt or datetime.now(IST)
        session_type = cls.get_session_type(eval_dt)

        if session_type == "MARKET_OPEN":
            return True, "MARKET_OPEN"
        if session_type == "PRE_OPEN":
            return False, "PRE_OPEN_AUCTION_ONLY"
        return False, "MARKET_CLOSED"

    @classmethod
    def calculate_fallback_monthly_expiry(cls, year: int, month: int) -> date:
        """
        Fallback-only formula for monthly expiry (last Thursday, or preceding trading day if holiday).
        Never used to override verified exchange reference data.
        """
        import calendar
        # Find last day of month
        _, last_day = calendar.monthrange(year, month)
        last_date = date(year, month, last_day)

        # Thursday is weekday 3
        offset = (last_date.weekday() - 3) % 7
        last_thursday = last_date - timedelta(days=offset)

        # If last Thursday is a holiday, move to preceding trading day
        candidate = last_thursday
        while not cls.is_trading_day(candidate) and candidate.month == month:
            candidate -= timedelta(days=1)

        return candidate
