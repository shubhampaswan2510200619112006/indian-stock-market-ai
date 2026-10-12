"""
Unit tests for the resilient Synthetic Option Chain generator and strike structures.
"""

from datetime import date
import pytest

from src.ingestion.schemas import OptionChainSnapshot, OptionType
from src.options.chain import OptionChainAnalyzer
from src.options.synthetic_chain import (
    generate_synthetic_option_chain,
    get_fallback_expiries,
)
from src.preprocessing.cleaning import clean_option_chain
from src.preprocessing.validation import validate_option_chain


def test_get_fallback_expiries():
    expiries = get_fallback_expiries("NIFTY", count=4)
    assert len(expiries) == 4
    for exp in expiries:
        assert isinstance(exp, date)
        # Weekday should be Thursday (3)
        assert exp.weekday() == 3
        assert exp >= date.today()


def test_generate_synthetic_option_chain_nifty():
    snap = generate_synthetic_option_chain("NIFTY", num_strikes_each_side=10)
    assert isinstance(snap, OptionChainSnapshot)
    assert snap.underlying == "NIFTY"
    assert snap.spot_price > 0
    assert len(snap.strikes) == 21  # 10 below + ATM + 10 above
    assert snap.total_ce_oi > 0
    assert snap.total_pe_oi > 0

    # Verify cleaning and validation pipeline passes
    cleaned = clean_option_chain(snap)
    report = validate_option_chain(cleaned)
    assert report is not None

    # Verify analysis passes without error
    analyzer = OptionChainAnalyzer()
    analysis = analyzer.analyze(cleaned)
    assert analysis.atm_strike is not None
    assert analysis.put_call_ratio_oi > 0


def test_generate_synthetic_option_chain_banknifty():
    snap = generate_synthetic_option_chain("BANKNIFTY", num_strikes_each_side=5)
    assert snap.underlying == "BANKNIFTY"
    assert len(snap.strikes) == 11
    # Check strikes step is 100
    strikes = [r.strike_price for r in snap.strikes]
    diffs = [strikes[i+1] - strikes[i] for i in range(len(strikes)-1)]
    assert all(d == 100.0 for d in diffs)
