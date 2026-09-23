"""
Unit tests for Implied Volatility Solver.
"""

import pytest

from src.ingestion.schemas import OptionType
from src.options.iv_solver import calculate_implied_volatility
from src.options.pricing import black_scholes_price


def test_iv_solver_roundtrip_call():
    """Price -> IV -> Price round-trip verification for Call."""
    spot, strike, tte, r, true_vol = 24000.0, 24000.0, 0.1, 0.07, 0.185
    market_price = black_scholes_price(spot, strike, tte, r, true_vol, OptionType.CE)

    obs = calculate_implied_volatility(market_price, spot, strike, tte, r, OptionType.CE)
    assert obs.solver_converged is True
    assert obs.iv is not None
    assert abs(obs.iv - true_vol) < 1e-4

    # Price back using solved IV
    recalculated_price = black_scholes_price(spot, strike, tte, r, obs.iv, OptionType.CE)
    assert abs(recalculated_price - market_price) < 1e-3


def test_iv_solver_roundtrip_put():
    """Price -> IV -> Price round-trip verification for Put."""
    spot, strike, tte, r, true_vol = 24000.0, 23500.0, 0.1, 0.07, 0.22
    market_price = black_scholes_price(spot, strike, tte, r, true_vol, OptionType.PE)

    obs = calculate_implied_volatility(market_price, spot, strike, tte, r, OptionType.PE)
    assert obs.solver_converged is True
    assert obs.iv is not None
    assert abs(obs.iv - true_vol) < 1e-4


def test_iv_solver_invalid_price_intrinsic_breach():
    """
    If call market price is below intrinsic value, solver MUST fail safely
    and return solver_converged=False without fabricating fake IV!
    """
    spot, strike, tte, r = 100.0, 80.0, 0.5, 0.05
    # Intrinsic value for call is max(0, S - K*exp(-r*T)) = 100 - 80*exp(-0.025) = 21.97
    invalid_price = 10.0  # Violation of no-arbitrage bound!

    obs = calculate_implied_volatility(invalid_price, spot, strike, tte, r, OptionType.CE)
    assert obs.solver_converged is False
    assert obs.iv is None


def test_iv_solver_zero_dte():
    """Zero DTE must fail safely without division by zero errors."""
    obs = calculate_implied_volatility(10.0, 100.0, 100.0, 0.0, 0.05, OptionType.CE)
    assert obs.solver_converged is False
    assert obs.iv is None


def test_iv_solver_negative_price():
    """Negative option price must return solver_converged=False."""
    obs = calculate_implied_volatility(-5.0, 100.0, 100.0, 0.2, 0.05, OptionType.CE)
    assert obs.solver_converged is False
    assert obs.iv is None
