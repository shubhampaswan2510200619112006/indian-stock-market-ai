"""
Unit tests for Black-Scholes European Option Pricing & Closed-Form Greeks.
"""

import numpy as np
import pytest

from src.ingestion.schemas import OptionType
from src.options.pricing import black_scholes_greeks, black_scholes_price


def test_black_scholes_call_price():
    # ATM Call: S=100, K=100, T=1, r=0.05, sigma=0.20
    price = black_scholes_price(spot=100.0, strike=100.0, tte=1.0, r=0.05, sigma=0.20, option_type=OptionType.CE)
    assert abs(price - 10.4506) < 0.05


def test_black_scholes_put_price():
    # ATM Put: S=100, K=100, T=1, r=0.05, sigma=0.20
    price = black_scholes_price(spot=100.0, strike=100.0, tte=1.0, r=0.05, sigma=0.20, option_type=OptionType.PE)
    assert abs(price - 5.5735) < 0.05


def test_put_call_parity():
    """
    Validates Put-Call Parity equation:
    C - P = S * e^(-q*T) - K * e^(-r*T)
    """
    S, K, T, r, sigma, q = 24000.0, 24000.0, 0.25, 0.07, 0.18, 0.01
    call_price = black_scholes_price(S, K, T, r, sigma, OptionType.CE, q)
    put_price = black_scholes_price(S, K, T, r, sigma, OptionType.PE, q)

    parity_lhs = call_price - put_price
    parity_rhs = S * np.exp(-q * T) - K * np.exp(-r * T)

    assert abs(parity_lhs - parity_rhs) < 1e-4, f"Put-Call Parity violated: {parity_lhs:.4f} != {parity_rhs:.4f}"


def test_delta_bounds():
    S, K, T, r, sigma = 100.0, 100.0, 0.5, 0.05, 0.20
    call_g = black_scholes_greeks(S, K, T, r, sigma, OptionType.CE)
    put_g = black_scholes_greeks(S, K, T, r, sigma, OptionType.PE)

    assert 0.0 <= call_g.delta <= 1.0
    assert -1.0 <= put_g.delta <= 0.0
    # Call Delta - Put Delta should equal 1.0 (when q=0)
    assert abs((call_g.delta - put_g.delta) - 1.0) < 1e-5


def test_gamma_positivity_and_atm_peak():
    S, T, r, sigma = 100.0, 0.5, 0.05, 0.20
    g_atm = black_scholes_greeks(S, strike=100.0, tte=T, r=r, sigma=sigma, option_type=OptionType.CE)
    g_otm = black_scholes_greeks(S, strike=130.0, tte=T, r=r, sigma=sigma, option_type=OptionType.CE)

    assert g_atm.gamma > 0.0
    assert g_otm.gamma > 0.0
    assert g_atm.gamma > g_otm.gamma  # Gamma peaks at ATM


def test_vega_behavior():
    S, T, r, sigma = 100.0, 0.5, 0.05, 0.20
    g_atm = black_scholes_greeks(S, strike=100.0, tte=T, r=r, sigma=sigma, option_type=OptionType.CE)
    g_otm = black_scholes_greeks(S, strike=130.0, tte=T, r=r, sigma=sigma, option_type=OptionType.CE)

    assert g_atm.vega > 0.0
    assert g_otm.vega > 0.0
    assert g_atm.vega > g_otm.vega  # Vega peaks at ATM


def test_theta_decay():
    S, K, T, r, sigma = 100.0, 100.0, 0.25, 0.05, 0.20
    g_call = black_scholes_greeks(S, K, T, r, sigma, OptionType.CE)
    g_put = black_scholes_greeks(S, K, T, r, sigma, OptionType.PE)

    # Time decay is negative for long call and long put
    assert g_call.theta < 0.0
    assert g_put.theta < 0.0


def test_rho_behavior():
    S, K, T, r, sigma = 100.0, 100.0, 0.5, 0.05, 0.20
    g_call = black_scholes_greeks(S, K, T, r, sigma, OptionType.CE)
    g_put = black_scholes_greeks(S, K, T, r, sigma, OptionType.PE)

    assert g_call.rho > 0.0
    assert g_put.rho < 0.0


def test_expiry_edge_cases():
    # At expiry (tte = 0)
    call_itm = black_scholes_greeks(spot=110.0, strike=100.0, tte=0.0, r=0.05, sigma=0.20, option_type=OptionType.CE)
    call_otm = black_scholes_greeks(spot=90.0, strike=100.0, tte=0.0, r=0.05, sigma=0.20, option_type=OptionType.CE)

    assert call_itm.delta == 1.0
    assert call_otm.delta == 0.0
    assert call_itm.gamma == 0.0
    assert call_itm.vega == 0.0
