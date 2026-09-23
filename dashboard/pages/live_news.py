"""
Streamlit Dashboard Page — Phase 7 Live News Intelligence Terminal.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ingestion.providers.news_provider import VerifiedRSSNewsProvider
from src.news.impact import NewsImpactAnalyzer
from src.news.models import NewsEventType, NewsMaterialityType, SourceAuthority
from src.news.storage import NewsStorageManager
from src.utils.config import get_config


def render_live_news_page():
    """Render Phase 7 Live News Intelligence Terminal."""
    st.title("📰 Live News Intelligence Terminal")
    st.caption("Verified RSS Feeds, MD5 Deduplication, Entity Mapping, Materiality & Non-Causal Market Impact")

    # Safety disclaimer
    st.info(
        "ℹ️ **NEWS INTELLIGENCE DISCLAIMER**: Market impact correlations are purely observational and non-causal. "
        "Post-event price changes do not imply direct causation."
    )

    storage = NewsStorageManager()
    impact_analyzer = NewsImpactAnalyzer()
    config = get_config()

    # Toolbar controls
    col_fetch, col_search, col_cat, col_mat = st.columns([1.5, 2, 2, 2])

    with col_fetch:
        st.write("")
        if st.button("🔄 Fetch Latest Feeds"):
            with st.spinner("Ingesting verified RSS feeds..."):
                provider = VerifiedRSSNewsProvider()
                articles = provider.fetch_latest_news()
                inserted_count = 0
                for a in articles:
                    if storage.save_article(a):
                        inserted_count += 1
                st.success(f"Fetched {len(articles)} articles ({inserted_count} new).")
            st.rerun()

    with col_search:
        search_ticker = st.text_input("Filter by Ticker / Symbol", placeholder="e.g. NIFTY, RELIANCE").strip().upper()

    with col_cat:
        selected_cat = st.selectbox(
            "Event Category",
            ["ALL"] + [c.value for c in NewsEventType],
            index=0,
        )

    with col_mat:
        selected_mat = st.selectbox(
            "Materiality Grade",
            ["ALL"] + [m.value for m in NewsMaterialityType],
            index=0,
        )

    # Fetch articles from database with filters
    category_filter = NewsEventType(selected_cat) if selected_cat != "ALL" else None
    materiality_filter = NewsMaterialityType(selected_mat) if selected_mat != "ALL" else None
    ticker_filter = search_ticker if search_ticker else None

    articles = storage.get_recent_articles(
        ticker=ticker_filter,
        category=category_filter,
        materiality=materiality_filter,
        limit=50,
    )

    st.subheader(f"Latest News Articles ({len(articles)} items)")

    if not articles:
        st.warning("No news articles found matching the selected criteria. Click 'Fetch Latest Feeds' above to ingest RSS news.")

    authority_colors = {
        SourceAuthority.OFFICIAL_EXCHANGE.value: "#00c853",
        SourceAuthority.PUBLIC_NEWS_FEED.value: "#29b6f6",
        SourceAuthority.AGGREGATOR.value: "#ab47bc",
    }

    materiality_colors = {
        NewsMaterialityType.CRITICAL.value: "#d50000",
        NewsMaterialityType.HIGH.value: "#ff6d00",
        NewsMaterialityType.MEDIUM.value: "#ffd600",
        NewsMaterialityType.LOW.value: "#64dd17",
    }

    for art in articles:
        auth_color = authority_colors.get(art.authority.value, "#757575")
        mat_color = materiality_colors.get(art.materiality.value, "#757575")

        entities_str = ", ".join([f"**{e.name}** ({e.ticker or 'N/A'})" for e in art.entities]) if art.entities else "None"
        pub_str = art.published_at.strftime("%Y-%m-%d %H:%M:%S")
        rec_str = art.received_at.strftime("%Y-%m-%d %H:%M:%S")
        proc_str = art.processed_at.strftime("%Y-%m-%d %H:%M:%S")

        with st.expander(f"[{art.materiality.value}] {art.title} — {art.source_name} ({pub_str} IST)"):
            st.markdown(
                f"""
                <div style="margin-bottom: 10px;">
                    <span style="background-color: {auth_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;">
                        {art.authority.value}
                    </span>
                    <span style="background-color: {mat_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-left: 8px;">
                        Materiality: {art.materiality.value}
                    </span>
                    <span style="background-color: #212121; color: #e0e0e0; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 8px;">
                        Category: {art.category.value}
                    </span>
                    <span style="background-color: #1a237e; color: #e0e0e0; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 8px;">
                        Sentiment: {art.sentiment.label.value} ({art.sentiment.score:+.2f})
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(f"**Summary:** {art.summary}")
            st.write(f"**Identified Entities:** {entities_str}")
            st.markdown(f"**Source URL:** [{art.url}]({art.url})")

            # 3 Latency Timestamps
            st.markdown(
                f"""
                <div style="background-color: #121824; padding: 8px; border-radius: 4px; font-size: 0.82em; color: #b0bec5; margin-top: 8px;">
                    ⏱️ <strong>Latency Timestamps:</strong> 
                    Published: <code>{pub_str}</code> | 
                    Received: <code>{rec_str}</code> | 
                    Processed: <code>{proc_str}</code> | 
                    MD5 Fingerprint: <code>{art.fingerprint[:12]}...</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Non-causal Impact Observation Card
            st.markdown("##### 📊 Observational Market Impact (Non-Causal)")
            # Sample observation card
            primary_ticker = art.entities[0].ticker if art.entities and art.entities[0].ticker else "NIFTY"
            obs = impact_analyzer.analyze_impact(article=art, ticker=primary_ticker, window_minutes=30)
            
            st.markdown(
                f"""
                <div style="background-color: #1a202c; padding: 10px; border-radius: 6px; border-left: 4px solid #64b5f6;">
                    <strong>Observed Price Delta (T+30m):</strong> {obs.price_change_pct:+.2f}%<br/>
                    <strong>Observed Volatility Delta:</strong> {obs.volatility_change:+.2f}%<br/>
                    <strong>Confidence / Attribution:</strong> <em style="color: #ffd600;">{obs.attribution_caveat}</em>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    st.set_page_config(page_title="Live News Intelligence Terminal", layout="wide")
    render_live_news_page()
