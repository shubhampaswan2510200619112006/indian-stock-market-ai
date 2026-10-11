"""
Top Decision Bar Component — Always Visible Terminal Header.

Displays:
- Real-time ticker cards: Nifty, Bank Nifty, India VIX, GIFT Nifty, FII/DII Net, Market Regime.
- Prominent Verdict Card: GOOD TO TRADE / CAUTION / NO TRADE with Top 3 Deterministic Reasons.
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

    # Styling helpers
    def _chg_color(val: float) -> str:
        return "#10b981" if val >= 0 else "#ef4444"

    def _chg_sign(val: float) -> str:
        return f"+{val:.2f}%" if val >= 0 else f"{val:.2f}%"

    # 1. TOP TICKER ROW
    st.markdown(
        f"""
        <div style="background-color: #0b0f19; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px;">
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px;">
                <!-- NIFTY 50 -->
                <div style="min-width: 130px;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">🏛️ NIFTY 50</div>
                    <div style="font-size: 15px; font-weight: 700; color: #f8fafc;" class="metric-mono">
                        ₹{snapshot.nifty_price:,.0f} 
                        <span style="font-size: 11px; color: {_chg_color(snapshot.nifty_change_pct)}; font-weight: 600;">{_chg_sign(snapshot.nifty_change_pct)}</span>
                    </div>
                </div>

                <!-- BANK NIFTY -->
                <div style="min-width: 140px;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">🏦 BANK NIFTY</div>
                    <div style="font-size: 15px; font-weight: 700; color: #f8fafc;" class="metric-mono">
                        ₹{snapshot.banknifty_price:,.0f} 
                        <span style="font-size: 11px; color: {_chg_color(snapshot.banknifty_change_pct)}; font-weight: 600;">{_chg_sign(snapshot.banknifty_change_pct)}</span>
                    </div>
                </div>

                <!-- INDIA VIX -->
                <div style="min-width: 120px;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">⚡ INDIA VIX</div>
                    <div style="font-size: 15px; font-weight: 700; color: #f8fafc;" class="metric-mono">
                        {snapshot.vix_value:.2f} 
                        <span style="font-size: 11px; color: {'#ef4444' if snapshot.vix_change_pct > 0 else '#10b981'}; font-weight: 600;">{_chg_sign(snapshot.vix_change_pct)}</span>
                    </div>
                </div>

                <!-- GIFT NIFTY -->
                <div style="min-width: 120px;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">🌐 GIFT NIFTY</div>
                    <div style="font-size: 15px; font-weight: 700; color: #f8fafc;" class="metric-mono">
                        ₹{snapshot.gift_nifty_price:,.0f}
                        <span style="font-size: 11px; color: {_chg_color(snapshot.gift_nifty_change_pct)}; font-weight: 600;">{_chg_sign(snapshot.gift_nifty_change_pct)}</span>
                    </div>
                </div>

                <!-- FII / DII NET -->
                <div style="min-width: 150px;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">💼 FII / DII NET (Cr)</div>
                    <div style="font-size: 13px; font-weight: 600;" class="metric-mono">
                        <span style="color: {_chg_color(snapshot.fii_net_cr)};">FII: {snapshot.fii_net_cr:+,.0f}</span> &nbsp;|&nbsp; 
                        <span style="color: {_chg_color(snapshot.dii_net_cr)};">DII: {snapshot.dii_net_cr:+,.0f}</span>
                    </div>
                </div>

                <!-- REGIME TAG -->
                <div style="min-width: 140px; text-align: right;">
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">🏷️ MARKET REGIME</div>
                    <div style="font-size: 13px; font-weight: 700; color: #38bdf8; background: #0f172a; padding: 2px 8px; border-radius: 4px; display: inline-block; border: 1px solid #1e293b;">
                        {snapshot.regime_tag}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. PROMINENT VERDICT BANNER
    verdict_txt = verdict_res.verdict
    color = verdict_res.badge_color

    # Pre-render top 3 reasons HTML
    reasons_html = "".join([f"<li style='margin-bottom: 3px;'>{r}</li>" for r in verdict_res.top_reasons])

    st.markdown(
        f"""
        <div style="background-color: #0e1526; border-left: 5px solid {color}; border-top: 1px solid #1e293b; border-right: 1px solid #1e293b; border-bottom: 1px solid #1e293b; border-radius: 8px; padding: 12px 18px; margin-bottom: 18px;">
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px;">
                <!-- Big Verdict Badge -->
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="background-color: {color}22; border: 2px solid {color}; color: {color}; font-size: 18px; font-weight: 800; padding: 6px 14px; border-radius: 6px; letter-spacing: 0.5px;">
                        {verdict_txt}
                    </div>
                    <div>
                        <div style="font-size: 13px; font-weight: 700; color: #f8fafc;">60-Second Trade Decision Verdict</div>
                        <div style="font-size: 11px; color: #94a3b8;">Deterministic rule-based gating • Strong bias toward capital preservation</div>
                    </div>
                </div>

                <!-- Top 3 Reasons -->
                <div style="flex: 1; min-width: 280px; max-width: 650px;">
                    <ul style="margin: 0; padding-left: 18px; font-size: 12px; color: #cbd5e1; line-height: 1.4;">
                        {reasons_html}
                    </ul>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return verdict_res
