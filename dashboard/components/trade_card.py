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
All rendered via native Streamlit widgets to eliminate any markdown code escaping bugs.
"""

from __future__ import annotations

import pandas as pd
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

    with st.container():
        # 1. Header with Badge & Status
        status_label = "🟢 EXECUTABLE SETUP" if idea.is_executable else ("🔴 REJECTED: ILLIQUID" if not idea.liquidity.is_liquid else "🟡 CAUTION: SIZING RESTRICTED")
        
        st.markdown(f"### {idea.strategy_name} &nbsp; `{idea.direction}`")
        st.caption(f"**Setup Status:** {status_label} &nbsp;|&nbsp; **Model Confidence:** {idea.confidence_score:.0f}/100")

        # 2. Why it fired
        st.markdown("**🎯 Why This Trade Fired:**")
        for r in idea.reasons_fired:
            st.markdown(f"- 📈 {r}")

        st.divider()

        # 3. Exact Contract Specifications
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

        # 4. Liquidity Check & Rejection Box
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
            reasons_md = "\n".join([f"- 🛑 {reason}" for reason in idea.liquidity.rejection_reasons])
            st.error(
                f"🚨 **OUTRIGHT TRADE REJECTION: ILLIQUID CONTRACT DETECTED**\n\n"
                f"{reasons_md}\n\n"
                f"*Execution is locked to prevent severe slippage disaster.*"
            )

        # 5. Trade Plan & Risk-Reward
        st.markdown("#### 🎯 Trade Plan (Levels & Targets)")
        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.metric("Limit Entry", f"₹{idea.plan.entry_price:,.2f}")
        with p2:
            st.metric(
                "Stop-Loss (SL)",
                f"₹{idea.plan.stop_loss:,.2f}",
                f"-₹{idea.plan.risk_per_share:,.2f} pts",
                delta_color="inverse",
            )
        with p3:
            st.metric(
                f"Target 1 (1:{idea.plan.risk_reward_t1})",
                f"₹{idea.plan.target_1:,.2f}",
                f"+₹{idea.plan.reward_t1_per_share:,.2f} pts",
            )
        with p4:
            st.metric(
                f"Target 2 (1:{idea.plan.risk_reward_t2})",
                f"₹{idea.plan.target_2:,.2f}",
                f"+₹{idea.plan.reward_t2_per_share:,.2f} pts",
            )

        st.divider()

        # 6. Interactive Position Sizing
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

        # 7. Real NSE Transaction Cost Breakdown
        with st.expander("🧾 Real NSE Transaction Cost Breakdown & Net P&L", expanded=False):
            tax_rows = [
                {"Tax / Charge Component": "Brokerage (Buy + Sell)", "Statutory Rate": "₹20 / order flat", "Amount (₹)": f"₹{costs.brokerage:,.2f}"},
                {"Tax / Charge Component": "Securities Transaction Tax (STT)", "Statutory Rate": "0.0625% on Sell Turnover", "Amount (₹)": f"₹{costs.stt:,.2f}"},
                {"Tax / Charge Component": "NSE Exchange Turnover Fee", "Statutory Rate": "0.053% on Total Turnover", "Amount (₹)": f"₹{costs.exchange_fee:,.2f}"},
                {"Tax / Charge Component": "Goods & Services Tax (GST)", "Statutory Rate": "18% on (Brokerage + Exchange)", "Amount (₹)": f"₹{costs.gst:,.2f}"},
                {"Tax / Charge Component": "SEBI Turnover Charge", "Statutory Rate": "₹10 per crore (0.0001%)", "Amount (₹)": f"₹{costs.sebi_charges:,.2f}"},
                {"Tax / Charge Component": "Stamp Duty", "Statutory Rate": "0.003% on Buy Turnover", "Amount (₹)": f"₹{costs.stamp_duty:,.2f}"},
                {"Tax / Charge Component": "TOTAL ROUND-TRIP CHARGES", "Statutory Rate": "All Statutory Taxes & Fees", "Amount (₹)": f"₹{costs.total_charges:,.2f}"},
            ]
            st.dataframe(pd.DataFrame(tax_rows), use_container_width=True, hide_index=True)

            pnl_c1, pnl_c2 = st.columns(2)
            with pnl_c1:
                st.metric(
                    "TARGET 1 NET REALIZATION",
                    f"₹{costs.net_t1_pnl:,.2f}",
                    f"Gross ₹{costs.gross_t1_pnl:,.2f} | Taxes -₹{costs.total_charges:,.2f}",
                )
            with pnl_c2:
                st.metric(
                    "TARGET 2 NET REALIZATION",
                    f"₹{costs.net_t2_pnl:,.2f}",
                    f"Gross ₹{costs.gross_t2_pnl:,.2f} | Taxes -₹{costs.total_charges:,.2f}",
                )

        # 8. MANDATORY "Why NOT to take this trade" Warning Box
        why_not_bullets = "\n".join([f"- **{warning}**" for warning in idea.why_not_to_take])
        st.warning(
            f"### ⚠️ WHY NOT TO TAKE THIS TRADE (MANDATORY HONEST APPRAISAL)\n\n"
            f"{why_not_bullets}"
        )

        # 9. One-Click Paper Trade Execution
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
        
        st.markdown("---")
