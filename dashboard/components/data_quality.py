"""
Data freshness and quality display components.

Clearly distinguishes:
- LIVE/RECENT DATA (< threshold)
- DELAYED DATA
- STALE DATA
- END-OF-DAY DATA
- UNAVAILABLE

Never labels cached/stale data as real-time.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import streamlit as st

from src.ingestion.schemas import DataFreshnessLevel, DataQualityStatus
from src.utils.config import get_config
from src.utils.time_utils import data_age_seconds, is_market_open, now_ist


def classify_freshness(timestamp: datetime) -> DataFreshnessLevel:
    """
    Classify data freshness based on age and market state.
    """
    config = get_config()
    freshness = config.data_freshness_config

    age = data_age_seconds(timestamp)

    live_threshold = freshness.get("live_threshold", 60)
    delayed_threshold = freshness.get("delayed_threshold", 300)
    stale_threshold = freshness.get("stale_threshold", 3600)

    market_is_open = is_market_open()

    if age < live_threshold:
        return DataFreshnessLevel.LIVE
    elif age < delayed_threshold:
        return DataFreshnessLevel.DELAYED
    elif age < stale_threshold:
        return DataFreshnessLevel.STALE
    elif not market_is_open:
        return DataFreshnessLevel.END_OF_DAY
    else:
        return DataFreshnessLevel.STALE


def render_freshness_badge(timestamp: Optional[datetime], label: str = "Data"):
    """
    Render a colored badge showing data freshness level.

    Green = LIVE
    Yellow = DELAYED
    Orange = STALE / END_OF_DAY
    Red = UNAVAILABLE
    """
    if timestamp is None:
        st.markdown(
            f"<span style='background-color:#dc3545;color:white;padding:2px 10px;"
            f"border-radius:4px;font-size:0.85em;'>⚠ {label}: UNAVAILABLE</span>",
            unsafe_allow_html=True,
        )
        return

    freshness = classify_freshness(timestamp)
    age = data_age_seconds(timestamp)

    # Format age
    if age < 60:
        age_str = f"{age:.0f}s ago"
    elif age < 3600:
        age_str = f"{age / 60:.0f}m ago"
    else:
        age_str = f"{age / 3600:.1f}h ago"

    colors = {
        DataFreshnessLevel.LIVE: ("#28a745", "🟢"),
        DataFreshnessLevel.DELAYED: ("#ffc107", "🟡"),
        DataFreshnessLevel.STALE: ("#fd7e14", "🟠"),
        DataFreshnessLevel.END_OF_DAY: ("#6c757d", "📊"),
        DataFreshnessLevel.UNAVAILABLE: ("#dc3545", "⚠"),
    }
    bg_color, icon = colors.get(freshness, ("#6c757d", "❓"))

    st.markdown(
        f"<span style='background-color:{bg_color};color:white;padding:2px 10px;"
        f"border-radius:4px;font-size:0.85em;'>"
        f"{icon} {label}: {freshness.value} ({age_str})</span>",
        unsafe_allow_html=True,
    )


def render_data_quality_summary(quality_report: dict):
    """Render a data quality summary from a validation report."""
    overall = quality_report.get("overall_quality", "UNKNOWN")
    total = quality_report.get("total_records", 0)
    valid = quality_report.get("valid_records", 0)
    partial = quality_report.get("partial_records", 0)
    suspect = quality_report.get("suspect_records", 0)
    errors = quality_report.get("validation_errors", [])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", total)
    col2.metric("Valid", valid)
    col3.metric("Partial", partial)
    col4.metric("Suspect", suspect)

    if errors:
        with st.expander(f"⚠ {len(errors)} Validation Issue(s)", expanded=False):
            for err in errors[:10]:
                st.text(f"• {err}")
            if len(errors) > 10:
                st.text(f"... and {len(errors) - 10} more")


def render_provider_info(provider_name: str):
    """Show which data provider is being used with appropriate caveats."""
    if provider_name == "nse_direct":
        st.caption(
            "📡 Data source: NSE direct access (experimental, not production-grade). "
            "Data may be delayed or unavailable."
        )
    elif provider_name == "yfinance":
        st.caption(
            "📡 Data source: Yahoo Finance (typically 15-minute delay). "
            "Not suitable for live trading decisions."
        )
    else:
        st.caption(f"📡 Data source: {provider_name}")
