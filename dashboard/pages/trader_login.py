"""
Trader Login & Institutional Account Management Page.
Provides 1-click access to verified trader profiles (Prop Desk, Quant Lead, Scalper, Retail)
and custom broker gateway credential authentication (Zerodha Kite, Angel One, Dhan, Paper Sandbox).
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is on Python path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st
from src.paper_trading.service import PaperTradingService


DEMO_PROFILES = [
    {
        "id": "rahul_sharma",
        "name": "Rahul Sharma",
        "role": "Senior Derivatives Trader (HNI)",
        "badge": "🏆 Prop Desk",
        "avatar": "👨‍💼",
        "capital": 2_500_000.0,
        "broker": "Zerodha Kite Connect (Simulated API)",
        "description": "Intraday directional index buyer & momentum options breakout specialist. High-conviction risk model.",
        "risk_tier": "Aggressive Alpha (Max ₹1.5L / trade)",
    },
    {
        "id": "dr_vikram_sen",
        "name": "Dr. Vikram Sen",
        "role": "Chief Quantitative Strategist",
        "badge": "🔬 Institutional Quant",
        "avatar": "👨‍🔬",
        "capital": 10_000_000.0,
        "broker": "Interactive Brokers / NSE Colo Direct",
        "description": "Multi-leg delta-neutral spreads, volatility skew arbitrage, and algorithmic statistical mean-reversion.",
        "risk_tier": "Systematic Arbitrage (Max ₹5.0L / trade)",
    },
    {
        "id": "priya_patel",
        "name": "Priya Patel",
        "role": "High-Frequency Options Scalper",
        "badge": "⚡ Gamma Scalper",
        "avatar": "👩‍💻",
        "capital": 1_000_000.0,
        "broker": "Dhan HQ SmartAPI (Simulated)",
        "description": "Fast 0DTE / weekly options gamma scalping on BankNifty & FinNifty opening volatility squeezes.",
        "risk_tier": "Intraday Momentum (Max ₹75k / trade)",
    },
    {
        "id": "arjun_verma",
        "name": "Arjun Verma",
        "role": "Retail Derivatives Learner",
        "badge": "🛡️ Conservative",
        "avatar": "🧑‍🎓",
        "capital": 200_000.0,
        "broker": "Angel One SmartAPI (Paper Sandbox)",
        "description": "Defined-risk credit spreads, bull call ladders, and mechanical risk management with verified rules.",
        "risk_tier": "Conservative (Max ₹15k / trade)",
    },
]


def init_user_session():
    """Ensure session state contains user credentials."""
    if "current_user" not in st.session_state:
        # Default to Rahul Sharma
        st.session_state["current_user"] = DEMO_PROFILES[0]
        st.session_state["is_logged_in"] = True
        st.session_state["login_timestamp"] = datetime.now().strftime("%I:%M %p IST")


def get_current_user() -> dict:
    init_user_session()
    return st.session_state.get("current_user", DEMO_PROFILES[0])


def render_trader_login_page(service: PaperTradingService):
    """Render the full Trader Authentication & Profile Management interface."""
    init_user_session()
    curr_user = get_current_user()
    is_logged_in = st.session_state.get("is_logged_in", True)

    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(16, 23, 40, 0.95), rgba(13, 20, 36, 0.98)); border: 1px solid rgba(212, 175, 55, 0.35); border-radius: 14px; padding: 22px 26px; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <div style="font-size: 11px; font-family: monospace; font-weight: 700; color: #d4af37; text-transform: uppercase; letter-spacing: 1px;">
                        INSTITUTIONAL ACCESS GATEWAY
                    </div>
                    <h2 style="color: white; margin: 4px 0 0 0; font-size: 24px; font-weight: 800;">
                        🔐 Trader Identity & Broker Gateway Terminal
                    </h2>
                    <p style="color: #94a3b8; margin: 6px 0 0 0; font-size: 13px;">
                        Switch between verified institutional trader desks, monitor simulated margin allocations, or connect your broker credentials.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Top Status Banner: Currently Authenticated Trader
    if is_logged_in and curr_user:
        c_badge, c_stats, c_logout = st.columns([2.5, 2.5, 1])
        with c_badge:
            st.markdown(
                f"""
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 12px; padding: 14px 18px; display: flex; align-items: center; gap: 14px;">
                    <div style="font-size: 36px;">{curr_user.get('avatar', '👤')}</div>
                    <div>
                        <div style="font-size: 12px; color: #10b981; font-weight: 700; font-family: monospace;">
                            ● ACTIVE TERMINAL SESSION ({curr_user.get('badge')})
                        </div>
                        <div style="font-size: 18px; font-weight: 800; color: #f8fafc;">
                            {curr_user.get('name')}
                        </div>
                        <div style="font-size: 12px; color: #94a3b8;">
                            {curr_user.get('role')}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_stats:
            equity = service.portfolio.get_equity()
            cash = service.portfolio.cash
            st.markdown(
                f"""
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px 18px;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">
                        Allocated Margin & Gateway
                    </div>
                    <div style="font-size: 18px; font-weight: 800; color: #38bdf8; font-family: monospace; margin-top: 2px;">
                        ₹{cash:,.2f}
                    </div>
                    <div style="font-size: 11px; color: #64748b; margin-top: 2px;">
                        Gateway: <span style="color: #cbd5e1;">{curr_user.get('broker')}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_logout:
            st.write("")
            st.write("")
            if st.button("🚪 Logout Session", use_container_width=True, key="trader_logout_btn"):
                st.session_state["is_logged_in"] = False
                st.session_state["current_user"] = None
                st.toast("Logged out of active terminal session.", icon="👋")
                st.rerun()

    st.markdown("### 🏢 Instant 1-Click Institutional Demo Desks")
    st.caption("Select any preset profile to instantly load its specialized risk parameters, capital allocation, and trading desk configuration.")

    cols = st.columns(4)
    for i, prof in enumerate(DEMO_PROFILES):
        with cols[i]:
            is_active = (curr_user and curr_user.get("id") == prof["id"])
            border_style = "2px solid #d4af37" if is_active else "1px solid rgba(255,255,255,0.08)"
            bg_style = "rgba(212, 175, 55, 0.08)" if is_active else "rgba(15, 23, 42, 0.8)"

            st.markdown(
                f"""
                <div style="background: {bg_style}; border: {border_style}; border-radius: 12px; padding: 16px; margin-bottom: 12px; min-height: 230px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 26px;">{prof['avatar']}</span>
                            <span style="font-size: 10px; font-family: monospace; background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 2px 6px; border-radius: 4px; font-weight: 700;">
                                {prof['badge']}
                            </span>
                        </div>
                        <div style="font-size: 15px; font-weight: 800; color: #f8fafc; margin-top: 8px;">
                            {prof['name']}
                        </div>
                        <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">
                            {prof['role']}
                        </div>
                        <div style="font-size: 13px; font-weight: 700; color: #10b981; font-family: monospace; margin-top: 6px;">
                            Capital: ₹{prof['capital']:,.0f}
                        </div>
                        <div style="font-size: 11px; color: #64748b; margin-top: 6px; line-height: 1.4;">
                            {prof['description']}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            btn_label = "✅ Active Desk" if is_active else f"⚡ Switch to {prof['name'].split()[0]}"
            if st.button(btn_label, key=f"switch_prof_{prof['id']}", use_container_width=True, disabled=is_active):
                st.session_state["current_user"] = prof
                st.session_state["is_logged_in"] = True
                st.session_state["login_timestamp"] = datetime.now().strftime("%I:%M %p IST")
                # Update service capital
                service.portfolio.cash = prof["capital"]
                service.portfolio.initial_capital = prof["capital"]
                st.toast(f"Switched to {prof['name']} with ₹{prof['capital']:,.0f} capital!", icon="🚀")
                st.rerun()

    st.divider()

    # Custom Credential Login & Broker API Gateway Form
    st.markdown("### 🔑 Custom Client Login & Broker Gateway Setup")
    st.caption("Authenticate with your custom trader ID or link a simulated Indian broker sandbox.")

    with st.container():
        c_form1, c_form2 = st.columns(2)
        with c_form1:
            custom_id = st.text_input("Trader ID / NSE Client Code", value="NSE-PRO-84920", key="cust_trader_id")
            custom_pwd = st.text_input("Password / Access Secret", value="••••••••••••", type="password", key="cust_pwd")
            custom_name = st.text_input("Trader Full Name", value="Institutional Trader", key="cust_name")

        with c_form2:
            broker_choice = st.selectbox(
                "Select Broker API Gateway",
                [
                    "Zerodha Kite Connect (Simulated OAuth 2.0)",
                    "Angel One SmartAPI (Mock TOTP)",
                    "Dhan HQ Fast API (Direct Sub-Millisecond)",
                    "Groww Paper Trading Gateway",
                    "Direct NSE/BSE Institutional Colo Sandbox",
                ],
                key="cust_broker_choice",
            )
            margin_input = st.number_input(
                "Initial Virtual Margin (₹)",
                min_value=50_000.0,
                max_value=100_000_000.0,
                value=2_000_000.0,
                step=100_000.0,
                key="cust_margin_input",
            )
            totp_pin = st.text_input("6-Digit TOTP / 2FA Authenticator Code", value="492817", key="cust_totp")

        col_act, col_msg = st.columns([1.5, 3])
        with col_act:
            if st.button("🚀 Connect & Authenticate Terminal", type="primary", use_container_width=True, key="cust_login_btn"):
                new_profile = {
                    "id": f"custom_{custom_id.lower().replace('-', '_')}",
                    "name": custom_name,
                    "role": f"Authenticated Trader ({custom_id})",
                    "badge": "🔒 Custom Desk",
                    "avatar": "🛡️",
                    "capital": float(margin_input),
                    "broker": broker_choice,
                    "description": f"Custom authenticated session connected to {broker_choice}.",
                    "risk_tier": "Custom Risk Model",
                }
                st.session_state["current_user"] = new_profile
                st.session_state["is_logged_in"] = True
                st.session_state["login_timestamp"] = datetime.now().strftime("%I:%M %p IST")
                service.portfolio.cash = float(margin_input)
                service.portfolio.initial_capital = float(margin_input)
                st.toast(f"Successfully authenticated as {custom_name}! Margin: ₹{margin_input:,.2f}", icon="🎉")
                st.rerun()

        with col_msg:
            st.info("ℹ️ **Security Notice**: All sessions are simulated for algorithmic validation. No live exchange order flow is routed without institutional SEBI clearance.")
