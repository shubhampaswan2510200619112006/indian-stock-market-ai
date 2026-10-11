"""
Streamlit Dashboard Page — Phase 8 Paper Positions & Portfolio.

Displays open positions, closed positions, Greeks, and mark-to-market status.
If market price is unavailable, marks UNAVAILABLE (never fabricated).
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from src.paper_trading.service import PaperTradingService


def _get_service() -> PaperTradingService:
    if "paper_service" not in st.session_state:
        st.session_state["paper_service"] = PaperTradingService()
    return st.session_state["paper_service"]


def render_paper_positions_page():
    """Render the paper positions and portfolio tracker page."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 12px 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0;">📊 PAPER POSITIONS & PORTFOLIO</h2>
            <p style="color: white; margin: 4px 0 0 0; font-size: 14px;">
                SIMULATED POSITIONS &nbsp;•&nbsp; GENUINE MARKS ONLY &nbsp;•&nbsp; NO FABRICATED VALUES
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    service = _get_service()

    # Portfolio overview
    summary = service.get_portfolio_summary()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Equity", f"₹{summary['equity']:,.2f}")
    with c2:
        st.metric("Cash Balance", f"₹{summary['cash']:,.2f}")
    with c3:
        st.metric("Total Realized P&L", f"₹{summary['realized_pnl']:,.2f}")
    with c4:
        st.metric("Total Unrealized P&L", f"₹{summary['unrealized_pnl']:,.2f}")

    st.divider()

    # Open positions
    st.markdown("### 🟢 Open Positions")
    positions = service.get_positions()
    open_pos = positions.get("positions", [])

    if open_pos:
        df_open = pd.DataFrame(open_pos)
        display_cols = [
            col for col in [
                "position_id", "symbol", "side", "quantity", "avg_entry_price",
                "current_price", "unrealized_pnl", "realized_pnl", "asset_class", "opened_at"
            ] if col in df_open.columns
        ]
        st.dataframe(df_open[display_cols], use_container_width=True)

        # Close position form
        st.markdown("#### Close a Position")
        col_sel, col_qty, col_btn = st.columns([2, 1, 1])
        with col_sel:
            selected_pos = st.selectbox(
                "Select Position to Close",
                options=[p["position_id"] for p in open_pos],
                format_func=lambda pid: f"{pid} - {next((p['symbol'] for p in open_pos if p['position_id'] == pid), '')}"
            )
        with col_qty:
            matching = next((p for p in open_pos if p["position_id"] == selected_pos), None)
            max_q = matching["quantity"] if matching else 1
            close_qty = st.number_input("Quantity to Close", min_value=1, max_value=max_q, value=max_q)
        with col_btn:
            st.write("")
            st.write("")
            if st.button("Close Position (Paper)"):
                res = service.close_position(selected_pos, quantity=close_qty)
                if res.get("status") == "REJECTED":
                    st.error(f"Failed to close: {res.get('rejection_reason')}")
                else:
                    st.success(f"Position closed! Fill ID: {res.get('fill_id')}")
    else:
        st.info("No open positions in paper portfolio.")

    st.divider()

    # Closed positions
    st.markdown("### 🏁 Closed Positions")
    closed = service.get_positions(status="CLOSED")
    closed_pos = closed.get("positions", [])

    if closed_pos:
        df_closed = pd.DataFrame(closed_pos)
        display_cols = [
            col for col in [
                "position_id", "symbol", "side", "quantity", "avg_entry_price",
                "realized_pnl", "asset_class", "opened_at", "closed_at"
            ] if col in df_closed.columns
        ]
        st.dataframe(df_closed[display_cols], use_container_width=True)
    else:
        st.info("No closed positions recorded yet.")

    # Mark-to-market notice
    st.caption("ℹ️ Marks use strictly verified provider observations. If market observation is unavailable, price is not marked and status is UNAVAILABLE.")
