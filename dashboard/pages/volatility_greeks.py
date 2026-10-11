"""
Options Volatility & Greeks Page for Streamlit Dashboard.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on Python path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


from datetime import date, datetime, timedelta

import numpy as np
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from src.features.volatility import calculate_realized_volatility
from src.ingestion.base import DataUnavailableError
from src.ingestion.provider_factory import get_market_data_provider, get_options_provider
from src.options.iv_solver import calculate_implied_volatility
from src.options.pricing import black_scholes_greeks
from src.options.surface import compute_expected_move, compute_volatility_surface
from dashboard.components.data_quality import render_freshness_badge, render_provider_info


def render_volatility_greeks_page():
    """Renders the Options Volatility & Greeks page."""
    symbol = st.session_state.get("selected_symbol", "NIFTY")

    st.title(f"⚡ Options Volatility & Greeks — {symbol}")

    options_provider = get_options_provider()
    market_provider = get_market_data_provider()

    # Expiry selector
    with st.spinner("Fetching available expiry dates..."):
        try:
            expiries = options_provider.get_expiry_dates(symbol)
        except DataUnavailableError as e:
            st.error(f"Option data unavailable for {symbol}: {e}")
            return
        except Exception as e:
            st.error(f"Could not load expiries: {e}")
            return

    if not expiries:
        st.warning(f"No active option expiries found for {symbol}.")
        return

    col_exp, col_r = st.columns([3, 2])
    with col_exp:
        selected_expiry = st.selectbox(
            "Select Expiry Date",
            expiries,
            format_func=lambda d: d.strftime("%d %b %Y"),
        )
    with col_r:
        r_rate = st.number_input("Risk-Free Rate (r)", min_value=0.0, max_value=0.20, value=0.07, step=0.005, format="%.3f")

    # Fetch option chain data
    with st.spinner(f"Loading Option Chain for {selected_expiry}..."):
        try:
            snapshot = options_provider.get_option_chain(symbol, selected_expiry)
        except Exception as e:
            st.error(f"Error loading option chain: {e}")
            return

    render_freshness_badge(snapshot.timestamp, "Options Quote Feed")
    render_provider_info(options_provider.provider_name)
    st.divider()

    spot = snapshot.spot_price
    today = date.today()
    dte = max(1, (selected_expiry - today).days)
    tte = dte / 365.0

    # Compute Volatility Surface & ATM IV
    surface = compute_volatility_surface(snapshot)
    atm_iv = surface.atm_iv

    # Fetch historical data for 20D Realized Volatility
    end_d = date.today()
    start_d = end_d - timedelta(days=60)
    rv_20d = None
    try:
        hist_df = market_provider.get_ohlcv(symbol, start=start_d, end=end_d)
        if not hist_df.empty and "close" in hist_df.columns:
            rv_20d = calculate_realized_volatility(hist_df["close"], window=20)
    except Exception:
        pass

    # Expected Move Card
    exp_move = compute_expected_move(
        spot=spot,
        expiry_date=selected_expiry,
        atm_iv=atm_iv,
        realized_vol_20d=rv_20d,
        underlying=symbol,
    )

    st.subheader("🎯 Expected Move Estimation")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Spot Price", f"₹{spot:,.2f}")
    with m2:
        m_str = f"±{exp_move.model_implied_move_pts:.1f} pts (±{exp_move.model_implied_move_pct:.1f}%)" if exp_move.model_implied_move_pts else "N/A"
        st.metric("Model Implied Move (1-sigma)", m_str)
    with m3:
        range_str = f"₹{exp_move.model_implied_lower:,.0f} - ₹{exp_move.model_implied_upper:,.0f}" if exp_move.model_implied_upper else "N/A"
        st.metric("Implied Range", range_str)
    with m4:
        rv_str = f"±{exp_move.historical_rv_move_pts:.1f} pts (±{exp_move.historical_rv_move_pct:.1f}%)" if exp_move.historical_rv_move_pts else "N/A"
        st.metric("20D Realized Vol Move", rv_str)

    st.divider()

    # Volatility Skew Chart
    st.subheader("📉 Volatility Skew & Smile")
    if surface.strikes and (surface.iv_calls or surface.iv_puts):
        fig_skew = go.Figure()
        valid_calls = [(k, iv*100) for k, iv in zip(surface.strikes, surface.iv_calls) if iv is not None]
        valid_puts = [(k, iv*100) for k, iv in zip(surface.strikes, surface.iv_puts) if iv is not None]

        if valid_calls:
            fig_skew.add_trace(go.Scatter(x=[x[0] for x in valid_calls], y=[x[1] for x in valid_calls], name="Call IV (%)", line=dict(color="#42a5f5", width=2)))
        if valid_puts:
            fig_skew.add_trace(go.Scatter(x=[x[0] for x in valid_puts], y=[x[1] for x in valid_puts], name="Put IV (%)", line=dict(color="#ff7043", width=2)))

        fig_skew.add_vline(x=spot, line_dash="dash", line_color="#ffee58", annotation_text=f"Spot: {spot:,.2f}")
        fig_skew.update_layout(
            template="plotly_dark",
            height=400,
            xaxis_title="Strike Price",
            yaxis_title="Implied Volatility (%)",
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(fig_skew, use_container_width=True)

    # Chain-wide Greeks Calculation Table
    st.subheader("📋 Option Chain Greeks & Implied Volatility Table")

    chain_rows = []
    for row in snapshot.strikes:
        k = row.strike_price

        # CE side
        ce_price = row.ce.last_price if row.ce else None
        ce_iv_obs = calculate_implied_volatility(ce_price, spot, k, tte, r_rate, OptionType.CE) if ce_price else None
        ce_iv = ce_iv_obs.iv if (ce_iv_obs and ce_iv_obs.solver_converged) else (row.ce.implied_volatility if row.ce else None)
        ce_greeks = black_scholes_greeks(spot, k, tte, r_rate, ce_iv or 0.20, OptionType.CE) if (ce_iv and ce_iv > 0) else None

        # PE side
        pe_price = row.pe.last_price if row.pe else None
        pe_iv_obs = calculate_implied_volatility(pe_price, spot, k, tte, r_rate, OptionType.PE) if pe_price else None
        pe_iv = pe_iv_obs.iv if (pe_iv_obs and pe_iv_obs.solver_converged) else (row.pe.implied_volatility if row.pe else None)
        pe_greeks = black_scholes_greeks(spot, k, tte, r_rate, pe_iv or 0.20, OptionType.PE) if (pe_iv and pe_iv > 0) else None

        chain_rows.append({
            "CE Delta": f"{ce_greeks.delta:.3f}" if ce_greeks else "N/A",
            "CE Gamma": f"{ce_greeks.gamma:.4f}" if ce_greeks else "N/A",
            "CE Theta": f"{ce_greeks.theta:.2f}" if ce_greeks else "N/A",
            "CE Vega": f"{ce_greeks.vega:.2f}" if ce_greeks else "N/A",
            "CE IV": f"{ce_iv*100:.1f}%" if ce_iv else "N/A",
            "CE Price": f"₹{ce_price:.2f}" if ce_price else "N/A",
            "Strike": f"{k:,.0f}",
            "PE Price": f"₹{pe_price:.2f}" if pe_price else "N/A",
            "PE IV": f"{pe_iv*100:.1f}%" if pe_iv else "N/A",
            "PE Delta": f"{pe_greeks.delta:.3f}" if pe_greeks else "N/A",
            "PE Gamma": f"{pe_greeks.gamma:.4f}" if pe_greeks else "N/A",
            "PE Theta": f"{pe_greeks.theta:.2f}" if pe_greeks else "N/A",
            "PE Vega": f"{pe_greeks.vega:.2f}" if pe_greeks else "N/A",
        })

    if chain_rows:
        st.dataframe(pd.DataFrame(chain_rows), use_container_width=True)

    st.caption("ℹ Greeks & IV observations are mathematically computed at timestamp T. Values are unavailable (N/A) when market prices violate intrinsic bounds.")

if __name__ == "__main__":
    st.set_page_config(page_title="Volatility Greeks", layout="wide")
    render_volatility_greeks_page()

