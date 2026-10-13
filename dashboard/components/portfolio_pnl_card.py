"""
Executive Real-Time Portfolio P&L Card Component.

Displays prominent, color-coded, institutional-grade profit and loss metrics:
- Overall Total P&L (₹ and %) with dynamic profit green / loss red styling
- Invested Capital vs Current Portfolio Value
- Booked / Realized P&L vs Open / Unrealized P&L
- Available Trading Margin / Cash
- Individual position cards with live LTP, P&L %, and 1-Click Square-Off / Exit
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
from typing import Optional

from src.paper_trading.service import PaperTradingService


def render_portfolio_pnl_header(
    service: PaperTradingService,
    title: str = "💼 Portfolio & Live P&L",
    subtitle: str = "Real-time Mark-to-Market Profit/Loss tracking across your active options and index trades",
    show_positions_table: bool = True,
    key_prefix: str = "pnl_hdr",
):
    """
    Renders an institutional real-time P&L card and position desk using native Streamlit widgets.
    Completely zero raw HTML strings to guarantee 100% immunity from markdown code-block escaping.
    """
    summary = service.get_portfolio_summary()
    equity = float(summary.get("equity", 1_000_000.0))
    cash = float(summary.get("cash", 1_000_000.0))
    realized_pnl = float(summary.get("realized_pnl", 0.0))
    unrealized_pnl = float(summary.get("unrealized_pnl", 0.0))

    initial_capital = 1_000_000.0
    total_pnl = realized_pnl + unrealized_pnl
    total_pnl_pct = (total_pnl / initial_capital) * 100.0 if initial_capital > 0 else 0.0

    # Get positions
    open_positions_data = service.get_positions(status="OPEN")
    open_positions = open_positions_data.get("positions", [])

    invested_value = 0.0
    current_market_value = 0.0
    for p in open_positions:
        entry = float(p.get("avg_entry_price", 0.0))
        qty = float(p.get("quantity", 0.0))
        curr = float(p.get("current_price", entry))
        invested_value += entry * qty
        current_market_value += curr * qty

    is_profit = total_pnl >= 0.0
    pnl_sign = "+" if is_profit else ""

    # Top Header & Total P&L Banner
    with st.container():
        c_title, c_tot = st.columns([2.5, 1.5])
        with c_title:
            st.markdown(f"### {title}")
            st.caption(subtitle)
        with c_tot:
            st.metric(
                label="TOTAL P&L (ALL TIME)",
                value=f"{pnl_sign}₹{total_pnl:,.2f}",
                delta=f"{pnl_sign}{total_pnl_pct:.2f}%",
            )

        st.divider()

        # 5 Key Financial Metric Cards using native Streamlit metrics
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("💼 Invested Amount", f"₹{invested_value:,.2f}")
        c2.metric("📈 Current Value", f"₹{current_market_value:,.2f}")
        unrealized_delta = f"{(unrealized_pnl / invested_value * 100):+.2f}%" if invested_value > 0 else "0.00%"
        c3.metric(
            "⚡ Unrealized P&L",
            f"{'+' if unrealized_pnl >= 0 else ''}₹{unrealized_pnl:,.2f}",
            delta=unrealized_delta,
        )
        c4.metric(
            "🔒 Booked P&L",
            f"{'+' if realized_pnl >= 0 else ''}₹{realized_pnl:,.2f}",
        )
        c5.metric("🏦 Available Cash", f"₹{cash:,.2f}")

    if not show_positions_table:
        return

    st.divider()

    # Render Positions
    st.markdown(f"#### 🟢 Active Open Positions ({len(open_positions)})")
    if not open_positions:
        st.info("ℹ️ No active trades currently open. You can browse strikes in the **Option Chain** and buy with 1-click execution!")
        return

    for idx, pos in enumerate(open_positions):
        pid = pos.get("position_id")
        sym = pos.get("symbol", "N/A")
        side = pos.get("side", "BUY")
        qty = int(pos.get("quantity", 0))
        entry = float(pos.get("avg_entry_price", 0.0))
        curr = float(pos.get("current_price", entry))
        pnl = float(pos.get("unrealized_pnl", 0.0))
        invested = entry * qty
        pnl_pct = (pnl / invested) * 100.0 if invested > 0 else 0.0

        is_ce = "CE" in sym
        is_pe = "PE" in sym
        type_badge = "🟢 CALL" if is_ce else ("🔴 PUT" if is_pe else "🏛️ INDEX")

        with st.container():
            col_info, col_pnl = st.columns([3, 1.5])
            with col_info:
                st.markdown(f"**{type_badge} {sym}** &nbsp; `ID: {pid}`")
                st.caption(
                    f"Quantity: **{qty} shares** &nbsp;|&nbsp; "
                    f"Buy Price: **₹{entry:,.2f}** &nbsp;|&nbsp; "
                    f"Market LTP: **₹{curr:,.2f}** &nbsp;|&nbsp; "
                    f"Invested: **₹{invested:,.2f}**"
                )
            with col_pnl:
                st.metric(
                    "Position P&L",
                    f"{'+' if pnl >= 0 else ''}₹{pnl:,.2f}",
                    delta=f"{'+' if pnl >= 0 else ''}{pnl_pct:.2f}%",
                )

            col_exit, _ = st.columns([2, 3])
            with col_exit:
                if st.button(
                    f"🚪 Square Off (Exit) {sym}",
                    key=f"{key_prefix}_exit_{pid}_{idx}",
                    type="secondary",
                    use_container_width=True,
                ):
                    res = service.close_position(pid)
                    if res.get("status") == "REJECTED":
                        st.error(f"Could not exit: {res.get('rejection_reason')}")
                    else:
                        st.success(f"Position {sym} squared off successfully! Realized P&L booked.")
                        st.rerun()
