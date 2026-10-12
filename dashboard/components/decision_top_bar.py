"""
Top Decision Bar Component — Always Visible Terminal Header.

Displays:
- Real-time ticker cards: Nifty, Bank Nifty, India VIX, GIFT Nifty, FII/DII Net, Market Regime.
- Prominent Verdict Banner: GOOD TO TRADE / CAUTION / NO TRADE with Top 3 Deterministic Reasons.
Rendered cleanly using native Streamlit layout to guarantee zero raw code block escaping.
"""

from __future__ import annotations

import streamlit as st
from src.features.trade_verdict import TradeVerdictEngine, MarketSnapshot, VerdictResult
from src.paper_trading.service import PaperTradingService


def render_decision_top_bar(service: PaperTradingService) -> VerdictResult:
    """
    Renders the sticky, always-visible Top Bar and Verdict Banner.
    Returns VerdictResult for downstream trade card gating.
    """
    if "verdict_engine" not in st.session_state:
        st.session_state["verdict_engine"] = TradeVerdictEngine()

    engine: TradeVerdictEngine = st.session_state["verdict_engine"]

    # Retrieve account risk indicators
    risk_status = service.get_risk_status()
    breaker_active = risk_status.get("is_any_breaker_active", False)
    summary = service.get_portfolio_summary()
    daily_pnl = summary.get("daily_pnl", 0.0)
    starting_cap = summary.get("starting_capital", 1000000.0)
    daily_loss_pct = abs(min(0.0, daily_pnl)) / starting_cap * 100.0 if starting_cap > 0 else 0.0

    # Evaluate snapshot & verdict
    snapshot = engine.get_market_snapshot()
    verdict_res = engine.evaluate_verdict(
        snapshot=snapshot,
        breaker_active=breaker_active,
        daily_loss_pct=daily_loss_pct,
    )

    # 1. SLEEK, SWEET TICKER ROW & VERDICT
    with st.container():
        col_nifty, col_bn, col_vix, col_verdict = st.columns([1.2, 1.2, 1, 1.6])

        with col_nifty:
            st.metric(
                "NIFTY 50",
                f"₹{snapshot.nifty_price:,.0f}",
                f"{snapshot.nifty_change_pct:+.2f}%",
            )

        with col_bn:
            st.metric(
                "BANK NIFTY",
                f"₹{snapshot.banknifty_price:,.0f}",
                f"{snapshot.banknifty_change_pct:+.2f}%",
            )

        with col_vix:
            st.metric(
                "INDIA VIX",
                f"{snapshot.vix_value:.2f}",
                f"{snapshot.vix_change_pct:+.2f}%",
                delta_color="inverse",
            )

        with col_verdict:
            badge_color = "#10b981" if verdict_res.verdict == "GOOD TO TRADE" else ("#f59e0b" if verdict_res.verdict == "CAUTION" else "#ef4444")
            badge_icon = "🟢" if verdict_res.verdict == "GOOD TO TRADE" else ("🟡" if verdict_res.verdict == "CAUTION" else "🔴")
            st.markdown(
                f"""
                <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid {badge_color}40; border-radius: 8px; padding: 10px 14px; margin-top: 2px;">
                    <div style="font-size: 10px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">AI Market Verdict</div>
                    <div style="font-size: 15px; font-weight: 700; color: {badge_color};">{badge_icon} {verdict_res.verdict}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Optional Collapsed Details for AI Market Analysis
    if verdict_res.top_reasons:
        with st.expander("💡 View Market Analysis & Key Reasons", expanded=False):
            for r in verdict_res.top_reasons:
                st.markdown(f"- {r}")

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    return verdict_res
