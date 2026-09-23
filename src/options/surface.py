"""
Volatility Surface Analytics & Expected Move Engine.

CRITICAL DESIGN REQUIREMENTS:
1. Volatility Surface: Computes ATM IV, OTM Put Skew, OTM Call Skew, and Term Structure across expiries.
2. Surface Interpolation: Uses 1D spline / linear interpolation ONLY across known market strikes. Never invents fake contracts.
3. Expected Move Engine: Multi-model expected move calculations distinguishing model-implied, realized-vol, and ATR-based expectations.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from src.ingestion.schemas import DataRecord, OptionChainSnapshot, OptionType


class ExpectedMove(BaseModel):
    """
    Multi-source Expected Move estimation for a given DTE.
    Clearly distinguishes model-implied from historical & ATR expectations.
    """
    underlying: str
    spot_price: float
    expiry_date: date
    dte_days: int

    # 1. Model-Implied Expected Move (Straddle / BS IV)
    model_implied_move_pts: Optional[float] = Field(description="Straddle price approximation or IV * sqrt(T) move in points")
    model_implied_move_pct: Optional[float] = Field(description="Model implied move in %")
    model_implied_upper: Optional[float] = None
    model_implied_lower: Optional[float] = None

    # 2. Historical Realized Vol Expected Move
    historical_rv_move_pts: Optional[float] = Field(description="Expected move using 20D realized volatility")
    historical_rv_move_pct: Optional[float] = None
    historical_rv_upper: Optional[float] = None
    historical_rv_lower: Optional[float] = None

    # 3. ATR Expected Move
    atr_move_pts: Optional[float] = Field(description="Expected move using 14-period ATR * sqrt(DTE)")
    atr_move_pct: Optional[float] = None

    interpretation: str = Field(description="Probabilistic summary of expected price distribution")


class VolatilitySurfaceResult(DataRecord):
    """
    Summary of the Volatility Surface for an underlying asset.
    Includes Skew (Smile) and Term Structure metrics.
    """
    underlying: str
    spot_price: float
    expiry_date: date

    # ATM Implied Volatility
    atm_iv: Optional[float] = None
    atm_iv_ce: Optional[float] = None
    atm_iv_pe: Optional[float] = None

    # Volatility Skew (Difference from ATM IV)
    otm_put_skew: Optional[float] = Field(default=None, description="IV(90% Strike Put) - ATM IV")
    otm_call_skew: Optional[float] = Field(default=None, description="IV(110% Strike Call) - ATM IV")
    skew_ratio: Optional[float] = Field(default=None, description="Put IV / Call IV ratio")

    # Curve Data by Strike
    strikes: list[float] = Field(default_factory=list)
    iv_calls: list[Optional[float]] = Field(default_factory=list)
    iv_puts: list[Optional[float]] = Field(default_factory=list)

    # Term Structure (ATM IV across available expiries)
    term_structure: dict[str, Optional[float]] = Field(default_factory=dict)  # {"2026-09-25": 0.155}


def compute_volatility_surface(
    chain_data: OptionChainSnapshot,
    term_structure_chains: Optional[list[OptionChainSnapshot]] = None,
) -> VolatilitySurfaceResult:
    """
    Extracts ATM IV, OTM Put Skew, OTM Call Skew, and Term Structure from chain data.
    """
    spot = chain_data.spot_price
    exp = chain_data.expiry_date

    if not chain_data.strikes or spot <= 0:
        return VolatilitySurfaceResult(
            underlying=chain_data.underlying,
            spot_price=spot,
            expiry_date=exp,
            timestamp=chain_data.timestamp,
            source="surface_engine",
        )

    strikes_list = []
    iv_ce_list = []
    iv_pe_list = []

    atm_strike = min(chain_data.strikes, key=lambda s: abs(s.strike_price - spot)).strike_price
    atm_iv_ce = None
    atm_iv_pe = None

    put_90_iv = None
    call_110_iv = None

    target_put_strike = spot * 0.90
    target_call_strike = spot * 1.10

    closest_put_dist = float("inf")
    closest_call_dist = float("inf")

    for row in sorted(chain_data.strikes, key=lambda x: x.strike_price):
        k = row.strike_price
        strikes_list.append(k)

        ce_iv = row.ce.implied_volatility if row.ce else None
        pe_iv = row.pe.implied_volatility if row.pe else None

        iv_ce_list.append(ce_iv)
        iv_pe_list.append(pe_iv)

        if k == atm_strike:
            atm_iv_ce = ce_iv
            atm_iv_pe = pe_iv

        # Closest 90% Put Strike
        if pe_iv is not None and abs(k - target_put_strike) < closest_put_dist:
            closest_put_dist = abs(k - target_put_strike)
            put_90_iv = pe_iv

        # Closest 110% Call Strike
        if ce_iv is not None and abs(k - target_call_strike) < closest_call_dist:
            closest_call_dist = abs(k - target_call_strike)
            call_110_iv = ce_iv

    # Calculate composite ATM IV
    valid_atm = [v for v in [atm_iv_ce, atm_iv_pe] if v is not None and v > 0]
    atm_iv = float(np.mean(valid_atm)) if valid_atm else None

    otm_put_skew = (put_90_iv - atm_iv) if (put_90_iv is not None and atm_iv is not None) else None
    otm_call_skew = (call_110_iv - atm_iv) if (call_110_iv is not None and atm_iv is not None) else None
    skew_ratio = (put_90_iv / call_110_iv) if (put_90_iv is not None and call_110_iv is not None and call_110_iv > 0) else None

    # Term Structure
    term_struct = {}
    if term_structure_chains:
        for c in term_structure_chains:
            c_atm = min(c.strikes, key=lambda s: abs(s.strike_price - c.spot_price)) if c.strikes else None
            c_ivs = []
            if c_atm:
                if c_atm.ce and c_atm.ce.implied_volatility:
                    c_ivs.append(c_atm.ce.implied_volatility)
                if c_atm.pe and c_atm.pe.implied_volatility:
                    c_ivs.append(c_atm.pe.implied_volatility)
            term_struct[c.expiry_date.isoformat()] = float(np.mean(c_ivs)) if c_ivs else None

    return VolatilitySurfaceResult(
        underlying=chain_data.underlying,
        spot_price=spot,
        expiry_date=exp,
        timestamp=chain_data.timestamp,
        source="surface_engine",
        atm_iv=atm_iv,
        atm_iv_ce=atm_iv_ce,
        atm_iv_pe=atm_iv_pe,
        otm_put_skew=otm_put_skew,
        otm_call_skew=otm_call_skew,
        skew_ratio=skew_ratio,
        strikes=strikes_list,
        iv_calls=iv_ce_list,
        iv_puts=iv_pe_list,
        term_structure=term_struct,
    )


def compute_expected_move(
    spot: float,
    expiry_date: date,
    atm_iv: Optional[float] = None,
    realized_vol_20d: Optional[float] = None,
    atr_14: Optional[float] = None,
    current_date: Optional[date] = None,
    underlying: str = "NIFTY",
) -> ExpectedMove:
    """
    Computes Expected Move across multiple models:
    - Model-Implied: Spot * ATM_IV * sqrt(DTE / 365)
    - Realized Vol: Spot * RV20 * sqrt(DTE / 365)
    - ATR: ATR14 * sqrt(DTE)
    """
    today = current_date or date.today()
    dte_days = max(1, (expiry_date - today).days)
    tte_years = dte_days / 365.0
    sqrt_tte = np.sqrt(tte_years)

    # 1. Model-Implied
    model_pts = (spot * atm_iv * sqrt_tte) if (atm_iv is not None and atm_iv > 0) else None
    model_pct = (model_pts / spot * 100.0) if model_pts is not None else None
    model_upper = (spot + model_pts) if model_pts is not None else None
    model_lower = (spot - model_pts) if model_pts is not None else None

    # 2. Historical Realized Vol
    rv_pts = (spot * realized_vol_20d * sqrt_tte) if (realized_vol_20d is not None and realized_vol_20d > 0) else None
    rv_pct = (rv_pts / spot * 100.0) if rv_pts is not None else None
    rv_upper = (spot + rv_pts) if rv_pts is not None else None
    rv_lower = (spot - rv_pts) if rv_pts is not None else None

    # 3. ATR
    atr_pts = (atr_14 * np.sqrt(dte_days)) if (atr_14 is not None and atr_14 > 0) else None
    atr_pct = (atr_pts / spot * 100.0) if atr_pts is not None else None

    interp = f"Expect 1-sigma price movement of +/-{model_pts:.2f} pts (+/-{model_pct:.2f}%) by expiry {expiry_date}." if model_pts else "Insufficient data to compute model-implied expected move."

    return ExpectedMove(
        underlying=underlying,
        spot_price=spot,
        expiry_date=expiry_date,
        dte_days=dte_days,
        model_implied_move_pts=model_pts,
        model_implied_move_pct=model_pct,
        model_implied_upper=model_upper,
        model_implied_lower=model_lower,
        historical_rv_move_pts=rv_pts,
        historical_rv_move_pct=rv_pct,
        historical_rv_upper=rv_upper,
        historical_rv_lower=rv_lower,
        atr_move_pts=atr_pts,
        atr_move_pct=atr_pct,
        interpretation=interp,
    )
