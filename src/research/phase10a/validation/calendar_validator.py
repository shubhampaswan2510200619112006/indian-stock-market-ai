"""
Phase 10A — NSE Market Calendar & Exchange Session Validator.

Authoritative representation of National Stock Exchange of India (NSE)
trading sessions for 2024, 2025, and 2026.

Distinguishes official NSE exchange holidays from generic bank/public holidays.
Correctly models:
- Normal trading sessions: 09:15:00 to 15:30:00 IST (Pre-open 09:00 to 09:08 IST)
- Muhurat Trading: Special annual 1-hour evening session on Diwali
- Weekends (Saturday, Sunday) as non-trading days, except special declared sessions.
"""

from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Set, Tuple
import zoneinfo

IST = zoneinfo.ZoneInfo("Asia/Kolkata")

# Official NSE Trading Holidays (Capital Markets / Equity Derivatives)
# Sources: NSE Circulars & Exchange Holiday Calendars for 2024, 2025, 2026
NSE_HOLIDAYS_2024: Set[date] = {
    date(2024, 1, 22),   # Special Holiday (Ayodhya Pran Pratishtha)
    date(2024, 1, 26),   # Republic Day
    date(2024, 3, 8),    # Maha Shivratri
    date(2024, 3, 25),   # Holi
    date(2024, 3, 29),   # Good Friday
    date(2024, 4, 11),   # Id-Ul-Fitr (Ramzan Eid)
    date(2024, 4, 17),   # Shri Ram Navami
    date(2024, 5, 1),    # Maharashtra Day
    date(2024, 5, 20),   # Parliamentary Elections (Mumbai)
    date(2024, 6, 17),   # Bakri Id / Eid ul-Adha
    date(2024, 7, 17),   # Moharram
    date(2024, 8, 15),   # Independence Day
    date(2024, 10, 2),   # Mahatma Gandhi Jayanti
    date(2024, 11, 1),   # Diwali Laxmi Pujan (Regular closed; Muhurat in evening)
    date(2024, 11, 15),  # Guru Nanak Jayanti
    date(2024, 11, 20),  # Maharashtra Assembly Elections
    date(2024, 12, 25),  # Christmas
}

NSE_HOLIDAYS_2025: Set[date] = {
    date(2025, 2, 26),   # Maha Shivratri
    date(2025, 3, 14),   # Holi
    date(2025, 3, 31),   # Id-Ul-Fitr
    date(2025, 4, 10),   # Shri Mahavir Jayanti
    date(2025, 4, 14),   # Dr. Baba Saheb Ambedkar Jayanti
    date(2025, 4, 18),   # Good Friday
    date(2025, 5, 1),    # Maharashtra Day
    date(2025, 6, 6),    # Bakri Id
    date(2025, 8, 15),   # Independence Day
    date(2025, 8, 27),   # Ganesh Chaturthi
    date(2025, 10, 2),   # Mahatma Gandhi Jayanti / Dussehra
    date(2025, 10, 21),  # Diwali Laxmi Pujan (Regular closed; Muhurat in evening)
    date(2025, 10, 22),  # Diwali Balipratipada
    date(2025, 11, 5),   # Prakash Gurpurb Sri Guru Nanak Dev
    date(2025, 12, 25),  # Christmas
}

NSE_HOLIDAYS_2026: Set[date] = {
    date(2026, 1, 26),   # Republic Day
    date(2026, 2, 16),   # Maha Shivratri
    date(2026, 3, 4),    # Holi
    date(2026, 3, 20),   # Id-Ul-Fitr
    date(2026, 4, 3),    # Good Friday
    date(2026, 4, 14),   # Dr. Baba Saheb Ambedkar Jayanti
    date(2026, 5, 1),    # Maharashtra Day
    date(2026, 5, 27),   # Bakri Id
    date(2026, 6, 26),   # Muharram
    date(2026, 9, 14),   # Ganesh Chaturthi
    date(2026, 10, 2),   # Mahatma Gandhi Jayanti
    date(2026, 10, 20),  # Dussehra
    date(2026, 11, 9),   # Diwali Laxmi Pujan (Muhurat session)
    date(2026, 11, 10),  # Diwali Balipratipada
    date(2026, 11, 24),  # Guru Nanak Jayanti
    date(2026, 12, 25),  # Christmas
}

