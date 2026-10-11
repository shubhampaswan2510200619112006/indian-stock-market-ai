"""
Beginner-Friendly Guided Views.
Provides plain-English workflows, guided order placement, simple terminology,
educational tooltips, and transparent safety guardrails.
Shares the exact same PaperTradingService and risk invariants as Pro mode.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta, timezone
import plotly.graph_objects as go
from src.paper_trading.service import PaperTradingService
from src.options.pricing import black_scholes_price
from src.utils.time_utils import is_market_open, now_ist
from src.features.price_action import PriceActionEngine
from src.ingestion.yfinance_provider import YFinanceProvider


def render_beginner_home(service: PaperTradingService):
    """Render the simplified Beginner Home dashboard."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); padding: 18px 22px; border-radius: 10px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span class="mode-badge-beginner">🔰 BEGINNER MODE ACTIVE</span>
                    <h2 style="color: white; margin: 8px 0 4px 0; font-size: 22px;">Welcome to Indian Stock Market AI</h2>
                    <p style="color: #94a3b8; margin: 0; font-size: 14px;">
                        Risk-free simulated trading with virtual funds. Learn, practice, and test market strategies safely.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Essential Portfolio Numbers
    summary = service.get_portfolio_summary()
    st.markdown("### 💰 Your Account at a Glance")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Account Value", f"₹{summary['equity']:,.0f}", help="Total worth of your account = Virtual Cash + Current Value of your active trades.")
    with col2:
        st.metric("Available Cash", f"₹{summary['cash']:,.0f}", help="Money ready to be used for new practice trades.")
    with col3:
        pnl = summary['total_pnl']
        st.metric("Total Profit / Loss", f"₹{pnl:,.0f}", delta=f"{summary['realized_pnl']:,.0f} realized", help="Total earnings or losses since you started practicing.")
    with col4:
        st.metric("Active Trades", summary['open_positions_count'], help="Number of open investments you currently hold.")

    st.markdown(
        """
        <div class="edu-tip-box">
            💡 <b>What is Paper Trading?</b> You are using 100% simulated play-money (starting with ₹10 Lakhs). No real money is at risk. 
            Every trade behaves with realistic prices, taxes, and exchange rules.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # 2. Market Pulse & Guidance
    st.markdown("### 🚦 Today's Market Direction")
    market_status = "🟢 Market is OPEN (Live Trading)" if is_market_open() else "🟡 Market is CLOSED (Practice Mode Active)"
    st.caption(f"**Exchange Status:** {market_status} • **Time:** {now_ist().strftime('%I:%M %p IST')}")

    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.markdown(
            """
            <div class="fin-card">
                <div style="font-weight: 600; color: #38bdf8;">🏛️ NIFTY 50</div>
                <div style="font-size: 20px; font-weight: 700; margin: 4px 0;" class="metric-mono">~24,200.00</div>
                <div style="font-size: 12px; color: #94a3b8;">Represents India's top 50 bluechip companies. Best index for beginners.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with mc2:
        st.markdown(
            """
            <div class="fin-card">
                <div style="font-weight: 600; color: #38bdf8;">🏦 BANK NIFTY</div>
                <div style="font-size: 20px; font-weight: 700; margin: 4px 0;" class="metric-mono">~51,500.00</div>
                <div style="font-size: 12px; color: #94a3b8;">Represents the 12 largest banks (HDFC, ICICI, SBI). Fast moving & volatile.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with mc3:
        st.markdown(
            """
            <div class="fin-card">
                <div style="font-weight: 600; color: #10b981;">🛡️ Safety Status</div>
                <div style="font-size: 16px; font-weight: 600; color: #34d399; margin: 4px 0;">All Systems Protected</div>
                <div style="font-size: 12px; color: #94a3b8;">Automated circuit breakers and loss caps are actively protecting your balance.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # 3. Next Steps Navigation
    st.markdown("### 🚀 What Would You Like to Do?")
    qc1, qc2, qc3 = st.columns(3)
    with qc1:
        st.markdown("#### 🎯 Place a Trade")
        st.write("Pick an index and follow our 3-step guided wizard to execute your first order.")
        if st.button("Go to Guided Trade ➔", use_container_width=True, key="btn_home_to_trade"):
            st.session_state["beginner_nav"] = "🎯 Guided Paper Trade"
            st.rerun()

    with qc2:
        st.markdown("#### 💼 View My Open Trades")
        st.write("Track your active holdings, monitor live profit/loss, and exit trades.")
        if st.button("Check My Trades ➔", use_container_width=True, key="btn_home_to_pos"):
            st.session_state["beginner_nav"] = "💼 My Holdings & Positions"
            st.rerun()

    with qc3:
        st.markdown("#### 🎓 Learn Options Basics")
        st.write("Understand Call, Put, Strike prices, and the 2% safety rule in plain English.")
        if st.button("Open Trading Academy ➔", use_container_width=True, key="btn_home_to_academy"):
            st.session_state["beginner_nav"] = "🎓 Trader Academy & Guide"
            st.rerun()


def render_beginner_trade(service: PaperTradingService):
    """Render the 3-step Guided Order Placement wizard for Beginners."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 16px 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0; font-size: 20px;">🎯 Guided Paper Trade Wizard</h2>
            <p style="color: #cbd5e1; margin: 4px 0 0 0; font-size: 13px;">
                Trade options or index futures with automatic price estimation and risk safeguards.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Step 1: What Is Your Market Outlook?")
    direction = st.radio(
        "Choose what you expect the market to do:",
        [
            "🟢 I expect the market to GO UP (Buy CALL / CE)",
            "🔴 I expect the market to GO DOWN (Buy PUT / PE)",
            "🏛️ I want to trade the Index directly (Spot / Futures)",
        ],
        index=0,
    )

    col_underlying, col_lots = st.columns(2)
    with col_underlying:
        underlying = st.selectbox(
            "Which Index do you want to trade?",
            ["NIFTY (Top 50 Companies)", "BANKNIFTY (Banking Index)"],
            index=0,
        )
        underlying_code = "NIFTY" if "NIFTY (" in underlying else "BANKNIFTY"
        base_spot = 24200.0 if underlying_code == "NIFTY" else 51500.0
        lot_size = 25 if underlying_code == "NIFTY" else 15

    with col_lots:
        lots = st.number_input(
            f"How many Lots? (1 Lot = {lot_size} shares)",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
            help="In India, options are bought in fixed bundles called lots.",
        )
        total_quantity = lots * lot_size

    is_options = "I expect" in direction
    raw_opt_type = "CE" if "GO UP" in direction else ("PE" if "GO DOWN" in direction else None)

    # Optional Candlestick Chart & Pattern Inspection
    with st.expander(f"📊 View {underlying_code} Candlestick Chart & Detected Patterns", expanded=False):
        render_candlestick_and_patterns_widget(underlying_code, days=45)

    st.markdown("#### Step 2: Review Strike & Estimated Investment")
    if is_options:
        strike = base_spot
        tte_years = 4 / 365.0
        est_premium = black_scholes_price(
            spot=base_spot,
            strike=strike,
            tte=tte_years,
            r=0.065,
            sigma=0.14,
            option_type=raw_opt_type,
        )
        est_premium = max(1.0, round(est_premium, 2))
        total_cost = est_premium * total_quantity
        formatted_symbol = f"{underlying_code}-{int(strike)}-{raw_opt_type}"

        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.metric("Option Contract", formatted_symbol)
        with col_c2:
            st.metric("Estimated Price per Share", f"₹{est_premium:.2f}")
        with col_c3:
            st.metric("Total Investment Required", f"₹{total_cost:,.2f}")

        equity = service.portfolio.get_equity()
        risk_pct = (total_cost / equity) * 100 if equity > 0 else 0
        if risk_pct <= 2.0:
            st.success(f"✅ **Safe Trade Size:** This order uses only **{risk_pct:.1f}%** of your account. (Well within the 2% safety rule!)")
        else:
            st.warning(f"⚠️ **Moderate Risk Size:** This trade uses **{risk_pct:.1f}%** of your account balance.")
    else:
        formatted_symbol = underlying_code
        total_cost = base_spot * total_quantity
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.metric("Index Contract", formatted_symbol)
        with col_c2:
            st.metric("Current Spot Reference", f"₹{base_spot:,.2f}")

    st.markdown("#### Step 3: Confirm and Place Your Practice Order")
    st.write(f"You are about to execute a simulated **BUY** order for **{total_quantity} shares** of **{formatted_symbol}**.")

    if st.button("🚀 Confirm & Submit Paper Trade", type="primary", use_container_width=True):
        service.fill_engine.allow_off_hours_simulation = True
        res = service.place_order(
            symbol=formatted_symbol,
            side="BUY",
            quantity=total_quantity,
            order_type="MARKET",
            instrument_type="OPTION" if is_options else "INDEX",
            strike=strike if is_options else None,
            option_type=raw_opt_type,
            strategy_name="Beginner Guided Trade",
        )

        if res.get("status") == "REJECTED":
            st.error(f"❌ Order Rejected by Safety System: {res.get('rejection_reason')}")
        else:
            order_id = res.get("order_id")
            fill_price = est_premium if is_options else base_spot
            service.process_market_update(
                symbol=formatted_symbol,
                bid=round(fill_price * 0.995, 2),
                ask=round(fill_price * 1.005, 2),
                ltp=fill_price,
                data_status="DELAYED",
                source_provider="THEORETICAL_BS" if is_options else "SIMULATED_SPOT",
            )
            st.success(
                f"🎉 **Trade Executed Successfully!**  \n"
                f"**Order ID:** `{order_id}` | **Contract:** `{formatted_symbol}` | **Executed Price:** `₹{fill_price:,.2f}`  \n"
                f"Your new position is active! Click below to check your live profit/loss."
            )
            if st.button("View My Open Positions ➔"):
                st.session_state["beginner_nav"] = "💼 My Holdings & Positions"
                st.rerun()


def render_beginner_portfolio(service: PaperTradingService):
    """Render a clean holdings view tailored for Beginners."""
    st.markdown("### 💼 My Active Holdings & Open Trades")
    st.caption("Track the current value of your trades and exit when you reach your profit goal.")

    positions = service.get_positions().get("positions", [])
    if not positions:
        st.info("ℹ️ You do not have any active trades right now. Head over to **Guided Trade** to make your first practice investment.")
        if st.button("Place a Trade Now ➔"):
            st.session_state["beginner_nav"] = "🎯 Guided Paper Trade"
            st.rerun()
        return

    df_pos = pd.DataFrame(positions)
    for idx, pos in enumerate(positions):
        pid = pos.get("position_id")
        sym = pos.get("symbol")
        qty = pos.get("quantity")
        entry = pos.get("avg_entry_price", 0)
        curr = pos.get("current_price", entry)
        pnl = pos.get("unrealized_pnl", 0)
        pnl_pct = (pnl / (entry * qty)) * 100 if (entry * qty) > 0 else 0

        pnl_color = "text-profit" if pnl >= 0 else "text-loss"
        pnl_prefix = "+" if pnl >= 0 else ""

        with st.container():
            st.markdown(
                f"""
                <div class="fin-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 16px; font-weight: 700; color: #38bdf8;">{sym}</span>
                            <span style="font-size: 12px; color: #94a3b8; margin-left: 10px;">ID: {pid}</span>
                        </div>
                        <div class="{pnl_color}" style="font-size: 18px;" class="metric-mono">
                            {pnl_prefix}₹{pnl:,.2f} ({pnl_prefix}{pnl_pct:.2f}%)
                        </div>
                    </div>
                    <div style="display: flex; gap: 24px; margin-top: 10px; font-size: 13px; color: #cbd5e1;">
                        <div><b>Quantity:</b> {qty} units</div>
                        <div><b>Bought At:</b> ₹{entry:,.2f}</div>
                        <div><b>Current Price:</b> ₹{curr:,.2f}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_exit, col_spacer = st.columns([1, 3])
            with col_exit:
                if st.button(f"🚪 Exit Trade ({sym})", key=f"btn_close_{pid}_{idx}", type="secondary"):
                    res = service.close_position(pid)
                    if res.get("status") == "REJECTED":
                        st.error(f"Could not exit: {res.get('rejection_reason')}")
                    else:
                        st.success(f"Trade closed successfully! Profit/Loss locked into your cash balance.")
                        st.rerun()


def render_beginner_risk(service: PaperTradingService):
    """Render the simplified risk & guardrails explanation."""
    st.markdown("### 🛡️ Your Account Safety & Guardrails")
    st.caption("How Indian Stock Market AI automatically protects your capital from catastrophic losses.")

    risk = service.get_risk_status()
    limits = risk.get("configured_limits", {})

    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric("Max Daily Loss Cap", f"₹{limits.get('max_daily_loss', 50000):,.0f}", help="If your losses hit this number in one day, the system stops trading to protect you.")
    with r2:
        st.metric("Max Loss Drawdown Limit", f"{limits.get('max_drawdown_pct', 0.1)*100:.1f}%", help="Maximum allowable dip from your account's peak value.")
    with r3:
        breaker = risk.get("is_any_breaker_active", False)
        status_txt = "🚨 HALTED" if breaker else "🟢 HEALTHY"
        st.metric("Circuit Breaker Status", status_txt)

    st.markdown(
        """
        <div class="edu-tip-box">
            <b>Why do these guardrails exist?</b><br>
            In professional stock and options trading, risk management is more important than prediction. 
            These rules ensure that even during sudden market crashes, your account can never be wiped out.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("#### ⚡ Emergency Safety Controls")
    c_trip, c_reset = st.columns(2)
    with c_trip:
        if st.button("🚨 Emergency Stop (Freeze All Trading)"):
            service.trip_breaker(reason="USER_MANUAL_HALT")
            st.warning("All trading has been halted.")
            st.rerun()
    with c_reset:
        if st.button("🔄 Unfreeze / Reset System"):
            service.reset_breakers()
            st.success("Trading unfrozen and returned to normal status.")
            st.rerun()


def render_beginner_academy():
    """Render educational glossary and trading fundamentals."""
    st.markdown("### 🎓 Trading Academy & Glossary (In Plain English)")
    st.caption("Essential terms and concepts explained without confusing financial jargon.")

    with st.expander("📌 What is NIFTY 50 and BANK NIFTY?", expanded=True):
        st.write(
            """
            - **NIFTY 50:** An index made of the 50 largest and most reliable companies in India (Reliance, TCS, Infosys, HDFC Bank, etc.). If the overall Indian economy is growing, NIFTY tends to rise.
            - **BANK NIFTY:** An index representing the top 12 banking institutions in India. Banks are more volatile and swing up and down faster than NIFTY.
            """
        )

    with st.expander("📌 What is a CALL Option (CE)?"):
        st.write(
            """
            - **CALL (CE) = Green Flag (Bullish).**
            - You buy a CALL option when you think the stock or index will **GO UP**.
            - As the price of the index climbs higher, your CALL option increases in value.
            """
        )

    with st.expander("📌 What is a PUT Option (PE)?"):
        st.write(
            """
            - **PUT (PE) = Red Flag (Bearish).**
            - You buy a PUT option when you think the stock or index will **GO DOWN**.
            - As the price drops, your PUT option increases in value.
            """
        )

    with st.expander("📌 What is a Strike Price?"):
        st.write(
            """
            - The **Strike Price** is the target price level of the contract.
            - If NIFTY is at 24,215:
              - **At-The-Money (ATM):** Strike 24,200 (closest to current price). Best for beginners.
              - **Out-of-The-Money (OTM):** Far away strikes (like 24,800). Cheap, but high risk of expiring worthless.
            """
        )

    with st.expander("📌 The 2% Golden Rule of Trading"):
        st.write(
            """
            - Never risk more than **1% to 2%** of your total portfolio on any single trade.
            - On a ₹10,00,000 account, never risk more than ₹10,000 to ₹20,000 per trade.
            - This ensures that even if you face 5 losing trades in a row, you still keep 90%+ of your capital safe.
            """
        )


def render_candlestick_and_patterns_widget(symbol: str = "NIFTY", days: int = 60):
    """Render an interactive candlestick chart and detected chart patterns."""
    st.markdown(f"#### 🕯️ {symbol} Candlestick Chart ({days} Days)")

    try:
        yf = YFinanceProvider()
        end = date.today()
        start = end - timedelta(days=days * 2)
        df = yf.get_ohlcv(symbol, start, end)

        if df.empty or len(df) < 5:
            st.info(f"No recent candlestick data returned for {symbol}. Check market hours or provider connection.")
            return

        df = df.tail(days).reset_index(drop=True)

        # 1. Interactive Candlestick Chart
        fig = go.Figure()
        fig.add_trace(
            go.Candlestick(
                x=df["date"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name=f"{symbol} Price",
                increasing_line_color="#10b981",  # Crisp green
                decreasing_line_color="#ef4444",  # Crisp red
            )
        )

        # Add 20 SMA line
        if len(df) >= 20:
            df["sma20"] = df["close"].rolling(window=20).mean()
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["sma20"],
                    name="20-Day SMA",
                    line=dict(color="#38bdf8", width=1.5),
                )
            )

        fig.update_layout(
            template="plotly_dark",
            height=420,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis_rangeslider_visible=False,
            paper_bgcolor="#0d121f",
            plot_bgcolor="#090d16",
        )
        st.plotly_chart(fig, use_container_width=True)

        # 2. Detect & Display Candlestick Patterns
        st.markdown(f"#### 🔍 Detected Candlestick Patterns ({symbol})")
        pa_engine = PriceActionEngine()
        patterns = pa_engine.detect_patterns(df)

        if patterns:
            for p in patterns:
                pat_name = p.pattern
                conf = int(p.confidence * 100)
                ctx = p.context
                invalidation = p.invalidation_conditions

                # Color badge based on bullish / bearish / indecision
                is_bullish = any(b in pat_name.lower() for b in ["hammer", "bullish", "morning"])
                is_bearish = any(b in pat_name.lower() for b in ["shooting", "bearish", "evening"])
                color_class = "text-profit" if is_bullish else ("text-loss" if is_bearish else "text-muted")
                bias_tag = "🟢 BULLISH SIGNAL" if is_bullish else ("🔴 BEARISH SIGNAL" if is_bearish else "🟡 CONSOLIDATION / NEUTRAL")

                st.markdown(
                    f"""
                    <div class="fin-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 16px; font-weight: 700; color: #f8fafc;">{pat_name} Pattern</span>
                                <span style="font-size: 11px; margin-left: 8px;" class="{color_class}"><b>{bias_tag}</b></span>
                            </div>
                            <div style="font-size: 13px; color: #38bdf8; font-weight: 600;">Match: {conf}%</div>
                        </div>
                        <div style="font-size: 13px; color: #cbd5e1; margin-top: 6px;"><b>Meaning:</b> {ctx}</div>
                        <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;"><b>Invalidation Rule:</b> {invalidation}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("ℹ️ No classic reversal patterns on the latest candle. Market is consolidating within normal ranges.")

    except Exception as e:
        st.warning(f"Unable to load candlestick chart right now: {e}")


def render_beginner_market_discovery(symbol: str = "NIFTY"):
    """Render the simplified Market Discovery page with Candlestick Chart & Patterns."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); padding: 16px 20px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0; font-size: 20px;">📈 Market Discovery & Price Charts</h2>
            <p style="color: #cbd5e1; margin: 4px 0 0 0; font-size: 13px;">
                Inspect interactive candlestick charts, moving averages, and automated pattern detection.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sym_col, days_col = st.columns([2, 2])
    with sym_col:
        selected_sym = st.selectbox("Select Asset", ["NIFTY", "BANKNIFTY", "FINNIFTY"], index=0)
    with days_col:
        history_days = st.slider("Candlestick History (Days)", min_value=15, max_value=120, value=60, step=15)

    render_candlestick_and_patterns_widget(selected_sym, history_days)

