"""
Authentication View Component — Trader Login and Registration Page.

Renders modern tabbed Login & Registration desk with persistent user data retention.
"""

from __future__ import annotations

import streamlit as st
from src.auth.service import AuthService, UserAccount


def _get_auth_service() -> AuthService:
    if "auth_service" not in st.session_state:
        st.session_state["auth_service"] = AuthService()
    return st.session_state["auth_service"]


def render_auth_page() -> Optional[UserAccount]:
    """
    Renders login and registration desk.
    Returns authenticated UserAccount if logged in, None otherwise.
    """
    auth_svc = _get_auth_service()

    st.markdown("## 🏛️ Indian Stock Market AI — Trader Portal")
    st.caption("Sign in to your private trading account to access your portfolio, trade options, and retain all practice history.")

    col_center, _ = st.columns([2, 1])
    with col_center:
        tab_login, tab_register = st.tabs(["🔐 Sign In to Trading Account", "📝 Register New Trader Account"])

        with tab_login:
            st.markdown("#### Welcome Back")
            login_ident = st.text_input("Username or Email Address", key="auth_login_ident")
            login_pwd = st.text_input("Password", type="password", key="auth_login_pwd")

            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                if st.button("🚀 Sign In", type="primary", use_container_width=True, key="auth_login_btn"):
                    if not login_ident or not login_pwd:
                        st.error("Please enter both username and password.")
                    else:
                        success, msg, user = auth_svc.login(login_ident, login_pwd)
                        if success and user:
                            st.session_state["authenticated_user"] = user
                            st.session_state["user_id"] = user.id
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")

            with btn_col2:
                # 1-Click Demo Account for quick client demonstration
                if st.button("⚡ Quick Demo Account", use_container_width=True, key="auth_quick_demo_btn", help="Login instantly with a pre-configured practice account"):
                    # Check if demo account exists or register it
                    success, msg, user = auth_svc.login("demotrader", "Demo1234!")
                    if not success:
                        success, msg, user = auth_svc.register(
                            username="demotrader",
                            email="demo@trader.ai",
                            password="Demo1234!",
                            full_name="Professional Demo Trader",
                            starting_capital=1000000.0,
                        )
                    if user:
                        st.session_state["authenticated_user"] = user
                        st.session_state["user_id"] = user.id
                        st.success(f"✅ Logged in as {user.full_name}!")
                        st.rerun()

        with tab_register:
            st.markdown("#### Create Your Personal Paper Trading Account")
            reg_name = st.text_input("Full Name (e.g., Rahul Sharma)", key="auth_reg_name")
            reg_email = st.text_input("Email Address", key="auth_reg_email")
            reg_username = st.text_input("Choose Username", key="auth_reg_user")
            reg_capital = st.number_input(
                "Starting Virtual Capital (₹)",
                min_value=100000.0,
                max_value=50000000.0,
                value=1000000.0,
                step=100000.0,
                key="auth_reg_capital",
                help="Virtual play funds credited to your account for safe practice.",
            )
            reg_pwd1 = st.text_input("Create Password", type="password", key="auth_reg_pwd1")
            reg_pwd2 = st.text_input("Confirm Password", type="password", key="auth_reg_pwd2")

            if st.button("✨ Create Trading Account", type="primary", use_container_width=True, key="auth_register_btn"):
                if not reg_name or not reg_email or not reg_username or not reg_pwd1:
                    st.error("Please fill in all registration fields.")
                elif reg_pwd1 != reg_pwd2:
                    st.error("Passwords do not match. Please re-enter.")
                else:
                    success, msg, user = auth_svc.register(
                        username=reg_username,
                        email=reg_email,
                        password=reg_pwd1,
                        full_name=reg_name,
                        starting_capital=float(reg_capital),
                    )
                    if success and user:
                        st.session_state["authenticated_user"] = user
                        st.session_state["user_id"] = user.id
                        st.success("🎉 Account created successfully! Logging you in...")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    return st.session_state.get("authenticated_user")