ALL_NSE_HOLIDAYS: Set[date] = NSE_HOLIDAYS_2024 | NSE_HOLIDAYS_2025 | NSE_HOLIDAYS_2026

# Special Muhurat Trading sessions (Date -> (Start IST, End IST))
MUHURAT_SESSIONS: Dict[date, Tuple[time, time]] = {
    date(2024, 11, 1): (time(18, 0), time(19, 0)),
    date(2025, 10, 21): (time(18, 15), time(19, 15)),
    date(2026, 11, 9): (time(18, 15), time(19, 15)),
}

# Special disaster recovery / mock trading live weekend sessions
SPECIAL_LIVE_SESSIONS: Dict[date, Tuple[time, time]] = {
    date(2024, 3, 2): (time(9, 15), time(15, 30)),   # Special Disaster Recovery live trading session
    date(2024, 5, 18): (time(9, 15), time(15, 30)),  # Special live trading session
}


class NSECalendarValidator:
    """
    Authoritative NSE trading calendar and session validator.
    """

    @classmethod
    def is_trading_day(cls, dt: date) -> bool:
        """Check if a given date is an official NSE trading day."""
        # Special weekend live trading sessions
        if dt in SPECIAL_LIVE_SESSIONS or dt in MUHURAT_SESSIONS:
            return True

        # Standard weekend
        if dt.weekday() >= 5:  # Saturday=5, Sunday=6
            return False

        # Official NSE holiday
        if dt in ALL_NSE_HOLIDAYS:
            return False

        return True

    @classmethod
    def get_session_hours(cls, dt: date) -> Optional[Tuple[time, time]]:
        """
        Return (session_start, session_end) in IST for a given date.
        Returns None if not a trading day.
        """
        if dt in MUHURAT_SESSIONS:
            return MUHURAT_SESSIONS[dt]
        if dt in SPECIAL_LIVE_SESSIONS:
            return SPECIAL_LIVE_SESSIONS[dt]
        if not cls.is_trading_day(dt):
            return None
        return (time(9, 15), time(15, 30))

    @classmethod
    def get_trading_days(cls, start_date: date, end_date: date) -> List[date]:
        """Return list of all official NSE trading days in [start_date, end_date]."""
        days = []
        cur = start_date
        while cur <= end_date:
            if cls.is_trading_day(cur):
                days.append(cur)
            cur += timedelta(days=1)
        return days

    @classmethod
    def validate_timestamp_in_session(cls, ts: datetime) -> Tuple[bool, str]:
        """
        Validate whether a datetime falls strictly within an active NSE market session.
        Handles timezone conversion to IST if tz-aware.
        """
        if ts.tzinfo is not None:
            ts_ist = ts.astimezone(IST)
        else:
            # Assume IST if naive
            ts_ist = ts.replace(tzinfo=IST)

        d = ts_ist.date()
        t = ts_ist.time()

        if not cls.is_trading_day(d):
            return False, f"Date {d} is not an official NSE trading day."

        hours = cls.get_session_hours(d)
        if hours is None:
            return False, f"No session scheduled on {d}."

        start_t, end_t = hours
        if t < start_t or t > end_t:
            return False, f"Time {t} is outside session hours ({start_t} - {end_t} IST) on {d}."

        return True, "VALID_SESSION_TIMESTAMP"

    @classmethod
    def audit_calendar_coverage(cls, start_date: date, end_date: date) -> Dict[str, int]:
        """Audit total calendar days, weekends, holidays, special sessions, and trading days."""
        total_days = (end_date - start_date).days + 1
        weekends = 0
        holidays = 0
        special_sessions = 0
        trading_days = 0

        cur = start_date
        while cur <= end_date:
            if cur in SPECIAL_LIVE_SESSIONS or cur in MUHURAT_SESSIONS:
                special_sessions += 1
                trading_days += 1
            elif cur.weekday() >= 5:
                weekends += 1
            elif cur in ALL_NSE_HOLIDAYS:
                holidays += 1
            else:
                trading_days += 1
            cur += timedelta(days=1)

        return {
            "total_calendar_days": total_days,
            "weekend_days": weekends,
            "official_holidays": holidays,
            "special_sessions": special_sessions,
            "official_trading_days": trading_days,
        }
