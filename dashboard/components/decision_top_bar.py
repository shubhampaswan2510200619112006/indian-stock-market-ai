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

    # Real-Time Gateway Status Strip
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 5px 14px; margin-bottom: 10px; font-size: 11px;">
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <span style="display: inline-block; width: 8px; height: 8px; background: #10b981; border-radius: 50%; box-shadow: 0 0 10px #10b981;"></span>
                <span style="color: #f8fafc; font-weight: 700; letter-spacing: 0.5px;">LIVE EXCHANGE FEED</span>
                <span style="color: #475569;">•</span>
                <span style="color: #38bdf8; font-weight: 600;">{snapshot.feed_provider}</span>
                <span style="color: #475569;">•</span>
                <span style="color: #cbd5e1;">Tick: <b>{snapshot.feed_time}</b></span>
            </div>
            <div style="color: #94a3b8; font-family: monospace;">
                ⚡ Feed Latency: <b style="color: {'#10b981' if snapshot.feed_latency_ms < 600 else '#f59e0b'};">{snapshot.feed_latency_ms:.0f}ms</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. TOP TICKER ROW (Rendered via native responsive columns)
    with st.container():
        col_nifty, col_bn, col_vix, col_gift, col_fii, col_regime = st.columns(6)

        with col_nifty:
            st.metric(
                "🏛️ NIFTY 50",
                f"₹{snapshot.nifty_price:,.0f}",
                f"{snapshot.nifty_change_pct:+.2f}%",
            )

        with col_bn:
            st.metric(
                "🏦 BANK NIFTY",
                f"₹{snapshot.banknifty_price:,.0f}",
                f"{snapshot.banknifty_change_pct:+.2f}%",
            )

        with col_vix:
            st.metric(
                "⚡ INDIA VIX",
                f"{snapshot.vix_value:.2f}",
                f"{snapshot.vix_change_pct:+.2f}%",
                delta_color="inverse",
            )

        with col_gift:
            st.metric(
                "🌐 GIFT NIFTY",
                f"₹{snapshot.gift_nifty_price:,.0f}",
                f"{snapshot.gift_nifty_change_pct:+.2f}%",
            )

        with col_fii:
            st.metric(
                "💼 FII / DII (Cr)",
                f"FII: {snapshot.fii_net_cr:+,.0f}",
                f"DII: {snapshot.dii_net_cr:+,.0f}",
            )

        with col_regime:
            st.metric(
                "🏷️ MARKET REGIME",
                snapshot.regime_tag,
                "Macro Context",
                delta_color="off",
            )

    # 2. PROMINENT VERDICT BANNER
    reasons_text = "\n".join([f"- **{r}**" for r in verdict_res.top_reasons])
    header_subtitle = "Deterministic rule-based gating • Strong bias toward capital preservation"

    if verdict_res.verdict == "GOOD TO TRADE":
        st.success(
            f"### 🟢 GOOD TO TRADE — 60-Second Verdict\n"
            f"*{header_subtitle}*\n\n"
            f"**Key Catalysts:**\n"
            f"{reasons_text}"
        )
    elif verdict_res.verdict == "CAUTION":
        st.warning(
            f"### 🟡 CAUTION — 60-Second Verdict\n"
            f"*{header_subtitle}*\n\n"
            f"**Key Cautionary Factors:**\n"
            f"{reasons_text}"
        )
    else:  # NO TRADE
        st.error(
            f"### 🔴 NO TRADE — 60-Second Verdict (Risk Protection Active)\n"
            f"*{header_subtitle}*\n\n"
            f"**Mandatory Lockout Reasons:**\n"
            f"{reasons_text}"
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    return verdict_res
