"""
Indian Options AI — Streamlit Dashboard

Main entry point for the multi-page Streamlit application.
"""

import sys
from pathlib import Path

# Ensure project root is on the Python path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st

from src.utils.config import get_config
from src.utils.time_utils import is_market_open, now_ist

# Page configuration — must be first Streamlit command
st.set_page_config(
    page_title="Indian Options AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database schema if not present
try:
    from src.database.connection import init_db
    init_db()
except Exception:
    pass


# Custom CSS for dark professional theme
st.markdown("""
<style>
    /* Dark theme refinements */
    .stApp { background-color: #0e1117; }

    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.4rem;
        font-weight: 600;
    }

    /* Header styling */
    h1 { color: #42a5f5 !important; }
    h2 { color: #90caf9 !important; }
    h3 { color: #e0e0e0 !important; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0a0f18;
        border-right: 1px solid #1e2530;
    }

    /* Hide redundant default Streamlit multipage navigation to eliminate duplicate sidebar */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* Table improvements */
    .stDataFrame { font-size: 0.85rem; }

    /* Badge styles */
    .freshness-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.85em;
        font-weight: 600;
    }

    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def main():
    """Main Streamlit application."""

    # ----- Sidebar -----
    with st.sidebar:
        st.image("https://img.icons8.com/color/48/analytics.png", width=40)
        st.title("Indian Options AI")
        st.caption("Phase 1 — Options Research")

        st.divider()

        # Market status
        now = now_ist()
        market_status = "🟢 OPEN" if is_market_open() else "🔴 CLOSED"
        st.markdown(f"**Market:** {market_status}")
        st.markdown(f"**Time (IST):** {now.strftime('%H:%M:%S')}")

        st.divider()

        # Navigation
        page = st.radio(
            "Navigate",
            [
                "🏛️ Investor Executive Overview",
                "⚡ AI Live Market Terminal",
                "📰 Live News Intelligence",
                "🏥 Provider Data Health",
                "🔬 Multi-Session Validation",
                "📋 Paper Trading Terminal",
                "📊 Paper Positions & Portfolio",
                "📜 Paper Trade Journal & Audit",
                "🛡️ Paper Risk & Limits",
                "🏠 Market Overview",
                "📋 Option Chain",
                "⚡ Options Volatility & Greeks",
                "🎯 Options Strategy Research",
                "⏳ Backtesting & Validation",
                "🤖 ML Research Framework",
                "📈 Technical Analysis",
                "🌡 Market Regime",
            ],
            label_visibility="collapsed",
        )

        st.divider()

        # Underlying selector (global)
        config = get_config()
        symbols = [u["symbol"] for u in config.enabled_underlyings]
        selected_symbol = st.selectbox(
            "Underlying",
            symbols,
            index=0 if symbols else None,
            key="global_symbol",
        )

        st.divider()
        st.caption("⚠ Research & Paper-Trading Preparation Only.")
        st.caption(f"v{config.yaml.get('app', {}).get('version', '0.8.5')}")

    # Store in session state for pages
    st.session_state["selected_symbol"] = selected_symbol

    # ----- Page routing -----
    if page == "🏛️ Investor Executive Overview":
        from dashboard.pages.investor_overview import render_investor_overview_page
        render_investor_overview_page()
    elif page == "⚡ AI Live Market Terminal":
        from dashboard.pages.live_market import render_live_market_page
        render_live_market_page()
    elif page == "📰 Live News Intelligence":
        from dashboard.pages.live_news import render_live_news_page
        render_live_news_page()
    elif page == "🏥 Provider Data Health":
        from dashboard.pages.data_health import render_data_health_page
        render_data_health_page()
    elif page == "🔬 Multi-Session Validation":
        from dashboard.pages.paper_validation import render_paper_validation_page
        render_paper_validation_page()
    elif page == "📋 Paper Trading Terminal":
        from dashboard.pages.paper_trading import render_paper_trading_page
        render_paper_trading_page()
    elif page == "📊 Paper Positions & Portfolio":
        from dashboard.pages.paper_positions import render_paper_positions_page
        render_paper_positions_page()
    elif page == "📜 Paper Trade Journal & Audit":
        from dashboard.pages.paper_journal import render_paper_journal_page
        render_paper_journal_page()
    elif page == "🛡️ Paper Risk & Limits":
        from dashboard.pages.paper_risk import render_paper_risk_page
        render_paper_risk_page()
    elif page == "🏠 Market Overview":
        from dashboard.pages.market import render_market_page
        render_market_page()
    elif page == "📋 Option Chain":
        from dashboard.pages.options_chain import render_options_chain_page
        render_options_chain_page()
    elif page == "⚡ Options Volatility & Greeks":
        from dashboard.pages.volatility_greeks import render_volatility_greeks_page
        render_volatility_greeks_page()
    elif page == "🎯 Options Strategy Research":
        from dashboard.pages.strategy_research import render_strategy_research_page
        render_strategy_research_page()
    elif page == "⏳ Backtesting & Validation":
        from dashboard.pages.backtest_validation import render_backtest_validation_page
        render_backtest_validation_page()
    elif page == "🤖 ML Research Framework":
        from dashboard.pages.ml_research import render as render_ml_page
        render_ml_page()
    elif page == "📈 Technical Analysis":
        from dashboard.pages.technical_analysis import render_technical_analysis_page
        render_technical_analysis_page()
    elif page == "🌡 Market Regime":
        from dashboard.pages.market_regime import render_market_regime_page
        render_market_regime_page()


if __name__ == "__main__":
    main()



