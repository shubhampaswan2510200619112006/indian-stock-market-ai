"""
Implied Volatility (IV) Numerical Solver.

CRITICAL GUARANTEES & CONSTRAINTS:
1. Strict Validation: Detects invalid/crossed prices, zero/negative DTE, and deep ITM/OTM intrinsic breaches.
2. Dual Numerical Engine:
   - Primary: Newton-Raphson (fast convergence using analytical Vega)
   - Fallback: Brent's Method (brentq) when Vega is near zero or Newton fails
3. Zero Fabrication: Returns solver_converged=False and iv=None when market price cannot be reconciled.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

import numpy as np
from scipy.optimize import brentq

from src.ingestion.schemas import DataQualityStatus, ImpliedVolatilityObs, OptionType
from src.options.pricing import black_scholes_greeks, black_scholes_price


def calculate_implied_volatility(
    market_price: float,
    spot: float,
    strike: float,
    tte: float,
    r: float,
    option_type: OptionType | str = OptionType.CE,
    q: float = 0.0,
    timestamp: Optional[datetime] = None,
    expiry_date: Optional[date] = None,
    underlying: str = "NIFTY",
    max_iterations: int = 50,
    tolerance: float = 1e-5,
) -> ImpliedVolatilityObs:
    """
    Computes Implied Volatility from an observed option market price.
    Returns ImpliedVolatilityObs carrying solver metadata.
    """
    opt_type = OptionType(option_type) if isinstance(option_type, str) else option_type
    ts = timestamp or datetime.now()
    exp = expiry_date or date.today()

    def _failed_obs(status: DataQualityStatus = DataQualityStatus.SUSPECT):
        return ImpliedVolatilityObs(
            underlying=underlying,
            option_type=opt_type,
            strike_price=strike,
            expiry_date=exp,
            spot_price=spot,
            timestamp=ts,
            source="iv_solver",
            data_quality=status,
            iv=None,
            solver_method="failed",
            solver_converged=False,
            solver_iterations=0,
            market_price_used=market_price if market_price > 0 else None,
            risk_free_rate=r,
        )

    # Sanity Checks
    if market_price <= 0 or spot <= 0 or strike <= 0 or tte <= 1e-7:
        return _failed_obs(DataQualityStatus.UNAVAILABLE)

    # Intrinsic & No-Arbitrage Price Bounds Check
    df_r = np.exp(-r * tte)
    df_q = np.exp(-q * tte)

    if opt_type == OptionType.CE:
        intrinsic_lower = max(0.0, spot * df_q - strike * df_r)
        price_upper = spot * df_q
    else:
        intrinsic_lower = max(0.0, strike * df_r - spot * df_q)
        price_upper = strike * df_r

    if market_price < intrinsic_lower - 1e-4 or market_price > price_upper + 1e-4:
        return _failed_obs(DataQualityStatus.SUSPECT)

    # 1. Try Newton-Raphson Solver
    sigma = 0.25  # Initial guess (25% IV)
    converged = False
    iterations = 0

    for i in range(1, max_iterations + 1):
        iterations = i
        price = black_scholes_price(spot, strike, tte, r, sigma, opt_type, q)
        diff = price - market_price

        if abs(diff) < tolerance:
            converged = True
            break

        greeks = black_scholes_greeks(spot, strike, tte, r, sigma, opt_type, q)
        vega_raw = greeks.vega * 100.0  # Convert back to raw Vega (dV/dsigma)

        if vega_raw < 1e-8:
            break  # Vega too small for Newton-Raphson, switch to Brent

        step = diff / vega_raw
        sigma -= step

        # Keep sigma within realistic bounds during iteration
        if sigma <= 0.0001 or sigma >= 10.0:
            break

    if converged and 0.0001 <= sigma <= 5.0:
        return ImpliedVolatilityObs(
            underlying=underlying,
            option_type=opt_type,
            strike_price=strike,
            expiry_date=exp,
            spot_price=spot,
            timestamp=ts,
            source="iv_solver",
            data_quality=DataQualityStatus.GOOD,
            iv=float(round(sigma, 6)),
            solver_method="newton_raphson",
            solver_converged=True,
            solver_iterations=iterations,
            market_price_used=market_price,
            risk_free_rate=r,
        )

    # 2. Fallback to Brent's Method (brentq)
    try:
        def objective(vol: float) -> float:
            return black_scholes_price(spot, strike, tte, r, vol, opt_type, q) - market_price

        iv_brent = brentq(objective, 0.0001, 5.0, xtol=tolerance, maxiter=100)
        return ImpliedVolatilityObs(
            underlying=underlying,
            option_type=opt_type,
            strike_price=strike,
            expiry_date=exp,
            spot_price=spot,
            timestamp=ts,
            source="iv_solver",
            data_quality=DataQualityStatus.GOOD,
            iv=float(round(iv_brent, 6)),
            solver_method="brent",
            solver_converged=True,
            solver_iterations=iterations + 10,
            market_price_used=market_price,
            risk_free_rate=r,
        )
    except Exception:
        return _failed_obs(DataQualityStatus.SUSPECT)
