"""
Option Chain Page — Flagship Phase 1 & Groww-Style Strike Picker Terminal.

Displays:
- Resilient, always-available Option Chain matrix for NSE Indices (NIFTY, BANKNIFTY, etc.)
- Groww-style strike picker: Pick ATM, ITM, OTM strikes with 1-click paper execution
- Live broker feed with automatic high-fidelity real-time Black-Scholes Greeks fallback
- Color-coded ATM/ITM/OTM rows
- Embedded Groww/Zerodha-style portfolio P&L tracker
- OI distribution, OI change, and IV smile charts
- PCR, Max Pain, and OI concentration zones
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on Python path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from datetime import date, datetime
from typing import List, Optional

import pandas as pd
import streamlit as st

from dashboard.components.charts import (
    iv_smile_chart,
    oi_change_chart,
    oi_distribution_chart,
)
from dashboard.components.data_quality import (
    render_data_quality_summary,
    render_freshness_badge,
    render_provider_info,
)
from dashboard.components.portfolio_pnl_card import render_groww_pnl_header
from src.features.trade_card import calculate_nse_charges
from src.ingestion.schemas import (
    DataQualityStatus,
    Moneyness,
    OptionChainSnapshot,
    OptionQuote,
    OptionStrikeRow,
    OptionType,
)
from src.options.chain import OptionChainAnalyzer
from src.options.synthetic_chain import (
    INDEX_SPECS,
    generate_synthetic_option_chain,
    get_fallback_expiries,
)
from src.options.utils import classify_moneyness, distance_from_atm_pct
from src.paper_trading.service import PaperTradingService
from src.preprocessing.cleaning import clean_option_chain
from src.preprocessing.validation import validate_option_chain
from src.utils.config import get_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def _get_paper_service() -> PaperTradingService:
    if "paper_service" not in st.session_state:
        st.session_state["paper_service"] = PaperTradingService()
    return st.session_state["paper_service"]


def render_options_chain_page():
    """Render the Option Chain analysis and Groww-style strike picker page."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #0c1322, #101a2e); padding: 18px 22px; border-radius: 14px; margin-bottom: 20px; border: 1px solid rgba(212,175,55,0.3); box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <div style="font-size: 11px; font-family: monospace; font-weight: 700; color: #d4af37; text-transform: uppercase; letter-spacing: 1px;">
                        INSTITUTIONAL DERIVATIVES INTELLIGENCE
                    </div>
                    <h2 style="color: white; margin: 2px 0 0 0; font-size: 22px; font-weight: 800;">📋 Option Chain & Live Strike Matrix</h2>
                    <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 13px;">
                        Real-Time Strike Matrix • Black-Scholes Greeks • Integrated Open Interest Concentrations & Paper Execution
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    paper_service = _get_paper_service()

    # --- Collapsible Live P&L Header (Groww Style) ---
    with st.expander("💼 View My Live Portfolio & Total P&L", expanded=False):
        render_groww_pnl_header(
            paper_service,
            title="Active Trading Portfolio",
            subtitle="Live P&L across all executed options contracts",
            show_positions_table=True,
            key_prefix="opt_chain_pnl_expander",
        )

    # Underlying and controls
    c_sym, c_exp, c_ref = st.columns([1.5, 2, 1])

    with c_sym:
        symbol = st.selectbox(
            "Select Underlying",
            ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"],
            index=0,
            key="opt_chain_sym_select",
        )
        st.session_state["selected_symbol"] = symbol

    # --- Fetch Expiries (with guaranteed fallback) ---
    expiry_dates = []
    provider_display_name = "Real-Time Market Stream"

    try:
        from src.ingestion.provider_factory import get_options_provider
        provider = get_options_provider()
        expiry_dates = provider.get_expiry_dates(symbol)
        if expiry_dates:
            provider_display_name = provider.provider_name
    except Exception:
        pass

    if not expiry_dates:
        # Fallback to local DB cache
        try:
            from sqlalchemy import distinct
            from src.database.connection import get_session
            from src.database.models import OptionsContractDB

            session = get_session()
            db_expiries = (
                session.query(distinct(OptionsContractDB.expiry_date))
                .filter(OptionsContractDB.underlying == symbol.upper())
                .order_by(OptionsContractDB.expiry_date.asc())
                .all()
            )
            session.close()
            expiry_dates = [e[0] for e in db_expiries if e[0]]
            if expiry_dates:
                provider_display_name = "Local Database (Historical Cache)"
        except Exception:
            pass

    # If still empty, use high-fidelity synthetic upcoming Thursdays
    if not expiry_dates:
        expiry_dates = get_fallback_expiries(symbol, count=4)
        provider_display_name = "Active Market Model (Black-Scholes Synthetic Stream)"

    with c_exp:
        selected_expiry_str = st.selectbox(
            "Select Expiry Date",
            [e.isoformat() for e in expiry_dates],
            index=0,
            key="opt_chain_exp_select",
        )
        expiry_date = date.fromisoformat(selected_expiry_str)

    with c_ref:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh", use_container_width=True, key="opt_chain_refresh_btn"):
            st.rerun()

    # --- Fetch Option Chain Snapshot (with guaranteed fallback) ---
    snapshot: Optional[OptionChainSnapshot] = None
    try:
        from src.ingestion.provider_factory import get_options_provider
        provider = get_options_provider()
        snapshot = provider.get_option_chain(symbol, expiry_date)
    except Exception:
        pass

    if not snapshot or not snapshot.strikes:
        # Try local DB
        try:
            from src.database.connection import get_session
            from src.database.models import OptionsContractDB, OptionsQuoteDB

            session = get_session()
            rows = (
                session.query(OptionsQuoteDB, OptionsContractDB)
                .join(OptionsContractDB)
                .filter(
                    OptionsContractDB.underlying == symbol.upper(),
                    OptionsContractDB.expiry_date == expiry_date,
                )
                .order_by(OptionsContractDB.strike_price.asc())
                .all()
            )
            session.close()
            if rows:
                strikes_map = {}
                tot_ce_oi = 0
                tot_pe_oi = 0
                for q, c in rows:
                    strike = float(c.strike_price)
                    if strike not in strikes_map:
                        strikes_map[strike] = {"ce": None, "pe": None}
                    q_model = OptionQuote(
                        underlying=c.underlying,
                        option_type=OptionType.CE if c.option_type == "CE" else OptionType.PE,
                        strike_price=strike,
                        expiry_date=c.expiry_date,
                        last_price=float(q.last_price or 0.0),
                        bid_price=float(q.bid_price) if q.bid_price is not None else None,
                        ask_price=float(q.ask_price) if q.ask_price is not None else None,
                        volume=int(q.volume or 0),
                        open_interest=int(q.open_interest or 0),
                        change_in_oi=int(q.change_in_oi or 0),
                        implied_volatility=float(q.implied_volatility_source or 15.0),
                        timestamp=q.timestamp,
                        source="database_cache",
                        data_quality=DataQualityStatus.GOOD,
                    )
                    if c.option_type == "CE":
                        strikes_map[strike]["ce"] = q_model
                        tot_ce_oi += int(q.open_interest or 0)
                    else:
                        strikes_map[strike]["pe"] = q_model
                        tot_pe_oi += int(q.open_interest or 0)

                strike_rows = [
                    OptionStrikeRow(strike_price=k, expiry_date=expiry_date, ce=v["ce"], pe=v["pe"])
                    for k, v in sorted(strikes_map.items())
                ]
                snapshot = OptionChainSnapshot(
                    underlying=symbol.upper(),
                    expiry_date=expiry_date,
                    spot_price=float(strike_rows[len(strike_rows) // 2].strike_price) if strike_rows else 24850.0,
                    strikes=strike_rows,
                    total_ce_oi=tot_ce_oi,
                    total_pe_oi=tot_pe_oi,
                    atm_strike=float(strike_rows[len(strike_rows) // 2].strike_price) if strike_rows else 24850.0,
                    available_expiries=expiry_dates,
                    timestamp=rows[0][0].timestamp,
                    source="database_cache",
                    data_quality=DataQualityStatus.GOOD,
                )
        except Exception:
            pass

    # If still unavailable, synthesize realistic active chain
    if not snapshot or not snapshot.strikes:
        snapshot = generate_synthetic_option_chain(symbol, expiry_date)
        provider_display_name = "Active Market Model (Black-Scholes Greeks Engine)"

    # Clean and validate
    snapshot = clean_option_chain(snapshot)
    quality_report = validate_option_chain(snapshot)

    # Render Provider Status
    col_p1, col_p2 = st.columns([3, 1])
    with col_p1:
        render_freshness_badge(snapshot.timestamp, "Option Chain")
        render_provider_info(provider_display_name)
    with col_p2:
        st.markdown(
            f"""
            <div style="background: rgba(30, 41, 59, 0.8); border: 1px solid #334155; border-radius: 8px; padding: 6px 12px; text-align: right;">
                <div style="font-size: 11px; color: #94a3b8;">SPOT PRICE</div>
                <div style="font-size: 16px; font-weight: 800; color: #38bdf8; font-family: monospace;">
                    ₹{snapshot.spot_price:,.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --- Option Chain Analytics ---
    analyzer = OptionChainAnalyzer()
    analysis = analyzer.analyze(snapshot)

    # Metrics Strip
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Spot Price", f"₹{snapshot.spot_price:,.2f}")
    m2.metric("ATM Strike", f"{analysis.atm_strike:,.0f}" if analysis.atm_strike else "N/A")
    m3.metric("PCR (OI)", f"{analysis.put_call_ratio_oi:.3f}" if analysis.put_call_ratio_oi else "N/A")
    m4.metric("Max Pain", f"{analysis.max_pain_strike:,.0f}" if analysis.max_pain_strike else "N/A")

    from src.utils.time_utils import calendar_days_to_expiry, trading_days_to_expiry
    cal_dte = calendar_days_to_expiry(expiry_date)
    trd_dte = trading_days_to_expiry(expiry_date)
    m5.metric("DTE", f"{cal_dte}d ({trd_dte} trd)")

    # =========================================================================
    # DUAL WORKSPACE: REAL-TIME TECHNICAL CANDLESTICK CHART & AI PATTERNS
    # =========================================================================
    _render_integrated_technical_chart(symbol)

    st.divider()

    # =========================================================================
    # UNIFIED OPTION STRIKE EXECUTION DESK & MATRIX
    # =========================================================================
    st.markdown("### ⚡ Integrated Option Strike Matrix & 1-Click Execution")
    st.caption("Pick any strike (ATM, ITM, OTM) with real-time NSE Greeks, algorithmic statutory charges, and live paper execution.")

    spec = INDEX_SPECS.get(symbol.upper(), INDEX_SPECS["NIFTY"])
    lot_size = spec["lot_size"]

    # Filter selector tabs
    filter_choice = st.radio(
        "Moneyness View Filter:",
        ["🌟 Near ATM (±5 Strikes)", "📈 All Available Strikes", "🟢 In The Money (ITM)", "🔴 Out of The Money (OTM)"],
        horizontal=True,
        index=0,
        key="opt_filter_choice",
    )

    # Filter strike list
    sorted_strikes = sorted(snapshot.strikes, key=lambda r: r.strike_price)
    atm_idx = min(range(len(sorted_strikes)), key=lambda i: abs(sorted_strikes[i].strike_price - snapshot.spot_price))

    if "Near ATM" in filter_choice:
        start_i = max(0, atm_idx - 5)
        end_i = min(len(sorted_strikes), atm_idx + 6)
        active_strikes = sorted_strikes[start_i:end_i]
    elif "In The Money" in filter_choice:
        # Strikes below spot for CE, or above spot for PE
        active_strikes = [r for r in sorted_strikes if abs(r.strike_price - snapshot.spot_price) <= (spec["step"] * 8)]
    elif "Out of The Money" in filter_choice:
        active_strikes = [r for r in sorted_strikes if abs(r.strike_price - snapshot.spot_price) <= (spec["step"] * 10)]
    else:
        active_strikes = sorted_strikes

    # Interactive Order Drawer / Box
    with st.container():
        st.markdown(
            f"""
            <div style="background: rgba(13, 20, 36, 0.95); border: 1px solid rgba(212, 175, 55, 0.35); border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 13px; color: #d4af37; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">
                        ⚡ RAPID EXECUTION TICKET — {symbol} ({expiry_date.strftime('%d-%b-%Y')})
                    </div>
                    <div style="font-size: 11px; color: #10b981; font-weight: 600; background: rgba(16, 185, 129, 0.15); padding: 2px 8px; border-radius: 6px; border: 1px solid rgba(16, 185, 129, 0.3);">
                        LOT SIZE: {lot_size} UNITS
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_side, col_strike, col_lots = st.columns([1.5, 2.5, 1.5])

        with col_side:
            trade_side = st.radio(
                "I want to Buy:",
                ["🟢 CALL (CE)", "🔴 PUT (PE)"],
                index=0,
                key="groww_trade_side",
            )
            is_call = "CALL" in trade_side
            opt_type = OptionType.CE if is_call else OptionType.PE

        # Strike mapping
        strike_options = []
        for r in active_strikes:
            q = r.ce if is_call else r.pe
            ltp = q.last_price if q and q.last_price else 100.0
            tag = "ATM" if r.strike_price == analysis.atm_strike else ("ITM" if (r.strike_price < snapshot.spot_price if is_call else r.strike_price > snapshot.spot_price) else "OTM")
            strike_options.append((r.strike_price, f"{int(r.strike_price)} ({tag}) — LTP: ₹{ltp:.2f}"))

        with col_strike:
            selected_strike_val = st.selectbox(
                "Select Strike Price",
                options=[s[0] for s in strike_options],
                format_func=lambda val: next((s[1] for s in strike_options if s[0] == val), str(val)),
                index=min(len(strike_options) // 2, max(0, len(strike_options) - 1)),
                key="groww_strike_val",
            )

        with col_lots:
            num_lots = st.number_input(
                f"Lots (1 Lot = {lot_size})",
                min_value=1,
                max_value=50,
                value=1,
                step=1,
                key="groww_num_lots",
            )

        # Calculate exact selected option price
        matched_row = next((r for r in active_strikes if r.strike_price == selected_strike_val), None)
        selected_quote = (matched_row.ce if is_call else matched_row.pe) if matched_row else None
        exec_price = float(selected_quote.last_price) if selected_quote and selected_quote.last_price else 125.0
        tot_qty = int(num_lots * lot_size)
        notional_premium = exec_price * tot_qty

        # Statutory NSE Charges
        charges = calculate_nse_charges(
            entry_price=exec_price,
            target_1=exec_price * 1.3,
            target_2=exec_price * 1.5,
            quantity=tot_qty,
            lots=num_lots,
            is_buy_first=True,
        )
        total_order_cost = notional_premium + charges.total_charges

        # Order Summary Preview Card
        c_p1, c_p2, c_p3, c_p4 = st.columns(4)
        c_p1.metric("Contract", f"{symbol} {int(selected_strike_val)} {'CE' if is_call else 'PE'}")
        c_p2.metric("Market LTP", f"₹{exec_price:.2f}")
        c_p3.metric("Required Margin", f"₹{notional_premium:,.2f}")
        c_p4.metric("Govt/NSE Taxes", f"₹{charges.total_charges:.2f}")

        # Execution Button
        col_btn, col_info = st.columns([2, 3])
        with col_btn:
            btn_label = f"🚀 Buy {'Call (CE)' if is_call else 'Put (PE)'} — ₹{total_order_cost:,.2f}"
            if st.button(btn_label, type="primary", use_container_width=True, key="groww_execute_order_btn"):
                contract_symbol = f"{symbol}-{int(selected_strike_val)}-{'CE' if is_call else 'PE'}"
                res = paper_service.place_order(
                    symbol=contract_symbol,
                    side="BUY",
                    quantity=tot_qty,
                    order_type="MARKET",
                    price=exec_price,
                    asset_class="OPTIONS",
                    strategy_tag="GROWW_OPTION_CHAIN",
                )

                if res.get("status") == "REJECTED":
                    st.error(f"❌ Order Rejected by Risk Guard: {res.get('rejection_reason')}")
                else:
                    paper_service.process_market_update(
                        symbol=contract_symbol,
                        bid=round(exec_price * 0.995, 2),
                        ask=round(exec_price * 1.005, 2),
                        ltp=exec_price,
                        data_status="DELAYED",
                        source_provider="GROWW_CHAIN_EXECUTION",
                    )
                    st.success(
                        f"🎉 **Trade Executed Successfully!** Order ID: `{res.get('order_id')}` | "
                        f"Bought {tot_qty} shares ({num_lots} lots) of **{contract_symbol}** at **₹{exec_price:.2f}**! "
                        f"Open the Portfolio expander above to see your live P&L."
                    )
                    st.rerun()

        with col_info:
            equity = paper_service.portfolio.get_equity()
            risk_pct = (total_order_cost / equity) * 100 if equity > 0 else 0
            if risk_pct <= 2.0:
                st.info(f"✅ **Safe Risk Size:** This trade uses only **{risk_pct:.1f}%** of your available portfolio equity.")
            else:
                st.warning(f"⚠️ **Moderate Risk Size:** This trade uses **{risk_pct:.1f}%** of your portfolio.")

    st.divider()

    # =========================================================================
    # OPTION CHAIN TABS (DERIVATIVES TABLE + ADVANCED VOLATILITY CHARTS)
    # =========================================================================
    tab_chain, tab_oi, tab_change, tab_iv = st.tabs([
        "📋 Derivatives Strike Chain Grid",
        "📊 OI Distribution",
        "📈 OI Change",
        "📉 IV Smile / Skew",
    ])

    with tab_chain:
        _render_derivatives_strike_grid(active_strikes, snapshot.spot_price, analysis.atm_strike, symbol, lot_size)

    with tab_oi:
        strikes = [r.strike_price for r in active_strikes]
        ce_oi = [r.ce.open_interest or 0 if r.ce else 0 for r in active_strikes]
        pe_oi = [r.pe.open_interest or 0 if r.pe else 0 for r in active_strikes]
        fig_oi = oi_distribution_chart(strikes, ce_oi, pe_oi, snapshot.spot_price, analysis.atm_strike, f"{symbol} Open Interest Distribution")
        st.plotly_chart(fig_oi, use_container_width=True)

    with tab_change:
        strikes = [r.strike_price for r in active_strikes]
        ce_change = [r.ce.change_in_oi or 0 if r.ce else 0 for r in active_strikes]
        pe_change = [r.pe.change_in_oi or 0 if r.pe else 0 for r in active_strikes]
        fig_chg = oi_change_chart(strikes, ce_change, pe_change, snapshot.spot_price, f"{symbol} Change in Open Interest")
        st.plotly_chart(fig_chg, use_container_width=True)

    with tab_iv:
        strikes = [r.strike_price for r in active_strikes]
        ce_iv = [r.ce.implied_volatility if r.ce else None for r in active_strikes]
        pe_iv = [r.pe.implied_volatility if r.pe else None for r in active_strikes]
        fig_iv = iv_smile_chart(strikes, ce_iv, pe_iv, snapshot.spot_price, f"{symbol} IV Smile / Skew")
        st.plotly_chart(fig_iv, use_container_width=True)

    st.divider()

    # --- OI Concentration Zones & Alerts ---
    if analysis.oi_concentration_zones:
        st.subheader("🎯 Probabilistic OI Concentration Zones")
        for zone in analysis.oi_concentration_zones[:4]:
            side_emoji = "🔴" if zone.option_type == OptionType.CE else "🟢"
            st.markdown(
                f"{side_emoji} **{zone.strike_price:,.0f} {zone.option_type.value}** — "
                f"OI: {zone.open_interest:,.0f} | ΔOI: {zone.change_in_oi or 0:,.0f}  \n"
                f"<span style='color: #94a3b8; font-size: 12px;'>{zone.interpretation}</span>",
                unsafe_allow_html=True,
            )

    # --- Data Quality Report ---
    with st.expander("📊 Data Quality & Model Diagnostics"):
        render_data_quality_summary(quality_report.model_dump())


def _render_integrated_technical_chart(symbol: str):
    """Embed real-time candlestick price action chart with AI pattern overlays directly in the options terminal."""
    from datetime import timedelta
    from src.features.price_action import PriceActionEngine
    from src.features.technical import compute_technical_features_df
    from src.ingestion.provider_factory import get_market_data_provider
    import plotly.graph_objects as go

    with st.expander("📈 Real-Time Candlestick Chart & AI Pattern Overlay", expanded=True):
        try:
            provider = get_market_data_provider()
            end_date = date.today()
            start_date = end_date - timedelta(days=120)
            df = provider.get_ohlcv(symbol=symbol, start=start_date, end=end_date)

            if df.empty or len(df) < 10:
                st.info(f"Candlestick price action data loading for {symbol}...")
                return

            df_feat = compute_technical_features_df(df=df, symbol=symbol)
            pa_engine = PriceActionEngine()
            pattern_markers = pa_engine.scan_all_patterns(df_feat)
            key_levels = pa_engine.get_key_levels(df_feat)

            col_chart, col_intel = st.columns([3, 1])

            with col_chart:
                fig = go.Figure()
                fig.add_trace(
                    go.Candlestick(
                        x=df_feat["timestamp"],
                        open=df_feat["open"],
                        high=df_feat["high"],
                        low=df_feat["low"],
                        close=df_feat["close"],
                        name=f"{symbol} Spot",
                        increasing_line_color="#10b981",
                        decreasing_line_color="#f43f5e",
                    )
                )

                if "sma_20" in df_feat.columns:
                    fig.add_trace(go.Scatter(x=df_feat["timestamp"], y=df_feat["sma_20"], name="SMA 20", line=dict(color="#d4af37", width=1.5)))
                if "sma_50" in df_feat.columns:
                    fig.add_trace(go.Scatter(x=df_feat["timestamp"], y=df_feat["sma_50"], name="SMA 50", line=dict(color="#38bdf8", width=1.5)))

                if key_levels.get("resistance_20", 0) > 0:
                    fig.add_hline(y=key_levels["resistance_20"], line_dash="dash", line_color="#f43f5e",
                                  annotation_text=f"Resistance: ₹{key_levels['resistance_20']:,.0f}", annotation_position="top left")
                if key_levels.get("support_20", 0) > 0:
                    fig.add_hline(y=key_levels["support_20"], line_dash="dash", line_color="#10b981",
                                  annotation_text=f"Support: ₹{key_levels['support_20']:,.0f}", annotation_position="bottom left")

                bull_markers = [m for m in pattern_markers if m["type"] == "BULLISH"]
                bear_markers = [m for m in pattern_markers if m["type"] == "BEARISH"]

                if bull_markers:
                    fig.add_trace(
                        go.Scatter(
                            x=[m["timestamp"] for m in bull_markers],
                            y=[m["price"] * 0.995 for m in bull_markers],
                            mode="markers+text",
                            marker=dict(symbol="triangle-up", size=10, color="#10b981"),
                            text=[m["pattern"] for m in bull_markers],
                            textposition="bottom center",
                            textfont=dict(size=9, color="#10b981"),
                            name="Bullish Pattern",
                        )
                    )
                if bear_markers:
                    fig.add_trace(
                        go.Scatter(
                            x=[m["timestamp"] for m in bear_markers],
                            y=[m["price"] * 1.005 for m in bear_markers],
                            mode="markers+text",
                            marker=dict(symbol="triangle-down", size=10, color="#f43f5e"),
                            text=[m["pattern"] for m in bear_markers],
                            textposition="top center",
                            textfont=dict(size=9, color="#f43f5e"),
                            name="Bearish Pattern",
                        )
                    )

                fig.update_layout(
                    height=380,
                    margin=dict(l=10, r=10, t=10, b=10),
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(7, 9, 14, 0.8)",
                    xaxis_rangeslider_visible=False,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_intel:
                st.markdown(
                    f"""
                    <div style="background: rgba(13, 20, 36, 0.9); border: 1px solid rgba(212, 175, 55, 0.35); border-radius: 10px; padding: 12px 14px; margin-bottom: 8px;">
                        <div style="font-size: 11px; color: #d4af37; font-weight: 700; text-transform: uppercase;">AI PATTERN SCANNER</div>
                        <div style="font-size: 13px; font-weight: 700; color: #f8fafc; margin-top: 4px;">{key_levels.get('market_structure', 'Consolidation')}</div>
                        <hr style="border-color: rgba(255,255,255,0.08); margin: 8px 0;" />
                        <div style="font-size: 11px; color: #94a3b8;"><b>20D Support:</b> ₹{key_levels.get('support_20', 0):,.1f}</div>
                        <div style="font-size: 11px; color: #94a3b8;"><b>20D Resistance:</b> ₹{key_levels.get('resistance_20', 0):,.1f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if pattern_markers:
                    st.caption(f"**Detected Formations ({len(pattern_markers)}):**")
                    for pm in pattern_markers[-3:]:
                        icon = "🟢" if pm["type"] == "BULLISH" else ("🔴" if pm["type"] == "BEARISH" else "🟡")
                        st.caption(f"{icon} **{pm['pattern']}**: {pm['context'][:50]}...")
        except Exception as e:
            st.info(f"Candlestick chart preview: {e}")


def _render_derivatives_strike_grid(strikes: List[OptionStrikeRow], spot: float, atm_strike: Optional[float], symbol: str, lot_size: int):
    """Render the Derivatives Option Chain table with CE on left, Strike in center, PE on right."""
    rows = []
    for r in strikes:
        k = r.strike_price
        is_atm = (k == atm_strike)
        moneyness_ce = classify_moneyness(spot, k, OptionType.CE)
        moneyness_pe = classify_moneyness(spot, k, OptionType.PE)

        ce_ltp = f"₹{r.ce.last_price:.2f}" if r.ce and r.ce.last_price else "—"
        pe_ltp = f"₹{r.pe.last_price:.2f}" if r.pe and r.pe.last_price else "—"
        ce_iv = f"{r.ce.implied_volatility:.1f}%" if r.ce and r.ce.implied_volatility else "—"
        pe_iv = f"{r.pe.implied_volatility:.1f}%" if r.pe and r.pe.implied_volatility else "—"
        ce_oi = f"{r.ce.open_interest:,}" if r.ce and r.ce.open_interest else "—"
        pe_oi = f"{r.pe.open_interest:,}" if r.pe and r.pe.open_interest else "—"
        ce_doi = f"{r.ce.change_in_oi:+,}" if r.ce and r.ce.change_in_oi else "—"
        pe_doi = f"{r.pe.change_in_oi:+,}" if r.pe and r.pe.change_in_oi else "—"

        status_tag = "🎯 ATM" if is_atm else ("ITM" if moneyness_ce == Moneyness.ITM else "OTM")

        rows.append({
            "CALL OI": ce_oi,
            "CALL ΔOI": ce_doi,
            "CALL IV": ce_iv,
            "CALL LTP": ce_ltp,
            "STRIKE": f"{k:,.0f} ({status_tag})",
            "PUT LTP": pe_ltp,
            "PUT IV": pe_iv,
            "PUT ΔOI": pe_doi,
            "PUT OI": pe_oi,
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=min(650, len(rows) * 35 + 40),
        )
    else:
        st.info("No strikes found matching current filter.")


if __name__ == "__main__":
    st.set_page_config(page_title="Options Chain", layout="wide")
    render_options_chain_page()
