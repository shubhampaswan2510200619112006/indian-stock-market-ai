"""
Phase 8 — Exchange-Aware Market Hours.

Determines NSE market state: PRE_OPEN, MARKET_OPEN, MARKET_CLOSED.
Reuses existing time_utils.py infrastructure.

Market closure is NOT a provider failure.
Normal-session fills are blocked when the market is closed.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Optional

from src.paper_trading.models import MarketState
from src.utils.time_utils import IST, MARKET_CLOSE, MARKET_OPEN, PRE_OPEN_START, now_ist, to_ist


# Pre-open ends at 09:08 IST (normal open auction)
PRE_OPEN_END = time(9, 8)


def get_market_state(dt: Optional[datetime] = None) -> MarketState:
    """
    Determine current NSE market state.

    Returns:
        MarketState.PRE_OPEN — 09:00 to 09:08 IST on trading days
        MarketState.MARKET_OPEN — 09:15 to 15:30 IST on trading days
        MarketState.MARKET_CLOSED — all other times
    """
    dt = dt or now_ist()
    dt = to_ist(dt)

    # Weekend check
    if dt.weekday() >= 5:
        return MarketState.MARKET_CLOSED

    current_time = dt.time()

    # Pre-open session: 09:00 - 09:08
    if PRE_OPEN_START <= current_time < PRE_OPEN_END:
        return MarketState.PRE_OPEN

    # Normal trading session: 09:15 - 15:30
    if MARKET_OPEN <= current_time <= MARKET_CLOSE:
        return MarketState.MARKET_OPEN

    return MarketState.MARKET_CLOSED


def is_fill_eligible_market_state(dt: Optional[datetime] = None) -> tuple[bool, str]:
    """
    Check if the current market state allows normal-session paper fills.

    Returns:
        (is_eligible, reason)
    """
    state = get_market_state(dt)

    if state == MarketState.MARKET_OPEN:
        return True, "MARKET_OPEN"

    if state == MarketState.PRE_OPEN:
        return False, "MARKET_PRE_OPEN"

    return False, "MARKET_CLOSED"
