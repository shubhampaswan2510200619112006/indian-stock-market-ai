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
            user_id=user_id,
        )
    st.session_state["paper_service"] = st.session_state[service_key]
    return st.session_state[service_key]


def main():
    """Main application orchestrator."""
    # 1. User Authentication Gate
    user = st.session_state.get("authenticated_user")
    if not user:
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

        # Sweet, Simple & User-Friendly Navigation (Zero Clutter)
        main_nav_options = [
            "🚀 Trading Desk",
            "💼 Positions & P&L",
            "📰 Market News & AI",
            "⚙️ Advanced Tools",
        ]

        # Check if deep-link requested
        default_idx = 0
        if "main_nav" in st.session_state and st.session_state["main_nav"] in main_nav_options:
            default_idx = main_nav_options.index(st.session_state["main_nav"])

        page = st.radio(
            "Navigation",
            main_nav_options,
            index=default_idx,
            label_visibility="collapsed",
            key="radio_main_nav",
        )
        st.session_state["main_nav"] = page

        adv_tool = None
        if page == "⚙️ Advanced Tools":
            adv_tool = st.selectbox(
                "Select Advanced Tool",
                [
                    "⚡ Volatility & Greeks Surface",
                    "📈 Technical Analysis Desk",
                    "🌡 Market Regime Classifier",
                    "⏳ Backtesting & Validation Gate",
                    "🎯 Strategy Research Lab",
                    "🛡️ Circuit Breakers & Risk Limits",
                    "🏥 Provider Data Health",
                ],
                key="adv_tool_select",
            )

        st.divider()

        # Global Underlying selector
        config = get_config()
        symbols = [u["symbol"] for u in config.enabled_underlyings]
        selected_symbol = st.selectbox(
            "Underlying Index",
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
                <div style="font-size: 11px; color: #38bdf8;">@{user.username}</div>
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

    # ----- Always-Visible Top Decision Bar (Clean & Compact) -----
    from dashboard.components.decision_top_bar import render_decision_top_bar
    verdict_res = render_decision_top_bar(service)

    # ----- Clean, Sweet Content Routing -----
    if page == "🚀 Trading Desk":
        st.components.v1.iframe("http://localhost:3000", height=980, scrolling=True)
    elif page == "💼 Positions & P&L":
        from dashboard.pages.paper_positions import render_paper_positions_page
        render_paper_positions_page()
    elif page == "📰 Market News & AI":
        from dashboard.pages.live_news import render_live_news_page
        render_live_news_page()
    elif page == "⚙️ Advanced Tools":
        if adv_tool == "⚡ Volatility & Greeks Surface":
            from dashboard.pages.volatility_greeks import render_volatility_greeks_page
            render_volatility_greeks_page()
        elif adv_tool == "📈 Technical Analysis Desk":
            from dashboard.pages.technical_analysis import render_technical_analysis_page
            render_technical_analysis_page()
        elif adv_tool == "🌡 Market Regime Classifier":
            from dashboard.pages.market_regime import render_market_regime_page
            render_market_regime_page()
        elif adv_tool == "⏳ Backtesting & Validation Gate":
            from dashboard.pages.backtest_validation import render_backtest_validation_page
            render_backtest_validation_page()
        elif adv_tool == "🎯 Strategy Research Lab":
            from dashboard.pages.strategy_research import render_strategy_research_page
            render_strategy_research_page()
        elif adv_tool == "🛡️ Circuit Breakers & Risk Limits":
            from dashboard.pages.paper_risk import render_paper_risk_page
            render_paper_risk_page()
        elif adv_tool == "🏥 Provider Data Health":
            from dashboard.pages.data_health import render_data_health_page
            render_data_health_page()


if __name__ == "__main__":
    main()
