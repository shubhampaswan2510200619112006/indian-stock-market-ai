"""
Data cleaning pipeline.

Rules:
- Preserve nulls — NEVER fill missing data with guesses
- Flag outliers for human review — do NOT silently remove
- Normalize timestamps to IST
- Detect and flag duplicates
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.ingestion.schemas import (
    DataQualityStatus,
    OptionChainSnapshot,
    OptionQuote,
    OptionStrikeRow,
)
from src.utils.logging_config import get_logger
from src.utils.time_utils import to_ist

logger = get_logger(__name__)


def clean_option_chain(snapshot: OptionChainSnapshot) -> OptionChainSnapshot:
    """
    Clean an option chain snapshot.

    - Normalizes timestamps to IST
    - Computes derived fields (bid-ask spread, volume/OI ratio) where missing
    - Flags data quality issues
    - NEVER invents data — missing fields stay None
    """
    cleaned_strikes = []

    for row in snapshot.strikes:
        ce = _clean_option_quote(row.ce) if row.ce else None
        pe = _clean_option_quote(row.pe) if row.pe else None

        cleaned_strikes.append(OptionStrikeRow(
            strike_price=row.strike_price,
            expiry_date=row.expiry_date,
            ce=ce,
            pe=pe,
            moneyness=row.moneyness,
            distance_from_atm=row.distance_from_atm,
            distance_from_atm_pct=row.distance_from_atm_pct,
        ))

    return snapshot.model_copy(update={"strikes": cleaned_strikes})


def _clean_option_quote(quote: OptionQuote) -> OptionQuote:
    """Clean a single option quote."""
    updates: dict = {}

    # Normalize timestamp
    if quote.timestamp:
        updates["timestamp"] = to_ist(quote.timestamp)

    # Compute bid-ask spread if we have both sides but it wasn't computed
    if (
        quote.bid_ask_spread is None
        and quote.bid_price is not None
        and quote.ask_price is not None
    ):
        spread = quote.ask_price - quote.bid_price
        updates["bid_ask_spread"] = spread if spread >= 0 else None
        if spread >= 0 and quote.bid_price + quote.ask_price > 0:
            mid = (quote.bid_price + quote.ask_price) / 2
            updates["bid_ask_spread_pct"] = (spread / mid) * 100 if mid > 0 else None

    # Compute volume/OI ratio if missing
    if (
        quote.volume_oi_ratio is None
        and quote.volume is not None
        and quote.open_interest is not None
        and quote.open_interest > 0
    ):
        updates["volume_oi_ratio"] = quote.volume / quote.open_interest

    # Flag suspect: bid > ask
    if (
        quote.bid_price is not None
        and quote.ask_price is not None
        and quote.bid_price > quote.ask_price
    ):
        updates["data_quality"] = DataQualityStatus.SUSPECT
        logger.debug(
            f"Suspect: bid ({quote.bid_price}) > ask ({quote.ask_price}) "
            f"at strike {quote.strike_price} {quote.option_type.value}"
        )

    if updates:
        return quote.model_copy(update=updates)
    return quote
