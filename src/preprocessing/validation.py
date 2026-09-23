"""
Data validation module.

Validates ingested data for quality issues.
Returns DataQualityReport — never silently fixes or invents data.

Checks:
- Price sanity (non-negative, within reasonable range)
- OI sanity (non-negative)
- Volume consistency
- Bid ≤ Ask
- Staleness detection
- Missing field tracking
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.ingestion.schemas import (
    DataQualityReport,
    DataQualityStatus,
    OptionChainSnapshot,
    OptionQuote,
)
from src.utils.config import get_config
from src.utils.logging_config import get_logger
from src.utils.time_utils import data_age_seconds, is_market_open, now_ist

logger = get_logger(__name__)


def validate_option_chain(snapshot: OptionChainSnapshot) -> DataQualityReport:
    """
    Validate an entire option chain snapshot.

    Returns a DataQualityReport describing quality issues found.
    Does NOT modify the data — only reports.
    """
    report = DataQualityReport()
    total = 0
    valid = 0
    partial = 0
    suspect = 0
    missing: dict[str, int] = {}
    errors: list[str] = []

    # Validate spot price
    if snapshot.spot_price is None or snapshot.spot_price <= 0:
        errors.append(f"Invalid spot price: {snapshot.spot_price}")

    for row in snapshot.strikes:
        for quote, side in [(row.ce, "CE"), (row.pe, "PE")]:
            if quote is None:
                continue
            total += 1
            issues = _validate_option_quote(quote)

            if not issues:
                valid += 1
            elif any(i["severity"] == "suspect" for i in issues):
                suspect += 1
                for i in issues:
                    errors.append(f"{side} {row.strike_price}: {i['message']}")
            else:
                partial += 1

            # Track missing fields
            for field in ["last_price", "bid_price", "ask_price", "volume", "open_interest"]:
                if getattr(quote, field) is None:
                    missing[field] = missing.get(field, 0) + 1

    # Determine overall quality
    if total == 0:
        overall = DataQualityStatus.UNAVAILABLE
        errors.append("No option data in snapshot")
    elif suspect > total * 0.2:
        overall = DataQualityStatus.SUSPECT
    elif partial > total * 0.5:
        overall = DataQualityStatus.PARTIAL
    elif valid == total:
        overall = DataQualityStatus.GOOD
    else:
        overall = DataQualityStatus.GOOD

    # Check staleness
    age = data_age_seconds(snapshot.timestamp)
    config = get_config()
    freshness = config.data_freshness_config
    stale_threshold = freshness.get("stale_threshold", 3600)

    if overall != DataQualityStatus.UNAVAILABLE and is_market_open() and age > stale_threshold:
        overall = DataQualityStatus.STALE
        errors.append(f"Data is {age:.0f}s old (threshold: {stale_threshold}s)")

    report.total_records = total
    report.valid_records = valid
    report.partial_records = partial
    report.suspect_records = suspect
    report.missing_fields = missing
    report.validation_errors = errors
    report.overall_quality = overall

    return report


def _validate_option_quote(quote: OptionQuote) -> list[dict]:
    """
    Validate a single option quote.
    Returns list of issues found. Empty list = valid.
    """
    issues = []

    # Price sanity
    if quote.last_price is not None and quote.last_price < 0:
        issues.append({"field": "last_price", "severity": "suspect", "message": "Negative LTP"})

    if quote.bid_price is not None and quote.bid_price < 0:
        issues.append({"field": "bid_price", "severity": "suspect", "message": "Negative bid"})

    if quote.ask_price is not None and quote.ask_price < 0:
        issues.append({"field": "ask_price", "severity": "suspect", "message": "Negative ask"})

    # Bid ≤ Ask
    if (
        quote.bid_price is not None
        and quote.ask_price is not None
        and quote.bid_price > quote.ask_price
        and quote.ask_price > 0
    ):
        issues.append({
            "field": "bid_ask",
            "severity": "suspect",
            "message": f"Bid ({quote.bid_price}) > Ask ({quote.ask_price})",
        })

    # OI sanity
    if quote.open_interest is not None and quote.open_interest < 0:
        issues.append({"field": "open_interest", "severity": "suspect", "message": "Negative OI"})

    # Volume sanity
    if quote.volume is not None and quote.volume < 0:
        issues.append({"field": "volume", "severity": "suspect", "message": "Negative volume"})

    # IV sanity (from source — should be 0-500% range)
    if quote.implied_volatility is not None:
        if quote.implied_volatility < 0:
            issues.append({"field": "iv", "severity": "suspect", "message": "Negative IV"})
        elif quote.implied_volatility > 500:
            issues.append({"field": "iv", "severity": "suspect", "message": f"Very high IV: {quote.implied_volatility}%"})

    return issues


def validate_spot_price(price: Optional[float], symbol: str) -> bool:
    """Quick sanity check on a spot price."""
    if price is None or price <= 0:
        return False

    # Basic range checks for known indices
    ranges = {
        "NIFTY": (5000, 50000),
        "BANKNIFTY": (10000, 100000),
        "FINNIFTY": (5000, 50000),
    }
    if symbol.upper() in ranges:
        low, high = ranges[symbol.upper()]
        if not (low <= price <= high):
            logger.warning(f"Spot price {price} for {symbol} outside expected range [{low}, {high}]")
            return False

    return True
