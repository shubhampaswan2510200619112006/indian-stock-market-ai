"""
60-Second Option Decision Terminal Page.

Flagship decision engine designed to let a trader decide in under 60 seconds:
- Top Market Verdict & Regimes (Sticky top bar)
- Curated high-conviction Trade Cards with honest probabilities
- Strict liquidity rejection banners
- Exact Greeks, real NSE transaction costs & itemized statutory taxes
- Mandatory 'Why NOT to take this trade' cautionary boxes
- One-click paper execution
"""

from __future__ import annotations

import streamlit as st
from datetime import date
from src.paper_trading.service import PaperTradingService
from src.features.trade_card import generate_curated_trade_ideas
from dashboard.components.trade_card import render_trade_card
from src.ingestion.provider_factory import get_market_data_provider


def render_decision_terminal_page(service: PaperTradingService):
    """Renders the 60-Second Option Decision Terminal."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #091a28, #102a43, #1e3a5f); padding: 18px 22px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #1e40af;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span style="background: #38bdf8; color: #0b1120; font-weight: 800; font-size: 11px; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.5px;">
                        INSTITUTIONAL SPEED • CAPITAL PRESERVATION FIRST
                    </span>
                    <h2 style="color: white; margin: 8px 0 4px 0; font-size: 24px; font-weight: 800;">
                        ⚡ 60-Second Trade Decision Terminal
                    </h2>
                    <p style="color: #94a3b8; margin: 0; font-size: 14px;">
                        Evaluate actionable index and stock option setups in under 60 seconds with full Greek visibility, 
                        real statutory NSE taxes, and a mandatory <b>bias toward NOT trading</b> unless edge is undeniable.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Terminal Configuration Controls
    col_sym, col_cap, col_risk = st.columns([1.5, 1.5, 1.5])
    with col_sym:
        available_symbols = ["NIFTY", "BANKNIFTY", "RELIANCE", "HDFCBANK", "TCS", "INFY"]
        current_sym = st.session_state.get("selected_symbol", "NIFTY")
        sym_idx = available_symbols.index(current_sym) if current_sym in available_symbols else 0
        selected_symbol = st.selectbox(
            "Selected Underlying",
            available_symbols,
            index=sym_idx,
            key="terminal_symbol_selector",
        )
        st.session_state["selected_symbol"] = selected_symbol

    with col_cap:
        portfolio_summary = service.get_portfolio_summary()
        current_equity = portfolio_summary.get("equity", 500000.0)
        account_capital = st.number_input(
            "Portfolio Account Capital (₹)",
            min_value=10000.0,
            max_value=100000000.0,
            value=float(current_equity),
            step=50000.0,
            key="terminal_account_capital",
        )

    with col_risk:
        trade_risk_pct = st.slider(
            "Risk Budget Per Trade (%)",
            min_value=0.25,
            max_value=3.0,
            value=1.0,
            step=0.25,
            key="terminal_trade_risk_pct",
            help="Strict limit: No single idea may risk more than this % of your total account capital.",
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 2. Fetch Spot Price & Generate Trade Ideas
    with st.spinner(f"Analyzing option chain, Greeks surface & liquidity for {selected_symbol}..."):
        provider = get_market_data_provider()
        try:
            spot_quote = provider.get_latest_price(selected_symbol)
            spot_val = spot_quote.price if (spot_quote and spot_quote.price > 0) else None
        except Exception:
            spot_val = None

        ideas = generate_curated_trade_ideas(
            symbol=selected_symbol,
            spot_price=spot_val,
            capital=account_capital,
            risk_pct=trade_risk_pct,
        )

    # 3. Decision Terminal Summary
    executable_count = sum(1 for i in ideas if i.is_executable)
    rejected_count = sum(1 for i in ideas if not i.is_executable)

    st.markdown(
        f"""
        <div style="display: flex; gap: 16px; margin-bottom: 20px;">
            <div style="background: rgba(30, 41, 59, 0.8); border: 1px solid #334155; border-radius: 8px; padding: 10px 16px; flex: 1;">
                <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">ACTIVE CANDIDATE SETUPS</div>
                <div style="font-size: 20px; font-weight: 800; color: #f8fafc;">{len(ideas)} Ideas Evaluated</div>
            </div>
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 8px; padding: 10px 16px; flex: 1;">
                <div style="font-size: 11px; color: #a7f3d0; font-weight: 600;">EXECUTABLE CANDIDATES</div>
                <div style="font-size: 20px; font-weight: 800; color: #34d399;">{executable_count} Setups</div>
            </div>
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; border-radius: 8px; padding: 10px 16px; flex: 1;">
                <div style="font-size: 11px; color: #fca5a5; font-weight: 600;">REJECTED BY SAFETY GATES</div>
                <div style="font-size: 20px; font-weight: 800; color: #f87171;">{rejected_count} Illiquid / High-Risk</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. Render Trade Cards
    for idx, idea in enumerate(ideas):
        render_trade_card(
            idea=idea,
            service=service,
            default_capital=account_capital,
            default_risk_pct=trade_risk_pct,
            card_index=idx,
        )
