"""
Streamlit Dashboard Page — Phase 8 Paper Risk Management.

Displays real-time paper risk limits, margin utilization, daily loss limits,
and active circuit breakers.
All limits labeled clearly as CONFIGURED PAPER RISK LIMITS.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on Python path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


import streamlit as st
import pandas as pd

from src.paper_trading.service import PaperTradingService


def _get_service() -> PaperTradingService:
    if "paper_service" not in st.session_state:
        st.session_state["paper_service"] = PaperTradingService()
    return st.session_state["paper_service"]


def render_paper_risk_page():
    """Render the paper risk monitoring page."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #cb2d3e, #ef473a); padding: 12px 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0;">🛡️ PAPER RISK MONITORING & CIRCUIT BREAKERS</h2>
            <p style="color: white; margin: 4px 0 0 0; font-size: 14px;">
                CONFIGURED PAPER RISK LIMITS &nbsp;•&nbsp; CIRCUIT BREAKER CONTROLS &nbsp;•&nbsp; NO BYPASS ALLOWED
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    service = _get_service()
    risk_status = service.get_risk_status()

    # Breaker Status
    breaker_active = risk_status.get("is_any_breaker_active", False)
    if breaker_active:
        st.error("🚨 CIRCUIT BREAKER TRIPPED! Paper order placement is currently suspended.")
    else:
        st.success("🟢 ALL SYSTEMS OPERATIONAL: Paper risk limits healthy, no circuit breakers active.")

    st.divider()

    # Risk Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Daily Realized P&L", f"₹{risk_status.get('daily_realized_pnl', 0):,.2f}")
    with col2:
        st.metric("Daily Unrealized P&L", f"₹{risk_status.get('daily_unrealized_pnl', 0):,.2f}")
    with col3:
        st.metric("Consecutive Losses", risk_status.get("consecutive_losses", 0))
    with col4:
        st.metric("Orders Rejected (Session)", risk_status.get("orders_rejected_count", 0))

    st.divider()

    # Configured limits table
    st.markdown("### 📋 Active Risk Constraints")
    st.caption("ℹ️ These are CONFIGURED PAPER RISK LIMITS for research simulation, not universally safe guarantees.")

    limits = risk_status.get("configured_limits", {})
    limits_data = [
        {"Rule": "Max Daily Loss", "Limit": f"₹{limits.get('max_daily_loss', 0):,.2f}"},
        {"Rule": "Max Drawdown %", "Limit": f"{limits.get('max_drawdown_pct', 0) * 100:.1f}%"},
        {"Rule": "Max Position Size (INR)", "Limit": f"₹{limits.get('max_position_size', 0):,.2f}"},
        {"Rule": "Max Open Positions", "Limit": str(limits.get('max_open_positions', 0))},
        {"Rule": "Max Capital Allocation %", "Limit": f"{limits.get('max_capital_allocation_pct', 0) * 100:.1f}%"},
        {"Rule": "Max Consecutive Losses", "Limit": str(limits.get('max_consecutive_losses', 0))},
    ]
    st.table(pd.DataFrame(limits_data))

    st.divider()

    # Breaker controls
    st.markdown("### ⚡ Manual Circuit Breaker Override")
    col_trip, col_reset = st.columns(2)
    with col_trip:
        if st.button("🚨 Trip Emergency Breaker (Halt Trading)"):
            service.trip_breaker(reason="MANUAL_EMERGENCY_HALT")
            st.warning("Emergency circuit breaker triggered manually!")
            st.rerun()
    with col_reset:
        if st.button("🔄 Reset Circuit Breakers"):
            service.reset_breakers()
            st.success("Circuit breakers reset!")
            st.rerun()

if __name__ == "__main__":
    st.set_page_config(page_title="Paper Risk", layout="wide")
    render_paper_risk_page()

