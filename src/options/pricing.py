"""
Black-Scholes European Option Pricing & Closed-Form Greeks Engine.

CRITICAL DESIGN & MATHEMATICAL PRINCIPLES:
1. Exact closed-form Black-Scholes equations for European Options.
2. Standardized Greek Units:
   - Delta: dV/dS (dimensionless, [-1.0, 1.0])
   - Gamma: d^2V/dS^2 (per point squared)
   - Theta: dV/dt expressed as 1 calendar day decay (Theta_annual / 365.0)
   - Vega: dV/d(sigma) expressed per 1 percentage point change in volatility (Vega_raw / 100.0)
   - Rho: dV/dr expressed per 1 percentage point change in risk-free rate (Rho_raw / 100.0)
3. Robust edge case handling:
   - T <= 0 (at/past expiry): Exact intrinsic value, zero time value, step-function Delta.
   - sigma <= 0: Discounted intrinsic value.
   - S <= 0 or K <= 0: Clean failure / return 0.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

import numpy as np
from scipy.stats import norm

from src.ingestion.schemas import DataQualityStatus, GreeksObservation, OptionType


def black_scholes_price(
    spot: float,
    strike: float,
    tte: float,  # Time to expiry in years (e.g. DTE / 365.0)
    r: float,    # Risk-free rate (e.g. 0.07 for 7%)
    sigma: float,# Volatility (e.g. 0.20 for 20%)
    option_type: OptionType | str = OptionType.CE,
    q: float = 0.0, # Dividend yield
) -> float:
    """
    Computes Black-Scholes price for European Call or Put.
    """
    if spot <= 0 or strike <= 0:
        return 0.0

    opt_type = OptionType(option_type) if isinstance(option_type, str) else option_type

    # Expiry or zero time edge case
    if tte <= 1e-7:
        if opt_type == OptionType.CE:
            return float(max(0.0, spot - strike))
        else:
            return float(max(0.0, strike - spot))

    # Zero volatility edge case
    if sigma <= 1e-7:
        df_r = np.exp(-r * tte)
        df_q = np.exp(-q * tte)
        if opt_type == OptionType.CE:
            return float(max(0.0, spot * df_q - strike * df_r))
        else:
            return float(max(0.0, strike * df_r - spot * df_q))

    sqrt_t = np.sqrt(tte)
    d1 = (np.log(spot / strike) + (r - q + 0.5 * sigma**2) * tte) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t

    df_r = np.exp(-r * tte)
    df_q = np.exp(-q * tte)

    if opt_type == OptionType.CE:
        price = spot * df_q * norm.cdf(d1) - strike * df_r * norm.cdf(d2)
    else:
        price = strike * df_r * norm.cdf(-d2) - spot * df_q * norm.cdf(-d1)

    return float(max(0.0, price))


def black_scholes_greeks(
    spot: float,
    strike: float,
    tte: float,
    r: float,
    sigma: float,
    option_type: OptionType | str = OptionType.CE,
    q: float = 0.0,
    timestamp: Optional[datetime] = None,
    expiry_date: Optional[date] = None,
    underlying: str = "NIFTY",
) -> GreeksObservation:
    """
    Computes closed-form Black-Scholes Greeks: Delta, Gamma, Theta (1-day), Vega (1%), Rho (1%).
    """
    opt_type = OptionType(option_type) if isinstance(option_type, str) else option_type
    ts = timestamp or datetime.now()
    exp = expiry_date or date.today()

    # Default result container for edge cases
    def _make_obs(d: float, g: float, t: float, v: float, rh: float):
        return GreeksObservation(
            underlying=underlying,
            option_type=opt_type,
            strike_price=strike,
            expiry_date=exp,
            spot_price=spot,
            timestamp=ts,
            source="bs_engine",
            data_quality=DataQualityStatus.GOOD,
            delta=float(d),
            gamma=float(g),
            theta=float(t),
            vega=float(v),
            rho=float(rh),
            pricing_model="black_scholes",
            iv_used=float(sigma),
            risk_free_rate=float(r),
        )

    # Edge Case: At or past expiry
    if tte <= 1e-7:
        if opt_type == OptionType.CE:
            d = 1.0 if spot > strike else (0.5 if spot == strike else 0.0)
        else:
            d = -1.0 if spot < strike else (-0.5 if spot == strike else 0.0)
        return _make_obs(d=d, g=0.0, t=0.0, v=0.0, rh=0.0)

    # Edge Case: Zero or invalid volatility / price
    if sigma <= 1e-7 or spot <= 0 or strike <= 0:
        if opt_type == OptionType.CE:
            d = 1.0 if spot > strike else 0.0
        else:
            d = -1.0 if spot < strike else 0.0
        return _make_obs(d=d, g=0.0, t=0.0, v=0.0, rh=0.0)

    sqrt_t = np.sqrt(tte)
    d1 = (np.log(spot / strike) + (r - q + 0.5 * sigma**2) * tte) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t

    df_r = np.exp(-r * tte)
    df_q = np.exp(-q * tte)
    pdf_d1 = norm.pdf(d1)

    # Delta
    if opt_type == OptionType.CE:
        delta = df_q * norm.cdf(d1)
    else:
        delta = -df_q * norm.cdf(-d1)

    # Gamma (Identical for Call and Put)
    gamma = (df_q * pdf_d1) / (spot * sigma * sqrt_t)

    # Theta (Annualized -> per calendar day)
    term1 = -(spot * df_q * pdf_d1 * sigma) / (2.0 * sqrt_t)
    if opt_type == OptionType.CE:
        theta_annual = term1 - r * strike * df_r * norm.cdf(d2) + q * spot * df_q * norm.cdf(d1)
    else:
        theta_annual = term1 + r * strike * df_r * norm.cdf(-d2) - q * spot * df_q * norm.cdf(-d1)
    theta_daily = theta_annual / 365.0

    # Vega (Per 1% change in volatility)
    vega_raw = spot * df_q * pdf_d1 * sqrt_t
    vega_1pct = vega_raw / 100.0

    # Rho (Per 1% change in risk-free rate)
    if opt_type == OptionType.CE:
        rho_raw = strike * tte * df_r * norm.cdf(d2)
    else:
        rho_raw = -strike * tte * df_r * norm.cdf(-d2)
    rho_1pct = rho_raw / 100.0

    return _make_obs(d=delta, g=gamma, t=theta_daily, v=vega_1pct, rh=rho_1pct)
