"""
Market Regime Page for Streamlit Dashboard.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from src.features.market_regime import MarketRegimeEngine
from src.ingestion.provider_factory import get_market_data_provider
from src.ingestion.schemas import MarketRegimeType
from src.ingestion.yfinance_provider import YFinanceProvider


def render_market_regime_page():
    """Renders the Market Regime dashboard page."""
    symbol = st.session_state.get("selected_symbol", "NIFTY")

    st.title("🌡 Market Regime Engine")

    provider = get_market_data_provider()
    end_date = date.today()
    start_date = end_date - timedelta(days=150)

    with st.spinner("Evaluating multi-signal market regime..."):
        try:
            nifty_df = provider.get_ohlcv(symbol="NIFTY", start=start_date, end=end_date)
            banknifty_df = None
            try:
                banknifty_df = provider.get_ohlcv(symbol="BANKNIFTY", start=start_date, end=end_date)
            except Exception:
                pass

            vix_val = None
            if isinstance(provider, YFinanceProvider):
                vix_val = provider.get_india_vix()

            engine = MarketRegimeEngine()
            result = engine.evaluate_regime(
                nifty_df=nifty_df,
                banknifty_df=banknifty_df,
                vix_value=vix_val,
                symbol=symbol,
            )
        except Exception as e:
            st.error(f"Could not evaluate market regime: {e}")
            return

    # Color badge mapping
    regime_colors = {
        MarketRegimeType.STRONG_BULL: ("#2e7d32", "🟢 STRONG BULL"),
        MarketRegimeType.BULL: ("#43a047", "🟢 BULL"),
        MarketRegimeType.SIDEWAYS: ("#fb8c00", "🟡 SIDEWAYS"),
        MarketRegimeType.BEAR: ("#e53935", "🔴 BEAR"),
        MarketRegimeType.STRONG_BEAR: ("#c62828", "🔴 STRONG BEAR"),
        MarketRegimeType.HIGH_VOLATILITY: ("#8e24aa", "🟣 HIGH VOLATILITY"),
        MarketRegimeType.UNKNOWN: ("#757575", "⚪ UNKNOWN"),
    }

    color, label = regime_colors.get(result.regime, ("#757575", result.regime.value))

    # Hero card
    st.markdown(
        f"""
        <div style="background-color: {color}22; border: 2px solid {color}; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
            <h2 style="color: {color}; margin: 0;">Market Regime: {label}</h2>
            <p style="font-size: 1.1rem; color: #e0e0e0; margin-top: 5px;">Rule-Based Alignment Score: <strong>{result.confidence*100:.0f}%</strong> <span style="font-size: 0.85em; color: #b0bec5;">(Deterministic Heuristic — Not Empirical Posterior Probability)</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Key Input Metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("NIFTY Trend", result.nifty_trend or "N/A")
    with m2:
        st.metric("BANK NIFTY Trend", result.banknifty_trend or "N/A")
    with m3:
        vix_str = f"{result.vix_value:.2f}" if result.vix_value is not None else "UNAVAILABLE"
        st.metric("India VIX", vix_str)
    with m4:
        breadth = f"{result.breadth_ratio*100:.0f}%" if result.breadth_ratio is not None else "N/A"
        st.metric("Bullish Alignment Ratio", breadth)

    st.divider()

    col_sup, col_conf = st.columns(2)

    with col_sup:
        st.subheader("✅ Supporting Evidence")
        if result.supporting_evidence:
            for item in result.supporting_evidence:
                st.markdown(f"- {item}")
        else:
            st.info("No supporting evidence logged.")

    with col_conf:
        st.subheader("⚠️ Conflicting Evidence")
        if result.conflicting_evidence:
            for item in result.conflicting_evidence:
                st.markdown(f"- {item}")
        else:
            st.success("No conflicting signals present.")

    st.divider()

    st.subheader("🛡 Invalidation & Shift Conditions")
    if result.invalidation_conditions:
        for cond in result.invalidation_conditions:
            st.markdown(f"• **{cond}**")
    else:
        st.info("Standard regime boundaries apply.")

    st.divider()
    st.caption(f"Evaluation Timestamp: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S IST')} | Data Quality: {result.data_quality.value}")
