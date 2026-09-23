"""
Unit tests for Options Strategy Payoff Engine & Breakeven Solver.
"""

import numpy as np
import pytest

from src.ingestion.schemas import OptionType
from src.options.portfolio_greeks import OptionLeg
from src.options.pricing import black_scholes_greeks
from src.strategies.payoff import (
    calculate_leg_payoff,
    calculate_multi_leg_payoff,
    calculate_strategy_breakevens_and_bounds,
    generate_payoff_grid,
)


def test_single_leg_payoff():
    # Long Call @ K=100, price=5
    payoff_itm = calculate_leg_payoff(spot=110.0, strike=100.0, option_type=OptionType.CE, entry_price=5.0, quantity=1, lot_size=1)
    assert payoff_itm == 5.0  # max(0, 110 - 100) - 5 = 5

    payoff_otm = calculate_leg_payoff(spot=90.0, strike=100.0, option_type=OptionType.CE, entry_price=5.0, quantity=1, lot_size=1)
    assert payoff_otm == -5.0  # max(0, 90 - 100) - 5 = -5


def test_bull_call_spread_payoff():
    # Buy Call @ 24000 (price 150), Sell Call @ 24500 (price 40). Net debit = 110
    g_dummy = black_scholes_greeks(24000.0, 24000.0, 0.1, 0.07, 0.20, OptionType.CE)

    leg1 = OptionLeg(strike_price=24000.0, option_type=OptionType.CE, quantity=1, lot_size=25, greeks=g_dummy)
    leg2 = OptionLeg(strike_price=24500.0, option_type=OptionType.CE, quantity=-1, lot_size=25, greeks=g_dummy)

    legs = [leg1, leg2]
    prices = [150.0, 40.0]

    # At 23500 (Below lower strike) -> Max Loss = -110 * 25 = -2750
    p_low = calculate_multi_leg_payoff(23500.0, legs, prices)
    assert p_low == -2750.0

    # At 25000 (Above upper strike) -> Max Profit = (500 - 110) * 25 = 9750
    p_high = calculate_multi_leg_payoff(25000.0, legs, prices)
    assert p_high == 9750.0


def test_strategy_breakevens_and_bounds():
    g_dummy = black_scholes_greeks(24000.0, 24000.0, 0.1, 0.07, 0.20, OptionType.CE)
    leg1 = OptionLeg(strike_price=24000.0, option_type=OptionType.CE, quantity=1, lot_size=25, greeks=g_dummy)
    leg2 = OptionLeg(strike_price=24500.0, option_type=OptionType.CE, quantity=-1, lot_size=25, greeks=g_dummy)

    be, max_p, max_l = calculate_strategy_breakevens_and_bounds("Bull Call Spread", 24000.0, [leg1, leg2], [150.0, 40.0])

    assert len(be) >= 1
    assert abs(be[0] - 24110.0) < 5.0  # K1 + Net Debit = 24000 + 110 = 24110
    assert max_p == 9750.0
    assert max_l == -2750.0


def test_payoff_grid_generation():
    g_dummy = black_scholes_greeks(24000.0, 24000.0, 0.1, 0.07, 0.20, OptionType.CE)
    leg1 = OptionLeg(strike_price=24000.0, option_type=OptionType.CE, quantity=1, lot_size=25, greeks=g_dummy)

    grid = np.linspace(22000.0, 26000.0, 50)
    df = generate_payoff_grid(grid, [leg1], [150.0])

    assert len(df) == 50
    assert "underlying_price" in df.columns
    assert "payoff" in df.columns
