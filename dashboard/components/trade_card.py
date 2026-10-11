"""
Trade Card Component for 60-Second Trade Decision Terminal.

Renders an all-in-one institutional-grade Trade Card:
- Direction, confidence, and fired reasons
- Exact contract: strike, expiry, lot size, premium, delta, theta/day, IV, IV percentile
- Strict liquidity validation & rejection banner
- Entry, stop-loss, targets (T1, T2), risk-reward ratio
- Dynamic position sizing (capital & risk % input -> suggested lots & max loss)
- Full statutory NSE transaction cost breakdown (Brokerage, STT, GST, Exchange fee, Stamp duty, SEBI)
- Net P&L after all charges
- Mandatory "Why NOT to take this trade" warning box
- One-click paper trade execution
"""

from __future__ import annotations

import streamlit as st
from datetime import date
from typing import Optional

from src.features.trade_card import (
    TradeIdea,
    build_trade_idea,
    compute_position_sizing,
    calculate_nse_charges,
)
from src.paper_trading.service import PaperTradingService


def render_trade_card(
    idea: TradeIdea,
    service: Optional[PaperTradingService] = None,
    default_capital: float = 500000.0,
    default_risk_pct: float = 1.0,
    card_index: int = 0,
):
    """
    Renders a single Trade Card with complete transparency and execution guardrails.
    """
    key_prefix = f"tc_{idea.id}_{card_index}"

    # Outer Container Styling
    border_color = "#10b981" if idea.is_executable else ("#ef4444" if not idea.liquidity.is_liquid else "#f59e0b")
    status_label = "🟢 EXECUTABLE SETUP" if idea.is_executable else ("🔴 REJECTED: ILLIQUID" if not idea.liquidity.is_liquid else "🟡 CAUTION: SIZING RESTRICTED")

    with st.container():
        st.markdown(
            f"""
            <div style="border: 2px solid {border_color}; border-radius: 12px; padding: 20px; background: rgba(15, 23, 42, 0.7); margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 12px; margin-bottom: 16px;">
                    <div>
                        <span style="font-size: 18px; font-weight: 800; color: #f8fafc;">{idea.strategy_name}</span>
                        <span style="background: rgba(30, 41, 59, 0.9); padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #38bdf8; margin-left: 8px;">
                            {idea.direction}
                        </span>
                    </div>
                    <div>
                        <span style="font-size: 13px; font-weight: 700; padding: 4px 12px; border-radius: 20px; background: {border_color}22; color: {border_color}; border: 1px solid {border_color};">
                            {status_label}
                        </span>
                        <span style="font-size: 13px; color: #94a3b8; margin-left: 10px;">
                            Confidence: <b style="color: #f8fafc;">{idea.confidence_score:.0f}/100</b>
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 1. Why it fired
        st.markdown("**🎯 Why This Trade Fired:**")
        for r in idea.reasons_fired:
            st.markdown(f"- 📈 {r}")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # 2. Exact Contract Specifications
        st.markdown("#### 📜 Exact Contract Specifications")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Strike & Type", f"{idea.contract.strike:,.0f} {idea.contract.option_type.value}", help="Exact strike price and option type.")
            st.caption(f"**Expiry:** {idea.contract.expiry_date.strftime('%d-%b-%Y')}")
        with c2:
            st.metric("LTP / Entry Premium", f"₹{idea.contract.premium:,.2f}", help="Last traded premium / best ask.")
            st.caption(f"**NSE Lot Size:** {idea.contract.lot_size} units")
        with c3:
            delta_val = idea.contract.delta
            st.metric("Delta (Δ)", f"{delta_val:+.2f}", help="Expected change in premium per ₹1 move in spot price.")
            st.caption(f"**Theta (Decay):** -₹{idea.contract.theta_per_day:,.1f}/day/lot")
        with c4:
            st.metric("Implied Volatility", f"{idea.contract.iv*100:.1f}%", help="Annualized implied volatility.")
            st.caption(f"**IV Percentile (IVP):** {idea.contract.iv_percentile:.0f}%")

        # 3. Liquidity Check & Rejection Box
        st.markdown("#### 💧 Liquidity & Spread Safety Check")
        liq_col1, liq_col2, liq_col3 = st.columns(3)
        spread_color = "normal" if idea.liquidity.spread_pct <= 0.035 else "inverse"
        with liq_col1:
            st.metric(
                "Bid-Ask Spread",
                f"{idea.liquidity.spread_pct*100:.2f}%",
                f"Bid ₹{idea.contract.bid:.2f} | Ask ₹{idea.contract.ask:.2f}",
                delta_color=spread_color,
            )
        with liq_col2:
            st.metric("Contract Volume", f"{idea.liquidity.volume:,} contracts")
        with liq_col3:
            st.metric("Open Interest (OI)", f"{idea.liquidity.open_interest:,} contracts")

        if not idea.liquidity.is_liquid:
            st.error(
                "🚨 **OUTRIGHT TRADE REJECTION: ILLIQUID CONTRACT DETECTED**\n\n"
                + "\n".join([f"- 🛑 {reason}" for reason in idea.liquidity.rejection_reasons])
                + "\n\n*Execution is locked to prevent severe slippage disaster.*"
            )

        # 4. Trade Plan & Risk-Reward
        st.markdown("#### 🎯 Trade Plan (Levels & Targets)")
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.markdown(f"**Limit Entry:** `₹{idea.plan.entry_price:,.2f}`")
        with p2:
            st.markdown(f"**Stop-Loss (SL):** `₹{idea.plan.stop_loss:,.2f}` <span style='color: #ef4444; font-size:12px;'>(-{idea.plan.risk_per_share:,.2f} pts)</span>", unsafe_allow_html=True)
        with p3:
            st.markdown(f"**Target 1 (1:{idea.plan.risk_reward_t1}):** `₹{idea.plan.target_1:,.2f}` <span style='color: #10b981; font-size:12px;'>(+{idea.plan.reward_t1_per_share:,.2f} pts)</span>", unsafe_allow_html=True)
        with p4:
            st.markdown(f"**Target 2 (1:{idea.plan.risk_reward_t2}):** `₹{idea.plan.target_2:,.2f}` <span style='color: #10b981; font-size:12px;'>(+{idea.plan.reward_t2_per_share:,.2f} pts)</span>", unsafe_allow_html=True)

        st.divider()

        # 5. Interactive Position Sizing
        st.markdown("#### ⚖️ Dynamic Position Sizing (Capital Protection)")
        sz_col1, sz_col2 = st.columns(2)
        with sz_col1:
            user_capital = st.number_input(
                "Account Capital (₹)",
                min_value=10000.0,
                max_value=100000000.0,
                value=float(default_capital),
                step=50000.0,
                key=f"{key_prefix}_cap",
            )
        with sz_col2:
            user_risk_pct = st.slider(
                "Max Risk Per Trade (%)",
                min_value=0.25,
                max_value=5.0,
                value=float(default_risk_pct),
                step=0.25,
                key=f"{key_prefix}_risk_pct",
                help="Recommended: 1.0% to 2.0% maximum risk per options trade.",
            )

        # Recalculate sizing dynamically
        sizing = compute_position_sizing(
            capital=user_capital,
            risk_pct=user_risk_pct,
            entry_price=idea.plan.entry_price,
            stop_loss=idea.plan.stop_loss,
            lot_size=idea.contract.lot_size,
        )

        res_col1, res_col2, res_col3, res_col4 = st.columns(4)
        with res_col1:
            st.metric("Suggested Lots", f"{sizing.suggested_lots} Lots", f"{sizing.suggested_quantity} Qty")
        with res_col2:
            st.metric("Max Loss Risk", f"₹{sizing.max_loss_rupees:,.2f}", f"{sizing.actual_risk_pct_of_capital:.2f}% of capital")
        with res_col3:
            st.metric("Capital Required", f"₹{sizing.total_capital_deployed:,.2f}")
        with res_col4:
            st.metric("Breakeven Premium", f"₹{sizing.breakeven_price:,.2f}", help="Entry premium + statutory fees per share.")

        # Recalculate NSE Costs dynamically
        calc_lots = max(1, sizing.suggested_lots)
        calc_qty = max(idea.contract.lot_size, sizing.suggested_quantity)
        costs = calculate_nse_charges(
            entry_price=idea.plan.entry_price,
            target_1=idea.plan.target_1,
            target_2=idea.plan.target_2,
            quantity=calc_qty,
            lots=calc_lots,
            is_buy_first=True,
        )

        # 6. Real NSE Transaction Cost Breakdown
        with st.expander("🧾 Real NSE Transaction Cost Breakdown & Net P&L (Click to view full taxes)", expanded=False):
            st.markdown(
                f"""
                <table style="width: 100%; font-size: 13px; border-collapse: collapse; margin-bottom: 12px;">
                    <tr style="border-bottom: 1px solid #334155;">
                        <th style="text-align: left; padding: 6px; color: #94a3b8;">Tax / Fee Component</th>
                        <th style="text-align: right; padding: 6px; color: #94a3b8;">Statutory Rate</th>
                        <th style="text-align: right; padding: 6px; color: #94a3b8;">Amount for {calc_lots} Lot(s)</th>
                    </tr>
                    <tr style="border-bottom: 1px solid #1e293b;">
                        <td style="padding: 6px;">Brokerage (Buy + Sell Orders)</td>
                        <td style="text-align: right; padding: 6px;">₹20 / order flat</td>
                        <td style="text-align: right; padding: 6px; font-weight: 600;">₹{costs.brokerage:,.2f}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #1e293b;">
                        <td style="padding: 6px;">Securities Transaction Tax (STT)</td>
                        <td style="text-align: right; padding: 6px;">0.0625% on Sell Turnover</td>
                        <td style="text-align: right; padding: 6px; font-weight: 600;">₹{costs.stt:,.2f}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #1e293b;">
                        <td style="padding: 6px;">NSE Exchange Turnover Fee</td>
                        <td style="text-align: right; padding: 6px;">0.053% on Total Turnover</td>
                        <td style="text-align: right; padding: 6px; font-weight: 600;">₹{costs.exchange_fee:,.2f}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #1e293b;">
                        <td style="padding: 6px;">Goods & Services Tax (GST)</td>
                        <td style="text-align: right; padding: 6px;">18% on (Brokerage + Exchange)</td>
                        <td style="text-align: right; padding: 6px; font-weight: 600;">₹{costs.gst:,.2f}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #1e293b;">
                        <td style="padding: 6px;">SEBI Turnover Charge</td>
                        <td style="text-align: right; padding: 6px;">₹10 per crore (0.0001%)</td>
                        <td style="text-align: right; padding: 6px; font-weight: 600;">₹{costs.sebi_charges:,.2f}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #1e293b;">
                        <td style="padding: 6px;">Stamp Duty</td>
                        <td style="text-align: right; padding: 6px;">0.003% on Buy Turnover</td>
                        <td style="text-align: right; padding: 6px; font-weight: 600;">₹{costs.stamp_duty:,.2f}</td>
                    </tr>
                    <tr style="border-top: 2px solid #334155; font-weight: bold; background: rgba(30, 41, 59, 0.4);">
                        <td style="padding: 8px; color: #f8fafc;">Total Round-Trip Statutory Charges</td>
                        <td style="text-align: right; padding: 8px;">—</td>
                        <td style="text-align: right; padding: 8px; color: #f43f5e;">₹{costs.total_charges:,.2f}</td>
                    </tr>
                </table>
                """,
                unsafe_allow_html=True,
            )

            pnl_c1, pnl_c2 = st.columns(2)
            with pnl_c1:
                st.markdown(
                    f"""
                    <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 8px; padding: 10px;">
                        <div style="font-size: 12px; color: #a7f3d0;">TARGET 1 NET REALIZATION</div>
                        <div style="font-size: 16px; font-weight: 800; color: #34d399;">₹{costs.net_t1_pnl:,.2f}</div>
                        <div style="font-size: 11px; color: #94a3b8;">Gross: ₹{costs.gross_t1_pnl:,.2f} &nbsp;|&nbsp; Tax: -₹{costs.total_charges:,.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with pnl_c2:
                st.markdown(
                    f"""
                    <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #059669; border-radius: 8px; padding: 10px;">
                        <div style="font-size: 12px; color: #a7f3d0;">TARGET 2 NET REALIZATION</div>
                        <div style="font-size: 16px; font-weight: 800; color: #10b981;">₹{costs.net_t2_pnl:,.2f}</div>
                        <div style="font-size: 11px; color: #94a3b8;">Gross: ₹{costs.gross_t2_pnl:,.2f} &nbsp;|&nbsp; Tax: -₹{costs.total_charges:,.2f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # 7. MANDATORY "Why NOT to take this trade" Warning Box
        st.markdown(
            f"""
            <div style="background: rgba(239, 68, 68, 0.08); border: 1.5px solid #dc2626; border-radius: 8px; padding: 14px 18px; margin: 16px 0;">
                <div style="display: flex; align-items: center; gap: 8px; color: #f87171; font-weight: 800; font-size: 14px; margin-bottom: 6px;">
                    <span>⚠️ WHY NOT TO TAKE THIS TRADE (MANDATORY HONEST APPRAISAL)</span>
                </div>
                <div style="color: #cbd5e1; font-size: 13px; line-height: 1.5;">
                    {"".join([f"<p style='margin: 4px 0;'>• <b>{warning}</b></p>" for warning in idea.why_not_to_take])}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 8. One-Click Paper Trade Execution
        can_execute = idea.is_executable and (sizing.suggested_lots > 0)
        
        btn_label = f"🚀 Execute Paper Trade ({sizing.suggested_lots} Lots / {sizing.suggested_quantity} Qty @ ₹{idea.plan.entry_price:,.2f})" if can_execute else "🔒 Execution Disabled (Rejected by Safety Limits)"
        
        if st.button(
            btn_label,
            key=f"{key_prefix}_exec_btn",
            disabled=not can_execute,
            use_container_width=True,
            type="primary" if can_execute else "secondary",
        ):
            if service is not None:
                with st.spinner("Submitting order through Paper Risk Gate..."):
                    try:
                        res = service.place_order(
                            symbol=idea.symbol,
                            side="BUY",
                            quantity=sizing.suggested_quantity,
                            order_type="LIMIT",
                            limit_price=idea.plan.entry_price,
                            stop_price=idea.plan.stop_loss,
                            instrument_type="OPTION",
                            strategy_name=idea.strategy_name,
                            strike=idea.contract.strike,
                            expiry_date=idea.contract.expiry_date.strftime("%Y-%m-%d"),
                            option_type=idea.contract.option_type.value,
                        )
                        if res.get("status") in ["ACCEPTED", "SUBMITTED", "PENDING"]:
                            st.success(f"✅ **Paper Trade Placed Successfully!** Order ID: `{res.get('order_id')}` | Session: `{res.get('session_id')}`")
                        else:
                            st.warning(f"⚠️ **Order Status:** {res.get('status')} — {res.get('message', 'Check paper positions.')}")
                    except Exception as e:
                        st.error(f"❌ Execution Error: {e}")
            else:
                st.info("ℹ️ Paper Trading Service is in simulation mode. Connect live service to persist trades.")
