"""
Option utility functions.

Moneyness classification, max pain calculation, DTE helpers,
and other option-specific utilities.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from src.ingestion.schemas import (
    Moneyness,
    OptionChainSnapshot,
    OptionType,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def classify_moneyness(
    spot: float,
    strike: float,
    option_type: OptionType,
    atm_threshold_pct: float = 0.5,
) -> Moneyness:
    """
    Classify an option as ATM, ITM, or OTM.

    ATM: strike within atm_threshold_pct of spot
    ITM: call strike < spot, put strike > spot
    OTM: call strike > spot, put strike < spot
    """
    if spot <= 0:
        return Moneyness.OTM

    pct_diff = abs(strike - spot) / spot * 100

    if pct_diff <= atm_threshold_pct:
        return Moneyness.ATM

    if option_type == OptionType.CE:
        return Moneyness.ITM if strike < spot else Moneyness.OTM
    else:  # PE
        return Moneyness.ITM if strike > spot else Moneyness.OTM


def distance_from_atm(spot: float, strike: float) -> float:
    """Absolute distance from ATM in points."""
    return strike - spot


def distance_from_atm_pct(spot: float, strike: float) -> float:
    """Percentage distance from ATM."""
    if spot <= 0:
        return 0.0
    return ((strike - spot) / spot) * 100


def calculate_max_pain(snapshot: OptionChainSnapshot) -> Optional[float]:
    """
    Calculate the Max Pain strike.

    Max Pain = strike price at which option writers (sellers) would face
    the LEAST total loss. This is where the combined CE and PE option
    buyers' payoff is minimized.

    Note: Max Pain is a theoretical concept. It does NOT guarantee that
    the underlying will close at this level. Use with caution.
    """
    if not snapshot.strikes:
        return None

    strikes_data = []
    for row in snapshot.strikes:
        ce_oi = row.ce.open_interest if row.ce and row.ce.open_interest else 0
        pe_oi = row.pe.open_interest if row.pe and row.pe.open_interest else 0
        strikes_data.append((row.strike_price, ce_oi, pe_oi))

    if not strikes_data:
        return None

    all_strikes = [s[0] for s in strikes_data]
    min_pain = float("inf")
    max_pain_strike = all_strikes[0]

    for test_price in all_strikes:
        total_pain = 0.0

        for strike, ce_oi, pe_oi in strikes_data:
            # CE buyers' loss at test_price
            if test_price > strike:
                # CE is ITM — CE writers pay out
                ce_intrinsic = test_price - strike
            else:
                # CE is OTM — CE buyers lose premium (pain = 0 for writers)
                ce_intrinsic = 0

            # PE buyers' loss at test_price
            if test_price < strike:
                # PE is ITM — PE writers pay out
                pe_intrinsic = strike - test_price
            else:
                pe_intrinsic = 0

            total_pain += ce_intrinsic * ce_oi + pe_intrinsic * pe_oi

        if total_pain < min_pain:
            min_pain = total_pain
            max_pain_strike = test_price

    return max_pain_strike


def find_atm_strike(spot: float, strikes: list[float]) -> Optional[float]:
    """Find the strike closest to spot price."""
    if not strikes:
        return None
    return min(strikes, key=lambda s: abs(s - spot))


def get_strike_step(strikes: list[float]) -> Optional[float]:
    """Infer the strike step size from a sorted list of strikes."""
    if len(strikes) < 2:
        return None
    sorted_strikes = sorted(strikes)
    diffs = [sorted_strikes[i + 1] - sorted_strikes[i] for i in range(len(sorted_strikes) - 1)]
    if not diffs:
        return None
    # Most common difference
    from collections import Counter
    counter = Counter(round(d, 2) for d in diffs)
    return counter.most_common(1)[0][0]
