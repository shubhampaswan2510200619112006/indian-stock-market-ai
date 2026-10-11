"""
Streamlit Dashboard Page — Phase 8 Paper Trading Terminal.

PAPER TRADING MODE — NO LIVE ORDERS — SIMULATED EXECUTION
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on Python path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


import streamlit as st

from src.paper_trading.execution_guard import ExecutionGuard
from src.paper_trading.service import PaperTradingService


def _get_service() -> PaperTradingService:
    if "paper_service" not in st.session_state:
        st.session_state["paper_service"] = PaperTradingService()
    return st.session_state["paper_service"]


def render_paper_trading_page():
    """Render the main paper trading dashboard."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #ff6b35, #f7c948); padding: 12px 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0;">📋 PAPER TRADING MODE</h2>
            <p style="color: white; margin: 4px 0 0 0; font-size: 14px;">
                NO LIVE ORDERS &nbsp;•&nbsp; SIMULATED EXECUTION &nbsp;•&nbsp; NO REAL MONEY
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    service = _get_service()
    guard_status = ExecutionGuard.get_execution_status()

    # Safety status
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("LIVE EXECUTION", guard_status["LIVE_EXECUTION"])
    with col2:
        st.metric("BROKER CONNECTIONS", guard_status["BROKER_CONNECTIONS"])
    with col3:
        st.metric("PAPER EXECUTION", guard_status["PAPER_EXECUTION"])

    st.divider()

    # Portfolio summary
    summary = service.get_portfolio_summary()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("💰 Cash", f"₹{summary['cash']:,.0f}")
    with c2:
        st.metric("📊 Equity", f"₹{summary['equity']:,.0f}")
    with c3:
        st.metric("📈 Total P&L", f"₹{summary['total_pnl']:,.0f}")
    with c4:
        st.metric("📉 Drawdown", f"{summary['drawdown_pct']*100:.2f}%")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric("Daily P&L", f"₹{summary['daily_pnl']:,.0f}")
    with c6:
        st.metric("Open Positions", summary['open_positions_count'])
    with c7:
        st.metric("Realized P&L", f"₹{summary['realized_pnl']:,.0f}")
    with c8:
        st.metric("Starting Capital", f"₹{summary['starting_capital']:,.0f}")

    st.divider()

    # Session & system status
    session = service.get_session_status()
    st.markdown("### System Status")
    status_cols = st.columns(4)
    with status_cols[0]:
        st.info(f"Options Paper Trading: **{session['options_paper_trading']}**")
    with status_cols[1]:
        st.info(f"ML Readiness: **{session['ml_production_readiness']}**")
    with status_cols[2]:
        st.info(f"Session: **{session['status']}**")
    with status_cols[3]:
        st.info(f"Mode: **{session['execution_mode']}**")

    st.divider()

    # Order entry form
    st.markdown("### 📝 Place Paper Order")
    st.caption("⚠️ SIMULATED PAPER TRADING — Real Market Mechanics with No Real Money at Risk")

    from src.options.pricing import black_scholes_price
    from datetime import datetime, timezone

    # Instrument selector outside form for reactive strike defaults
    inst_type = st.radio(
        "Select Instrument Type",
        ["Options Contract (CE / PE)", "Index (Spot / Futures)"],
        horizontal=True,
    )

    underlying = st.selectbox("Underlying Index", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
    
    # Base spot references
    spot_map = {"NIFTY": 24200.0, "BANKNIFTY": 51500.0, "FINNIFTY": 23800.0}
    default_step = {"NIFTY": 50, "BANKNIFTY": 100, "FINNIFTY": 50}[underlying]
    default_lot = {"NIFTY": 25, "BANKNIFTY": 15, "FINNIFTY": 25}[underlying]
    base_spot = spot_map[underlying]

    with st.form("paper_order_form"):
        col_left, col_right = st.columns(2)
        
        if "Options" in inst_type:
            with col_left:
                opt_type = st.selectbox(
                    "Option Type",
                    ["CALL (CE) - Expect Market UP 🟢", "PUT (PE) - Expect Market DOWN 🔴"],
                )
                raw_opt = "CE" if "CALL" in opt_type else "PE"
                
                strike = st.number_input(
                    f"Strike Price (Spot ~ ₹{base_spot:,.0f})",
                    min_value=1000.0,
                    max_value=100000.0,
                    value=float(base_spot),
                    step=float(default_step),
                )
                side = st.selectbox("Side", ["BUY", "SELL"])
                quantity = st.number_input("Quantity (Shares/Units)", min_value=default_lot, value=default_lot, step=default_lot)
            
            with col_right:
                dte = st.slider("Days to Expiry (DTE)", min_value=1, max_value=30, value=4)
                order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
                limit_price = st.number_input("Limit Price (if LIMIT order)", min_value=0.0, value=0.0, step=0.5)
                strategy = st.text_input("Trade Notes / Strategy Name", value="Manual Practice Trade")

            # Estimated premium calculation via Black-Scholes
            tte_years = max(0.001, dte / 365.0)
            est_premium = black_scholes_price(
                spot=base_spot,
                strike=strike,
                tte=tte_years,
                r=0.065,
                sigma=0.14,
                option_type=raw_opt,
            )
            est_premium = max(1.0, round(est_premium, 2))
            est_total = est_premium * quantity

            st.info(f"💡 **Estimated Option Premium:** **₹{est_premium:.2f}** per unit | **Estimated Trade Value:** **₹{est_total:,.2f}**")
            formatted_symbol = f"{underlying}-{int(strike)}-{raw_opt}"

        else:
            # Index Trading
            formatted_symbol = underlying
            raw_opt = None
            strike = None
            with col_left:
                side = st.selectbox("Side", ["BUY", "SELL"])
                quantity = st.number_input("Quantity", min_value=default_lot, value=default_lot, step=default_lot)
            with col_right:
                order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
                limit_price = st.number_input("Limit Price (if LIMIT order)", min_value=0.0, value=0.0, step=0.5)
                strategy = st.text_input("Trade Notes / Strategy Name", value="Index Trade")
            est_premium = base_spot

        submitted = st.form_submit_button("📋 Submit Paper Order", use_container_width=True)
        if submitted:
            result = service.place_order(
                symbol=formatted_symbol,
                side=side,
                quantity=int(quantity),
                order_type=order_type,
                limit_price=limit_price if limit_price > 0 else None,
                instrument_type="OPTION" if "Options" in inst_type else "INDEX",
                strike=strike,
                option_type=raw_opt,
                strategy_name=strategy if strategy else None,
            )
            if result.get("status") == "REJECTED":
                st.error(f"❌ Order REJECTED: {result.get('rejection_reason')}")
            else:
                order_id = result.get("order_id")
                # For Market orders, simulate instant fill using theoretical market quote
                if order_type == "MARKET":
                    fill_p = est_premium
                    service.fill_engine.allow_off_hours_simulation = True
                    sim_res = service.process_market_update(
                        symbol=formatted_symbol,
                        bid=round(fill_p * 0.995, 2),
                        ask=round(fill_p * 1.005, 2),
                        ltp=fill_p,
                        data_status="DELAYED",
                        source_provider="THEORETICAL_BS" if "Options" in inst_type else "SIMULATED_SPOT",
                    )
                    st.success(
                        f"✅ **Paper Order FILLED!**  \n"
                        f"**Contract:** `{formatted_symbol}` &nbsp;|&nbsp; **Side:** `{side}` &nbsp;|&nbsp; **Qty:** `{quantity}`  \n"
                        f"**Fill Price:** `₹{fill_p:,.2f}` &nbsp;|&nbsp; **Order ID:** `{order_id}`  \n"
                        f"👉 Head over to **'Paper Positions'** to monitor your live P&L and close the trade!"
                    )
                else:
                    st.success(f"✅ Paper order placed: {order_id} (Status: PENDING LIMIT ORDER at ₹{limit_price})")

    st.divider()

    # Recent orders
    st.markdown("### 📋 Recent Orders")
    orders = service.get_orders()
    if orders.get("orders"):
        import pandas as pd
        df = pd.DataFrame(orders["orders"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No orders yet.")

    # Risk status
    st.markdown("### ⚠️ Risk Status")
    risk = service.get_risk_status()
    if risk.get("is_any_breaker_active"):
        st.error("🚨 CIRCUIT BREAKER ACTIVE — New orders rejected")
    else:
        st.success("✅ Risk controls normal")

    st.caption(f"Limits label: {risk.get('configured_limits', {}).get('label', 'CONFIGURED PAPER RISK LIMITS')}")

if __name__ == "__main__":
    st.set_page_config(page_title="Paper Trading", layout="wide")
    render_paper_trading_page()

