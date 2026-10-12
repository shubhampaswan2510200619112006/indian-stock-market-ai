"""
60-Second Option Decision Terminal Page.

Flagship decision engine designed to let a trader decide in under 60 seconds:
- Top Market Verdict & Regimes (Sticky top bar)
- Curated high-conviction Trade Cards with honest probabilities
- Strict liquidity rejection banners
- Exact Greeks, real NSE transaction costs & itemized statutory taxes
- Mandatory 'Why NOT to take this trade' cautionary boxes
- One-click paper execution
Rendered using 100% native Streamlit components to prevent any code-block formatting issues.
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
    st.markdown("## ⚡ 60-Second Trade Decision Terminal")
    st.caption("Institutional speed • Capital preservation first • Strict liquidity rejection • Exact NSE statutory taxes")

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

    st.divider()

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

    sum_col1, sum_col2, sum_col3 = st.columns(3)
    with sum_col1:
        st.metric("Total Setups Evaluated", f"{len(ideas)} Ideas")
    with sum_col2:
        st.metric("Executable Setups", f"{executable_count} Liquid")
    with sum_col3:
        st.metric("Rejected by Safety Gates", f"{rejected_count} Illiquid / High-Risk", delta_color="inverse")

    st.divider()

    # 4. Render Trade Cards
    for idx, idea in enumerate(ideas):
        render_trade_card(
            idea=idea,
            service=service,
            default_capital=account_capital,
            default_risk_pct=trade_risk_pct,
            card_index=idx,
        )


if __name__ == "__main__":
    st.set_page_config(page_title="60-Second Option Decision Terminal", layout="wide")
    from src.paper_trading.service import PaperTradingService
    render_decision_terminal_page(PaperTradingService())
