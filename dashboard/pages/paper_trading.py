"""
Streamlit Dashboard Page — Phase 8 Paper Trading Terminal.

PAPER TRADING MODE — NO LIVE ORDERS — SIMULATED EXECUTION
"""

from __future__ import annotations

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
    st.caption("⚠️ PAPER ORDER ONLY — no real execution")

    with st.form("paper_order_form"):
        oc1, oc2 = st.columns(2)
        with oc1:
            symbol = st.selectbox("Symbol", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
            side = st.selectbox("Side", ["BUY", "SELL"])
            quantity = st.number_input("Quantity", min_value=1, value=25, step=25)
        with oc2:
            order_type = st.selectbox("Order Type", ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"])
            limit_price = st.number_input("Limit Price", min_value=0.0, value=0.0, step=0.05)
            strategy = st.text_input("Strategy Name", value="")

        submitted = st.form_submit_button("📋 Submit Paper Order")
        if submitted:
            result = service.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=order_type,
                limit_price=limit_price if limit_price > 0 else None,
                strategy_name=strategy if strategy else None,
            )
            if result.get("status") == "REJECTED":
                st.error(f"❌ Order REJECTED: {result.get('rejection_reason')}")
            else:
                st.success(f"✅ Paper order submitted: {result.get('order_id')} — Status: {result.get('status')}")

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
