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

    try:
        articles = storage.get_recent_articles(
            ticker=ticker_filter,
            category=category_filter,
            materiality=materiality_filter,
            limit=50,
        )
    except Exception:
        articles = []

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
        if isinstance(art, dict):
            auth_val = art.get("source_authority", "AGGREGATOR")
            mat_val = art.get("materiality", "MEDIUM")
            cat_val = art.get("event_type", "GENERAL")
            sent_val = art.get("sentiment", "NEUTRAL")
            title = art.get("title", "")
            source_name = art.get("source_name", "RSS")
            summary = art.get("summary", title)
            url = art.get("url", "#")
            fingerprint = art.get("article_id", "news-hash")
            entity = art.get("entity", "NIFTY")
            pub = art.get("published_at")
            rec = art.get("received_at")
            proc = art.get("processed_at")
            pub_str = pub.strftime("%Y-%m-%d %H:%M:%S") if hasattr(pub, "strftime") else str(pub or "N/A")
            rec_str = rec.strftime("%Y-%m-%d %H:%M:%S") if hasattr(rec, "strftime") else str(rec or "N/A")
            proc_str = proc.strftime("%Y-%m-%d %H:%M:%S") if hasattr(proc, "strftime") else str(proc or "N/A")
            entities_str = f"**{entity}**"
        else:
            auth_val = art.authority.value if hasattr(art.authority, "value") else str(art.authority)
            mat_val = art.materiality.value if hasattr(art.materiality, "value") else str(art.materiality)
            cat_val = art.category.value if hasattr(art.category, "value") else str(art.category)
            sent_val = f"{art.sentiment.label.value} ({art.sentiment.score:+.2f})" if hasattr(art, "sentiment") and hasattr(art.sentiment, "label") else "NEUTRAL"
            title = art.title
            source_name = art.source_name
            summary = getattr(art, "summary", title)
            url = getattr(art, "url", "#")
            fingerprint = getattr(art, "fingerprint", getattr(art, "article_id", "news-hash"))
            entities_str = ", ".join([f"**{e.name}** ({e.ticker or 'N/A'})" for e in art.entities]) if getattr(art, "entities", None) else "None"
            pub = getattr(art, "published_at", None)
            rec = getattr(art, "received_at", None)
            proc = getattr(art, "processed_at", None)
            pub_str = pub.strftime("%Y-%m-%d %H:%M:%S") if hasattr(pub, "strftime") else str(pub or "N/A")
            rec_str = rec.strftime("%Y-%m-%d %H:%M:%S") if hasattr(rec, "strftime") else str(rec or "N/A")
            proc_str = proc.strftime("%Y-%m-%d %H:%M:%S") if hasattr(proc, "strftime") else str(proc or "N/A")

        auth_color = authority_colors.get(auth_val, "#757575")
        mat_color = materiality_colors.get(mat_val, "#757575")

        with st.expander(f"[{mat_val}] {title} — {source_name} ({pub_str} IST)"):
            st.markdown(
                f"""
                <div style="margin-bottom: 10px;">
                    <span style="background-color: {auth_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;">
                        {auth_val}
                    </span>
                    <span style="background-color: {mat_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-left: 8px;">
                        Materiality: {mat_val}
                    </span>
                    <span style="background-color: #212121; color: #e0e0e0; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 8px;">
                        Category: {cat_val}
                    </span>
                    <span style="background-color: #1a237e; color: #e0e0e0; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 8px;">
                        Sentiment: {sent_val}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write(f"**Summary:** {summary}")
            st.write(f"**Identified Entities:** {entities_str}")
            st.markdown(f"**Source URL:** [{url}]({url})")

            # 3 Latency Timestamps
            st.markdown(
                f"""
                <div style="background-color: #121824; padding: 8px; border-radius: 4px; font-size: 0.82em; color: #b0bec5; margin-top: 8px;">
                    ⏱️ <strong>Latency Timestamps:</strong> 
                    Published: <code>{pub_str}</code> | 
                    Received: <code>{rec_str}</code> | 
                    Processed: <code>{proc_str}</code> | 
                    MD5 Fingerprint: <code>{str(fingerprint)[:12]}...</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Non-causal Impact Observation Card
            try:
                st.markdown("##### 📊 Observational Market Impact (Non-Causal)")
                primary_ticker = entity if isinstance(art, dict) else (art.entities[0].ticker if hasattr(art, "entities") and art.entities else "NIFTY")
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
            except Exception:
                pass


if __name__ == "__main__":
    st.set_page_config(page_title="Live News Intelligence Terminal", layout="wide")
    render_live_news_page()
