"""
Indian Stock Market AI — Master Unified Trading Platform.
Supports seamless toggle between Beginner Mode (Guided, Educational, Essential)
and Pro Mode (Dense, Institutional, Quant Desks).
Shares identical backend, market data, portfolio, and safety invariants.
"""

import sys
from pathlib import Path

# Ensure project root is on the Python path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from typing import Optional
import streamlit as st

from src.utils.config import get_config
from src.utils.time_utils import is_market_open, now_ist
from dashboard.components.theme import inject_custom_theme
from dashboard.components.ui_mode import get_current_ui_mode, render_mode_switcher_sidebar
from src.paper_trading.service import PaperTradingService

# Page configuration — must be first Streamlit command
st.set_page_config(
    page_title="Indian Stock Market AI — Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database schema if not present
try:
    from src.database.connection import init_db
    init_db()
except Exception:
    pass

# Inject modern institutional financial styling
inject_custom_theme()


from src.auth.service import UserAccount
from dashboard.components.auth_view import render_auth_page


def _get_shared_service(user: Optional[UserAccount] = None) -> PaperTradingService:
    """Ensure shared per-user instance of PaperTradingService across all pages & modes."""
    user_id = user.id if user else st.session_state.get("user_id", "default_trader")
    starting_cap = user.starting_capital if user else 1_000_000.0

    service_key = f"paper_service_{user_id}"
    if service_key not in st.session_state:
        user_state_dir = f"data/user_state/{user_id}"
        st.session_state[service_key] = PaperTradingService(
            initial_capital=starting_cap,
            state_dir=user_state_dir,
            auto_restore=True,
        )
    return st.session_state[service_key]


def main():
    """Main application orchestrator."""
    # 1. User Authentication Gate
    user = st.session_state.get("authenticated_user")
    if not user:
        from src.auth.service import AuthService
        auth_svc = AuthService()
        success, msg, user = auth_svc.login("demotrader", "Demo1234!")
        if not success:
            success, msg, user = auth_svc.register(
                username="demotrader",
                password="Demo1234!",
                full_name="Executive Trader VIP",
                email="trader@indianmarket.ai",
                starting_capital=1_000_000.0,
            )
        if user:
            st.session_state["authenticated_user"] = user
            st.session_state["user_id"] = user.id
        else:
            render_auth_page()
            return

    service = _get_shared_service(user)
    ui_mode = get_current_ui_mode()

    # ----- Sidebar -----
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <img src="https://img.icons8.com/color/48/analytics.png" width="36" />
                <div>
                    <div style="font-weight: 700; font-size: 17px; color: #f8fafc; line-height: 1.1;">INDIAN MARKET AI</div>
                    <div style="font-size: 11px; color: #94a3b8;">Quantitative Intelligence Terminal</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Mode Switcher (Beginner vs Pro)
        render_mode_switcher_sidebar()

        st.divider()

        # Categorized Navigation based on selected UI Mode
        if ui_mode == "BEGINNER":
            beginner_options = [
                "🎯 Guided Paper Trade & Catalysts",
                "⚡ 60s Option Decision Terminal",
                "🏠 Home & Balance",
                "📋 Option Chain & Buy Strikes",
                "💼 My Portfolio & Live P&L",
                "📰 Live Market News",
                "📈 Market Discovery",
                "🛡️ Safety & Risk Guard",
                "🎓 Trader Academy & Guide",
                "🚀 Unified Master Trading Terminal",
            ]
            # Handle deep-link transitions from buttons
            default_idx = 0
            if "beginner_nav" in st.session_state and st.session_state["beginner_nav"] in beginner_options:
                default_idx = beginner_options.index(st.session_state["beginner_nav"])

            page = st.radio(
                "Beginner Navigation",
                beginner_options,
                index=default_idx,
                label_visibility="collapsed",
                key="radio_beginner_nav",
            )
            # Sync back state
            st.session_state["beginner_nav"] = page

        else:
            # PRO MODE: Dense, Institutional Terminal Desks
            pro_options = [
                "🚀 Unified Master Trading Terminal",
                "⚡ 60s Option Decision Terminal",
                "🏛️ Executive Terminal",
                "⚡ AI Live Market Terminal",
                "📰 Live News Intelligence",
                "📋 Option Chain & Technical Desk",
                "⚡ Volatility & Greeks Surface",
                "📈 Technical Analysis Desk",
                "🌡 Market Regime Classifier",
                "📋 Pro Paper Execution Desk",
                "📊 Portfolio & Mark-to-Market",
                "📜 Execution Journal & Audit",
                "🛡️ Circuit Breakers & Risk Limits",
                "🎯 Strategy Research Lab",
                "⏳ Backtesting & Validation Gate",
                "🤖 ML Predictive Alphas",
                "🔬 Multi-Session Validation",
                "🏥 Provider Data Health",
                "🏠 Market Overview",
            ]
            page = st.radio(
                "Pro Terminal Desks",
                pro_options,
                index=0,
                label_visibility="collapsed",
                key="radio_pro_nav",
            )

        st.divider()

        # Global Underlying selector
        config = get_config()
        symbols = [u["symbol"] for u in config.enabled_underlyings]
        selected_symbol = st.selectbox(
            "Default Underlying",
            symbols,
            index=0 if symbols else None,
            key="global_symbol",
        )
        st.session_state["selected_symbol"] = selected_symbol

        st.divider()

        # Trader Account Profile Badge & Logout
        st.markdown(
            f"""
            <div style="background: rgba(30, 41, 59, 0.8); border: 1px solid #334155; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">ACTIVE TRADER</div>
                <div style="font-size: 14px; font-weight: 700; color: #f8fafc;">{user.full_name}</div>
                <div style="font-size: 11px; color: #38bdf8;">@{user.username} &nbsp;•&nbsp; {user.email}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚪 Sign Out", key="auth_logout_btn", use_container_width=True):
            st.session_state.pop("authenticated_user", None)
            st.session_state.pop("user_id", None)
            st.rerun()

        # Market status indicator
        now = now_ist()
        market_open = is_market_open()
        market_badge = "🟢 OPEN" if market_open else "🔴 CLOSED"
        st.caption(f"**NSE Status:** {market_badge} • `{now.strftime('%H:%M:%S IST')}`")
        st.caption("🛡️ **PAPER TRADING SIMULATION ONLY** • No real money used.")

    # ----- Always-Visible Top Decision Bar & Verdict Banner -----
    from dashboard.components.decision_top_bar import render_decision_top_bar
    verdict_res = render_decision_top_bar(service)

    # ----- Content Routing -----
    if page == "🚀 Unified Master Trading Terminal":
        st.markdown("### 🚀 Unified Master Trading Terminal")
        st.caption("Integrated Derivatives Strike Matrix • Automated Candlestick Pattern AI • Synchronized P&L Ledger")
        st.components.v1.iframe("http://localhost:3000", height=950, scrolling=True)
    elif page in ("🎯 Guided Paper Trade & Catalysts", "🎯 Guided Paper Trade"):
        from dashboard.components.beginner_views import render_beginner_trade
        render_beginner_trade(service)
    elif page == "⚡ 60s Option Decision Terminal":
        from dashboard.pages.option_decision_terminal import render_decision_terminal_page
        render_decision_terminal_page(service)
    elif ui_mode == "BEGINNER":
        from dashboard.components.beginner_views import (
            render_beginner_home,
            render_beginner_trade,
            render_beginner_portfolio,
            render_beginner_risk,
            render_beginner_academy,
        )
        if page == "🏠 Home & Balance":
            render_beginner_home(service)
        elif page in ("📋 Option Chain & Buy Strikes", "📋 Option Chain & Technical Desk"):
            from dashboard.pages.options_chain import render_options_chain_page
            render_options_chain_page()
        elif page == "💼 My Portfolio & Live P&L":
            render_beginner_portfolio(service)
        elif page == "📰 Live Market News":
            from dashboard.pages.live_news import render_live_news_page
            render_live_news_page()
        elif page == "💼 My Holdings & Positions":
            render_beginner_portfolio(service)
        elif page == "📈 Market Discovery":
            from dashboard.components.beginner_views import render_beginner_market_discovery
            render_beginner_market_discovery(selected_symbol or "NIFTY")
        elif page == "🛡️ Safety & Risk Guard":
            render_beginner_risk(service)
        elif page == "🎓 Trader Academy & Guide":
            render_beginner_academy()

    else:
        # Pro Mode Routing
        if page == "🏛️ Executive Terminal":
            from dashboard.pages.investor_overview import render_investor_overview_page
            render_investor_overview_page()
        elif page == "⚡ AI Live Market Terminal":
            from dashboard.pages.live_market import render_live_market_page
            render_live_market_page()
        elif page == "📰 Live News Intelligence":
            from dashboard.pages.live_news import render_live_news_page
            render_live_news_page()
        elif page in ("📋 Option Chain Matrix", "📋 Option Chain & Technical Desk"):
            from dashboard.pages.options_chain import render_options_chain_page
            render_options_chain_page()
        elif page == "⚡ Volatility & Greeks Surface":
            from dashboard.pages.volatility_greeks import render_volatility_greeks_page
            render_volatility_greeks_page()
        elif page == "📈 Technical Analysis Desk":
            from dashboard.pages.technical_analysis import render_technical_analysis_page
            render_technical_analysis_page()
        elif page == "🌡 Market Regime Classifier":
            from dashboard.pages.market_regime import render_market_regime_page
            render_market_regime_page()
        elif page == "📋 Pro Paper Execution Desk":
            from dashboard.pages.paper_trading import render_paper_trading_page
            render_paper_trading_page()
        elif page == "📊 Portfolio & Mark-to-Market":
            from dashboard.pages.paper_positions import render_paper_positions_page
            render_paper_positions_page()
        elif page == "📜 Execution Journal & Audit":
            from dashboard.pages.paper_journal import render_paper_journal_page
            render_paper_journal_page()
        elif page == "🛡️ Circuit Breakers & Risk Limits":
            from dashboard.pages.paper_risk import render_paper_risk_page
            render_paper_risk_page()
        elif page == "🎯 Strategy Research Lab":
            from dashboard.pages.strategy_research import render_strategy_research_page
            render_strategy_research_page()
        elif page == "⏳ Backtesting & Validation Gate":
            from dashboard.pages.backtest_validation import render_backtest_validation_page
            render_backtest_validation_page()
        elif page == "🤖 ML Predictive Alphas":
            from dashboard.pages.ml_research import render as render_ml_page
            render_ml_page()
        elif page == "🔬 Multi-Session Validation":
            from dashboard.pages.paper_validation import render_paper_validation_page
            render_paper_validation_page()
        elif page == "🏥 Provider Data Health":
            from dashboard.pages.data_health import render_data_health_page
            render_data_health_page()
        elif page == "🏠 Market Overview":
            from dashboard.pages.market import render_market_page
            render_market_page()


if __name__ == "__main__":
    main()
