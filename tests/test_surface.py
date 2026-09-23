"""
Unit tests for Volatility Surface & Expected Move Engine.
"""

from datetime import date, datetime, timedelta

import pytest

from src.ingestion.schemas import OptionChainSnapshot, OptionQuote, OptionStrikeRow, OptionType
from src.options.surface import compute_expected_move, compute_volatility_surface


def make_sample_chain():
    exp = date.today() + timedelta(days=14)
    spot = 24000.0

    strikes_data = [
        (21600.0, 0.25, 0.28),  # 90% Put strike
        (24000.0, 0.16, 0.16),  # ATM strike
        (26400.0, 0.14, 0.18),  # 110% Call strike
    ]

    rows = []
    for k, ce_iv, pe_iv in strikes_data:
        ce_q = OptionQuote(
            timestamp=datetime.now(),
            source="test",
            underlying="NIFTY",
            option_type=OptionType.CE,
            strike_price=k,
            expiry_date=exp,
            last_price=100.0,
            implied_volatility=ce_iv,
        )
        pe_q = OptionQuote(
            timestamp=datetime.now(),
            source="test",
            underlying="NIFTY",
            option_type=OptionType.PE,
            strike_price=k,
            expiry_date=exp,
            last_price=100.0,
            implied_volatility=pe_iv,
        )
        rows.append(OptionStrikeRow(strike_price=k, expiry_date=exp, ce=ce_q, pe=pe_q))

    return OptionChainSnapshot(
        timestamp=datetime.now(),
        source="test",
        underlying="NIFTY",
        expiry_date=exp,
        spot_price=spot,
        strikes=rows,
    )



def test_volatility_surface_skew():
    chain = make_sample_chain()
    surface = compute_volatility_surface(chain)

    assert surface.atm_iv == 0.16
    assert surface.otm_put_skew is not None
    assert surface.otm_call_skew is not None
    # Put IV (0.28) > ATM IV (0.16) -> positive put skew
    assert surface.otm_put_skew > 0.0


def test_compute_expected_move():
    exp = date.today() + timedelta(days=30)
    move = compute_expected_move(
        spot=24000.0,
        expiry_date=exp,
        atm_iv=0.15,
        realized_vol_20d=0.12,
        atr_14=250.0,
    )

    assert move.model_implied_move_pts is not None
    assert move.model_implied_move_pts > 0.0
    assert move.historical_rv_move_pts is not None
    assert move.atr_move_pts is not None

    # Model implied range
    assert move.model_implied_upper > 24000.0
    assert move.model_implied_lower < 24000.0
