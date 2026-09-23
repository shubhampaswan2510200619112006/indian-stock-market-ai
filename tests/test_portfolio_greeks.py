"""
Unit tests for Portfolio & Multi-Leg Strategy Greeks Aggregator.
"""

from datetime import date, datetime

import pytest

from src.ingestion.schemas import OptionType
from src.options.portfolio_greeks import OptionLeg, aggregate_portfolio_greeks
from src.options.pricing import black_scholes_greeks


def test_bull_call_spread_net_greeks():
    """
    Bull Call Spread:
    +1 Long Call (24000)
    -1 Short Call (24500)
    Net Delta must be Positive, Net Vega Positive, Net Theta Negative.
    """
    S, T, r, sigma = 24000.0, 0.1, 0.07, 0.18
    g_long = black_scholes_greeks(S, 24000.0, T, r, sigma, OptionType.CE)
    g_short = black_scholes_greeks(S, 24500.0, T, r, sigma, OptionType.CE)

    leg1 = OptionLeg(strike_price=24000.0, option_type=OptionType.CE, quantity=1, lot_size=25, greeks=g_long)
    leg2 = OptionLeg(strike_price=24500.0, option_type=OptionType.CE, quantity=-1, lot_size=25, greeks=g_short)

    net_g = aggregate_portfolio_greeks([leg1, leg2])

    assert net_g.net_delta > 0.0, "Bull call spread net delta must be positive"
    assert net_g.net_vega > 0.0, "Bull call spread net vega must be positive"
    assert net_g.net_theta < 0.0, "Bull call spread net theta must be negative"


def test_delta_hedged_straddle_net_greeks():
    """
    Long Straddle:
    +1 Long Call (24000)
    +1 Long Put (24000)
    Net Delta near 0 (at ATM), Net Gamma > 0, Net Vega > 0, Net Theta < 0.
    """
    S, K, T, r, sigma = 24000.0, 24000.0, 0.1, 0.07, 0.18
    g_call = black_scholes_greeks(S, K, T, r, sigma, OptionType.CE)
    g_put = black_scholes_greeks(S, K, T, r, sigma, OptionType.PE)

    leg1 = OptionLeg(strike_price=K, option_type=OptionType.CE, quantity=1, lot_size=25, greeks=g_call)
    leg2 = OptionLeg(strike_price=K, option_type=OptionType.PE, quantity=1, lot_size=25, greeks=g_put)

    net_g = aggregate_portfolio_greeks([leg1, leg2])

    assert abs(net_g.net_delta) < 5.0, "Straddle net delta should be near 0 at ATM"
    assert net_g.net_gamma > 0.0, "Long straddle net gamma must be positive"
    assert net_g.net_vega > 0.0, "Long straddle net vega must be positive"
    assert net_g.net_theta < 0.0, "Long straddle net theta must be negative"
