"""
Streamlit Dashboard Page — Phase 8 Paper Trade Journal & Audit.

Shows complete, immutable paper execution audit trail: orders, fills, rejections,
risk check events, cancellations, and session snapshots.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from src.paper_trading.service import PaperTradingService


def _get_service() -> PaperTradingService:
    if "paper_service" not in st.session_state:
        st.session_state["paper_service"] = PaperTradingService()
    return st.session_state["paper_service"]


def render_paper_journal_page():
    """Render the paper trade journal & audit page."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #11998e, #38ef7d); padding: 12px 20px; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0;">📜 PAPER TRADE JOURNAL & AUDIT</h2>
            <p style="color: white; margin: 4px 0 0 0; font-size: 14px;">
                FULL AUDIT TRAIL &nbsp;•&nbsp; REJECTIONS &amp; FILLS &nbsp;•&nbsp; ZERO SYNTHETIC OMISSIONS
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    service = _get_service()

    # Filter controls
    col1, col2 = st.columns([1, 2])
    with col1:
        event_filter = st.selectbox(
            "Filter by Event Type",
            ["ALL", "ORDER_PLACED", "FILL", "ORDER_REJECTED", "ORDER_CANCELLED", "RISK_BREACH", "SNAPSHOT"]
        )
    with col2:
        limit = st.slider("Max Events to Display", min_value=10, max_value=200, value=50)

    # Fetch audit events
    filter_arg = None if event_filter == "ALL" else event_filter
    events = service.get_journal_entries(event_type=filter_arg, limit=limit)

    st.markdown(f"### Journal Records ({len(events)})")
    if events:
        df_events = pd.DataFrame(events)
        st.dataframe(df_events, use_container_width=True)
    else:
        st.info("No audit journal events matching the filter.")

    st.divider()

    # Reconcile button & status
    st.markdown("### 🔍 On-Demand Reconciliation Check")
    st.caption("Verifies cash balance + positions = total equity, and fills match order records.")
    if st.button("Run Portfolio Reconciliation"):
        rec_res = service.reconcile()
        if rec_res.get("status") == "RECONCILED":
            st.success(f"✅ Portfolio Reconciled: Cash ₹{rec_res.get('cash', 0):,.2f}, Positions {rec_res.get('positions_count', 0)}")
        else:
            st.error(f"❌ RECONCILIATION FAILURE: {rec_res.get('discrepancies')}")
