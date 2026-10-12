"""
Groww & Zerodha Style Real-Time Portfolio P&L Card Component.

Displays prominent, color-coded, retail-broker-grade profit and loss metrics:
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


def render_groww_pnl_header(
    service: PaperTradingService,
    title: str = "💼 Portfolio & Live P&L",
    subtitle: str = "Real-time Mark-to-Market Profit/Loss tracking across your active options and index trades",
    show_positions_table: bool = True,
    key_prefix: str = "pnl_hdr",
):
    """
    Renders an institutional retail-broker style P&L card inspired by Groww and Zerodha Kite.
    """
    summary = service.get_portfolio_summary()
    equity = float(summary.get("equity", 1_000_000.0))
    cash = float(summary.get("cash", 1_000_000.0))
    realized_pnl = float(summary.get("realized_pnl", 0.0))
    unrealized_pnl = float(summary.get("unrealized_pnl", 0.0))

    initial_capital = 1_000_000.0  # ₹10 Lakhs standard demo capital
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

    # Color themes
    is_profit = total_pnl >= 0.0
    pnl_sign = "+" if is_profit else ""
    pnl_text_color = "#10b981" if is_profit else "#ef4444"
    card_bg_gradient = (
        "linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(15, 23, 42, 0.95) 100%)"
        if is_profit
        else "linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(15, 23, 42, 0.95) 100%)"
    )
    border_color = "rgba(16, 185, 129, 0.4)" if is_profit else "rgba(239, 68, 68, 0.4)"

    # Header Card
    st.markdown(
        f"""
        <div style="
            background: {card_bg_gradient};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                <div>
                    <div style="font-size: 13px; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                        {title}
                    </div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 2px;">
                        {subtitle}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">
                        TOTAL P&amp;L (ALL TIME)
                    </div>
                    <div style="font-size: 28px; font-weight: 800; color: {pnl_text_color}; line-height: 1.1; font-family: monospace;">
                        {pnl_sign}₹{total_pnl:,.2f}
                        <span style="font-size: 16px; font-weight: 700; margin-left: 6px;">
                            ({pnl_sign}{total_pnl_pct:.2f}%)
                        </span>
                    </div>
                </div>
            </div>
            
            <div style="
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
                gap: 12px;
                margin-top: 18px;
                padding-top: 14px;
                border-top: 1px solid rgba(255, 255, 255, 0.08);
            ">
                <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 8px;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">💼 Invested Amount</div>
                    <div style="font-size: 16px; font-weight: 700; color: #f8fafc; font-family: monospace; margin-top: 2px;">
                        ₹{invested_value:,.2f}
                    </div>
                </div>
                <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 8px;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">📈 Current Value</div>
                    <div style="font-size: 16px; font-weight: 700; color: #38bdf8; font-family: monospace; margin-top: 2px;">
                        ₹{current_market_value:,.2f}
                    </div>
                </div>
                <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 8px;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">⚡ Unrealized P&amp;L</div>
                    <div style="font-size: 16px; font-weight: 700; color: {'#10b981' if unrealized_pnl >= 0 else '#ef4444'}; font-family: monospace; margin-top: 2px;">
                        {'+' if unrealized_pnl >= 0 else ''}₹{unrealized_pnl:,.2f}
                    </div>
                </div>
                <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 8px;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">🔒 Booked (Realized) P&amp;L</div>
                    <div style="font-size: 16px; font-weight: 700; color: {'#10b981' if realized_pnl >= 0 else '#ef4444'}; font-family: monospace; margin-top: 2px;">
                        {'+' if realized_pnl >= 0 else ''}₹{realized_pnl:,.2f}
                    </div>
                </div>
                <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 8px;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">🏦 Available Cash Margin</div>
                    <div style="font-size: 16px; font-weight: 700; color: #f8fafc; font-family: monospace; margin-top: 2px;">
                        ₹{cash:,.2f}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not show_positions_table:
        return

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

        pos_profit = pnl >= 0
        pos_pnl_color = "#10b981" if pos_profit else "#ef4444"
        pos_sign = "+" if pos_profit else ""

        # Option type badge (CE / PE)
        is_ce = "CE" in sym
        is_pe = "PE" in sym
        type_badge = "🟢 CALL" if is_ce else ("🔴 PUT" if is_pe else "🏛️ INDEX")

        with st.container():
            st.markdown(
                f"""
                <div style="
                    background: #1e293b;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    padding: 14px 18px;
                    margin-bottom: 12px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                        <div>
                            <span style="font-size: 12px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 2px 8px; border-radius: 4px; font-weight: 700; margin-right: 8px;">
                                {type_badge}
                            </span>
                            <span style="font-size: 16px; font-weight: 700; color: #f8fafc;">
                                {sym}
                            </span>
                            <span style="font-size: 11px; color: #64748b; margin-left: 8px;">
                                ID: {pid}
                            </span>
                        </div>
                        <div style="text-align: right; font-family: monospace;">
                            <span style="font-size: 18px; font-weight: 800; color: {pos_pnl_color};">
                                {pos_sign}₹{pnl:,.2f}
                            </span>
                            <span style="font-size: 12px; font-weight: 700; color: {pos_pnl_color}; margin-left: 6px;">
                                ({pos_sign}{pnl_pct:.2f}%)
                            </span>
                        </div>
                    </div>
                    
                    <div style="
                        display: flex;
                        gap: 24px;
                        margin-top: 10px;
                        font-size: 12px;
                        color: #94a3b8;
                        flex-wrap: wrap;
                    ">
                        <div>Quantity: <b style="color: #f8fafc;">{qty} shares</b></div>
                        <div>Buy Price: <b style="color: #f8fafc;">₹{entry:,.2f}</b></div>
                        <div>Market LTP: <b style="color: #38bdf8;">₹{curr:,.2f}</b></div>
                        <div>Invested: <b style="color: #f8fafc;">₹{invested:,.2f}</b></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_exit, col_space = st.columns([1.5, 4])
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
