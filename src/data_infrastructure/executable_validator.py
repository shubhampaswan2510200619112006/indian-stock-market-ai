"""
Phase 9 — Executable Quote Validator.

Enforces the non-negotiable principle:
EXECUTION REQUIRES GENUINE EXECUTABLE BID/ASK QUOTES.
LTP MAY BE USED ONLY FOR VALUATION MARKS, NEVER AS AN EXECUTION FALLBACK.

Rejection Codes:
- NO_BID: Bid is missing or non-positive for a SELL order.
- NO_ASK: Ask is missing or non-positive for a BUY order.
- INVALID_SPREAD: Bid > Ask (crossed market) or spread exceeds configured limit.
- STALE_QUOTE: Observation is marked STALE.
- MARKET_CLOSED: Market is currently closed.
- TIMESTAMP_INVALID: Timestamps exhibit clock skew or impossible ordering.
- PROVIDER_UNAVAILABLE: Provider feed is unconfigured or UNAVAILABLE.
- DATA_UNVERIFIED: Provider capability is UNVERIFIED.
- QUOTE_TOO_OLD: Quote age exceeds maximum allowable execution age.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.data_infrastructure.models import DataStatus


@dataclass
class QuoteValidationResult:
    is_executable: bool
    rejection_code: Optional[str] = None
    rejection_details: Optional[str] = None
    executable_price: Optional[float] = None
    spread_pct: Optional[float] = None
    valuation_mark: Optional[float] = None


class ExecutableQuoteValidator:
    """
    Standardized, reusable validation gate for trade execution eligibility.
    """

    DEFAULT_MAX_SPREAD_PCT: float = 2.5
    DEFAULT_MAX_AGE_SECONDS: float = 60.0

    @classmethod
    def validate_for_execution(
        cls,
        side: str,  # "BUY" or "SELL"
        bid: Optional[float],
        ask: Optional[float],
        ltp: Optional[float] = None,
        quote_age_seconds: Optional[float] = None,
        data_status: Optional[str | DataStatus] = None,
        is_market_open: bool = True,
        max_spread_pct: float = DEFAULT_MAX_SPREAD_PCT,
        max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
    ) -> QuoteValidationResult:
        """
        Evaluates whether an observation satisfies all conditions for paper or live execution.
        Strictly refuses to substitute LTP for missing Bid/Ask.
        """
        side_upper = side.upper()
        status_str = data_status.value if isinstance(data_status, DataStatus) else str(data_status or "UNVERIFIED")

        # 1. Market Open Check
        if not is_market_open:
            return QuoteValidationResult(
                is_executable=False,
                rejection_code="MARKET_CLOSED",
                rejection_details="Exchange is currently closed. Normal continuous fills are forbidden.",
                valuation_mark=ltp,
            )

        # 2. Data Status Check
        if status_str == DataStatus.STALE.value:
            return QuoteValidationResult(
                is_executable=False,
                rejection_code="STALE_QUOTE",
                rejection_details="Observation is marked STALE by provider freshness monitor.",
                valuation_mark=ltp,
            )
        if status_str == DataStatus.UNAVAILABLE.value:
            return QuoteValidationResult(
                is_executable=False,
                rejection_code="PROVIDER_UNAVAILABLE",
                rejection_details="Provider feed is UNAVAILABLE.",
                valuation_mark=ltp,
            )
        if status_str == DataStatus.UNVERIFIED.value:
            return QuoteValidationResult(
                is_executable=False,
                rejection_code="DATA_UNVERIFIED",
                rejection_details="Provider data is UNVERIFIED.",
                valuation_mark=ltp,
            )
        if status_str == DataStatus.ERROR.value:
            return QuoteValidationResult(
                is_executable=False,
                rejection_code="PROVIDER_UNAVAILABLE",
                rejection_details="Provider returned ERROR status.",
                valuation_mark=ltp,
            )

        # 3. Mandatory Bid / Ask Requirement
        if side_upper == "BUY":
            if ask is None or ask <= 0.0:
                return QuoteValidationResult(
                    is_executable=False,
                    rejection_code="NO_ASK",
                    rejection_details=f"BUY order requires positive executable Ask quote. Found: ask={ask}. LTP ({ltp}) cannot be used for execution.",
                    valuation_mark=ltp,
                )
        elif side_upper == "SELL":
            if bid is None or bid <= 0.0:
                return QuoteValidationResult(
                    is_executable=False,
                    rejection_code="NO_BID",
                    rejection_details=f"SELL order requires positive executable Bid quote. Found: bid={bid}. LTP ({ltp}) cannot be used for execution.",
                    valuation_mark=ltp,
                )
        else:
            return QuoteValidationResult(
                is_executable=False,
                rejection_code="INVALID_SIDE",
                rejection_details=f"Unknown order side: {side}",
                valuation_mark=ltp,
            )

        # 4. Spread Sanity Check
        spread_pct = None
        if bid is not None and ask is not None:
            if bid > ask:
                return QuoteValidationResult(
                    is_executable=False,
                    rejection_code="INVALID_SPREAD",
                    rejection_details=f"Crossed market: Bid ({bid}) > Ask ({ask}).",
                    valuation_mark=ltp,
                )
            if ask > 0:
                spread_pct = round(((ask - bid) / ask) * 100.0, 4)
                if spread_pct > max_spread_pct:
                    return QuoteValidationResult(
                        is_executable=False,
                        rejection_code="INVALID_SPREAD",
                        rejection_details=f"Spread {spread_pct:.2f}% exceeds maximum threshold {max_spread_pct:.2f}%.",
                        spread_pct=spread_pct,
                        valuation_mark=ltp,
                    )

        # 5. Freshness / Quote Age Check
        if quote_age_seconds is not None and quote_age_seconds > max_age_seconds:
            return QuoteValidationResult(
                is_executable=False,
                rejection_code="QUOTE_TOO_OLD",
                rejection_details=f"Quote age {quote_age_seconds:.1f}s exceeds threshold {max_age_seconds:.1f}s.",
                spread_pct=spread_pct,
                valuation_mark=ltp,
            )

        # Approved for execution
        exec_price = ask if side_upper == "BUY" else bid
        return QuoteValidationResult(
            is_executable=True,
            executable_price=exec_price,
            spread_pct=spread_pct,
            valuation_mark=ltp or exec_price,
        )
