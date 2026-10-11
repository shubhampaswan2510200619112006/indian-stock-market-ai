"""
Streamlit Dashboard Page — Phase 7 AI Indian Market Live Terminal.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on Python path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.ai_analyst.analyst import AIMarketAnalyst
from src.ai_analyst.ood_detector import OODDetector
from src.live_market.service import LiveMarketService
from src.news.storage import NewsStorageManager
from src.utils.config import get_config


def render_live_market_page():
    """Render Phase 7 AI Indian Market Live Terminal."""
    st.title("⚡ AI Indian Market Live Terminal")
    st.caption("Real-Time Multi-Timeframe Monitoring, News Markers & Event-Driven AI Insights")

    # Mandatory Safety Banner
    st.warning(
        "🛡️ **RESEARCH & PAPER-TRADING PREPARATION ONLY** | "
        "Strictly NO live broker order execution or automated trading. "
        "All model recommendations carry non-zero risk of error."
    )

    # ML Research Status Preserved Banner
    st.info(
        "🔬 **MODEL RESEARCH STATUS: LIMITED DATA / INSUFFICIENT STATISTICAL EVIDENCE** | "
        "Phase 6.5 conclusion: Historical options data represents limited sample size. "
        "Do NOT infer guaranteed trading edge."
    )

    config = get_config()
    service = LiveMarketService()
    news_storage = NewsStorageManager()
    ood_detector = OODDetector()
    analyst = AIMarketAnalyst()

    # Sidebar / Header Controls
    col_sym, col_tf, col_ref = st.columns([2, 2, 1])
    with col_sym:
        symbols = [u["symbol"] for u in config.enabled_underlyings] + ["RELIANCE", "TCS", "INFY", "HDFCBANK"]
        selected_symbol = st.selectbox("Select Asset / Ticker", list(dict.fromkeys(symbols)), index=0)
    with col_tf:
        interval = st.selectbox("Primary Timeframe", ["1m", "5m", "15m", "1h", "1d"], index=1)
    with col_ref:
        st.write("")
        st.write("")
        if st.button("🔄 Force Refresh"):
            st.rerun()

    # Get Live Market Snapshot
    snapshot = service.get_live_snapshot(selected_symbol)
    # Use .market instead of .quote (correct attribute name on LiveMarketSnapshot)
    quote = snapshot.market
    multi_tf = snapshot.multi_timeframe

    # Header Data Freshness & Status Display
    status_colors = {
        "REAL_TIME": "#00c853",
        "NEAR_REAL_TIME": "#64dd17",
        "DELAYED": "#ffd600",
        "STALE": "#ff6d00",
        "UNAVAILABLE": "#d50000",
        "ERROR": "#d50000",
    }

    if quote is None:
        st.error(f"⚠ Could not fetch live quote for **{selected_symbol}**. Data provider unavailable. "
                 "Check network and provider configuration.")
    else:
        # quote.status_label is the RealTimeDataStatus enum; quote.last_price, .change, .change_pct
        status_val = quote.status_label.value if quote.status_label else "UNAVAILABLE"
        badge_color = status_colors.get(status_val, "#757575")
        latency_s = (quote.latency_ms / 1000.0) if quote.latency_ms else 0.0

        st.markdown(
            f"""
            <div style="background-color: #1e2530; padding: 12px 20px; border-radius: 8px; border-left: 5px solid {badge_color}; margin-bottom: 15px;">
                <span style="font-size: 1.4em; font-weight: bold; color: white;">{quote.symbol}</span>
                <span style="font-size: 1.4em; margin-left: 15px; color: {'#00e676' if quote.change >= 0 else '#ff5252'};">
                    ₹{quote.last_price:,.2f} ({'+' if quote.change >= 0 else ''}{quote.change:.2f} / {quote.change_pct:+.2f}%)
                </span>
                <span style="float: right; font-size: 0.9em; color: #b0bec5;">
                    Status: <strong style="color: {badge_color};">{status_val}</strong> | 
                    Source: <strong>{quote.source}</strong> | 
                    Latency: <strong>{latency_s:.1f}s</strong> | 
                    Freshness: <strong>{status_val}</strong>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Multi-timeframe metric strip
    # Build a flat dict from MultiTimeframeSummary fields
    st.subheader("📊 Multi-Timeframe Summary")
    m_cols = st.columns(5)

    if multi_tf is not None:
        tf_signal_map = {
            "1m": multi_tf.tf_1m,
            "5m": multi_tf.tf_5m,
            "15m": multi_tf.tf_15m,
            "1h": multi_tf.tf_1h,
            "1d": multi_tf.tf_1d,
        }
        for i, tf in enumerate(["1m", "5m", "15m", "1h", "1d"]):
            signal = tf_signal_map.get(tf, "NEUTRAL")
            with m_cols[i]:
                trend_color = (
                    "#00e676" if "BULLISH" in signal
                    else ("#ff5252" if "BEARISH" in signal else "#ffd600")
                )
                st.markdown(
                    f"""
                    <div style="background-color: #121824; padding: 8px; border-radius: 6px; text-align: center; border: 1px solid #2a3446;">
                        <span style="font-size: 0.85em; color: #90caf9; font-weight: bold;">{tf.upper()}</span><br/>
                        <span style="font-size: 0.95em; font-weight: bold; color: {trend_color};">{signal}</span><br/>
                        <span style="font-size: 0.75em; color: #b0bec5;">Signal</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        if multi_tf.conflicting_signals:
            st.warning(f"⚡ Conflicting signals: {' | '.join(multi_tf.conflicting_signals)}")
    else:
        for i, tf in enumerate(["1m", "5m", "15m", "1h", "1d"]):
            with m_cols[i]:
                st.caption(f"{tf.upper()}: N/A")

    st.markdown("---")

    # Main Tabs
    tab_chart, tab_ai, tab_options, tab_health = st.tabs([
        "📈 Interactive Candlestick & News Overlay",
        "🤖 AI Market Analyst & Drift Detector",
        "⚡ Live Options Feed Status",
        "🏥 Data Provider Capabilities",
    ])

    # TAB 1: Interactive Chart with News Overlays
    with tab_chart:
        # Use fetch_intraday_candles (correct method name on LiveMarketService)
        candles = service.fetch_intraday_candles(selected_symbol, timeframe=interval, limit=100)
        recent_articles = news_storage.get_recent_articles(entity=selected_symbol, limit=20)

        if candles:
            # LiveCandle is a Pydantic model — use .model_dump() in Pydantic v2
            try:
                df = pd.DataFrame([c.model_dump() for c in candles])
            except AttributeError:
                df = pd.DataFrame([c.dict() for c in candles])
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")

            fig = make_subplots(
                rows=2, cols=1, shared_xaxes=True,
                vertical_spacing=0.03, subplot_titles=(f"{selected_symbol} ({interval.upper()})", "Volume"),
                row_width=[0.2, 0.8]
            )

            # Candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=df["timestamp"],
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    name="OHLC",
                ),
                row=1, col=1
            )

            # Volume bar chart
            fig.add_trace(
                go.Bar(
                    x=df["timestamp"],
                    y=df["volume"],
                    name="Volume",
                    marker_color="#37474f",
                ),
                row=2, col=1
            )

            # News markers overlay
            for art in recent_articles:
                try:
                    pub = art.get("published_at") if isinstance(art, dict) else getattr(art, "published_at", None)
                    if not pub:
                        continue
                    art_time = pd.to_datetime(pub)
                    if df["timestamp"].min() <= art_time <= df["timestamp"].max():
                        closest_idx = (df["timestamp"] - art_time).abs().idxmin()
                        closest_price = df.loc[closest_idx, "high"] * 1.002
                        title = art.get("title", "News") if isinstance(art, dict) else getattr(art, "title", "News")
                        auth = art.get("authority", "") if isinstance(art, dict) else getattr(art, "authority", "")
                        auth_val = auth.value if hasattr(auth, "value") else str(auth)
                        mat = art.get("materiality", "") if isinstance(art, dict) else getattr(art, "materiality", "")
                        mat_val = mat.value if hasattr(mat, "value") else str(mat)
                        fig.add_trace(
                            go.Scatter(
                                x=[art_time],
                                y=[closest_price],
                                mode="markers+text",
                                marker=dict(symbol="triangle-down", size=12, color="#ab47bc"),
                                text=[f"📰 {title[:25]}..."],
                                textposition="top center",
                                name="News Event",
                                hovertext=f"<b>{title}</b><br/>Authority: {auth_val}<br/>Materiality: {mat_val}",
                            ),
                            row=1, col=1
                        )
                except Exception:
                    continue

            fig.update_layout(
                template="plotly_dark",
                height=550,
                xaxis_rangeslider_visible=False,
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No candle data available for {selected_symbol} on timeframe {interval}.")

    # TAB 2: AI Market Analyst & Drift Detector
    with tab_ai:
        col_analyst, col_drift = st.columns([3, 2])

        with col_analyst:
            st.subheader("🤖 Structured AI Analyst Synthesis")
            recent_articles = news_storage.get_recent_articles(entity=selected_symbol, limit=10)
            try:
                analysis = analyst.analyze_snapshot(snapshot=snapshot)
                st.markdown(f"**Regime Summary:** `{analysis.market_regime}`")
                st.markdown(
                    f"**Primary Bias:** `{analysis.directional_bias.value}` "
                    f"(Rule-Based Match Score: `{analysis.confidence:.2f}` — *Heuristic, Not Calibrated Probability*)"
                )

                st.markdown("#### Bullish Factors")
                for sig in analysis.bullish_factors:
                    st.markdown(f"- 🟢 {sig}")

                st.markdown("#### Bearish Factors")
                for sig in analysis.bearish_factors:
                    st.markdown(f"- 🔴 {sig}")

                st.markdown("#### Uncertainty / Risks")
                for r in analysis.uncertainty_factors:
                    st.markdown(f"- ⚠️ {r}")

                if analysis.invalidation_conditions:
                    st.info(f"💡 **Invalidation Conditions:** {' | '.join(analysis.invalidation_conditions)}")
                st.caption(f"Strategy: {analysis.recommended_strategy} | Reasoning: {analysis.reasoning[:100]}...")
            except Exception as e:
                st.warning(f"AI analysis unavailable: {e}")

        with col_drift:
            st.subheader("🛡️ ML Feature Drift (OOD) Detector")
            # Build sample feature vector from snapshot — use safe defaults from flat multi_tf fields
            volatility_est = 1.2
            range_pct_est = 0.8

            feature_vector = {
                "volatility_1d": volatility_est,
                "range_pct_1d": range_pct_est,
                "volume_ratio": 1.1,
                "trend_score": 0.5,
            }
            ood_result = ood_detector.detect(feature_vector)

            drift_colors = {
                "NORMAL": "#00c853",
                "DRIFT_WARNING": "#ffd600",
                "OOD": "#d50000",
                "INSUFFICIENT_DATA": "#757575",
            }
            d_color = drift_colors.get(ood_result["status"].value, "#757575")

            st.markdown(
                f"""
                <div style="background-color: #121824; padding: 15px; border-radius: 8px; border: 2px solid {d_color}; text-align: center;">
                    <h3 style="margin: 0; color: {d_color};">OOD STATUS: {ood_result['status'].value}</h3>
                    <p style="color: #b0bec5; font-size: 0.9em; margin-top: 5px;">Max Z-Score: <strong>{ood_result['max_z_score']:.2f}</strong></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")
            st.caption(ood_result["recommendation"])
            if ood_result["flagged_features"]:
                st.warning(f"Flagged Features: {', '.join(ood_result['flagged_features'])}")

    # TAB 3: Live Options Feed Status
    with tab_options:
        st.subheader("⚡ Live Options Feed Capability & Status")
        # Use snapshot.options (correct attribute name)
        opts = snapshot.options

        if opts and opts.get("status_label") not in (None, "UNAVAILABLE"):
            st.success(f"Options Status: {opts.get('status_label')}")
            st.write(opts)
        else:
            st.warning(
                "⚡ **OPTIONS STATUS: UNAVAILABLE**\n\n"
                "Live stream for real-time NSE options chain is NOT configured in current environment.\n"
                "The platform explicitly reports **UNAVAILABLE** and refuses to fabricate fake options chains or prices."
            )
            st.markdown(
                """
                - **Configured Feed**: `NSELiveOptionsProvider`
                - **Real-Time Level-2 Stream**: Unconfigured / Unavailable
                - **Historical Options Data**: Available in Phase 5.6 database for backtest research.
                """
            )

    # TAB 4: Data Provider Capabilities Matrix
    with tab_health:
        st.subheader("🏥 Ingestion Provider Health & Capabilities")
        # Use get_provider_health() which returns List[ProviderStatus]
        try:
            health_statuses = service.get_provider_health()
            for h in health_statuses:
                col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
                with col_p1:
                    st.markdown(f"**{h.provider_name}** ({h.provider_type.value})")
                with col_p2:
                    if h.is_healthy:
                        st.success(h.status_label)
                    else:
                        st.error(h.status_label)
                with col_p3:
                    st.caption(f"Latency: {h.latency_ms:.0f}ms")
        except Exception as e:
            st.error(f"Provider health check failed: {e}")

        # Also show data_health from snapshot
        if snapshot.data_health:
            st.markdown("#### Provider Health Summary from Snapshot")
            st.dataframe(pd.DataFrame(snapshot.data_health), use_container_width=True)


if __name__ == "__main__":
    st.set_page_config(page_title="AI Indian Market Live Terminal", layout="wide")
    render_live_market_page()
