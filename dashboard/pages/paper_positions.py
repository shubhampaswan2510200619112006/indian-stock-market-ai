"""
Streamlit Dashboard Page — Phase 8 Paper Positions & Portfolio.

Displays open positions, closed positions, Greeks, and mark-to-market status.
If market price is unavailable, marks UNAVAILABLE (never fabricated).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on Python path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


import streamlit as st
import pandas as pd

from src.paper_trading.service import PaperTradingService
from dashboard.components.portfolio_pnl_card import render_portfolio_pnl_header


def _get_service() -> PaperTradingService:
    if "paper_service" not in st.session_state:
        st.session_state["paper_service"] = PaperTradingService()
    return st.session_state["paper_service"]


def render_paper_positions_page():
    """Render the paper positions and portfolio tracker page."""
    service = _get_service()

    # Prominent Real-Time P&L Header
    render_portfolio_pnl_header(
        service,
        title="💼 PORTFOLIO & LIVE P&L",
        subtitle="Institutional Mark-to-Market P&L Tracking • Simulated Execution • Verified Marks",
        show_positions_table=False,
        key_prefix="pro_paper_pnl",
    )

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

if __name__ == "__main__":
    st.set_page_config(page_title="Paper Positions", layout="wide")
    render_paper_positions_page()

