"""
Technical Analysis & Institutional Price Action Page for Streamlit Dashboard.

Features:
- Multi-pane interactive chart: Candlestick, Moving Averages, Bollinger Bands, RSI, MACD
- Direct visual overlay of detected Candlestick Patterns (Hammers, Engulfing, Shooting Stars, Doji)
- Dynamic Price Action Key Levels (Support & Resistance lines, Market Structure)
- Real-time data provider latency & freshness status
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on Python path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from datetime import date, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from src.features.price_action import PriceActionEngine
from src.features.technical import compute_technical_features_df, extract_latest_features
from src.features.volatility import calculate_realized_volatility_table
from src.ingestion.provider_factory import get_market_data_provider
from src.ingestion.schemas import TimeFrame
from src.utils.time_utils import is_market_open, now_ist


def render_technical_analysis_page():
    """Renders the Technical Analysis & Price Action dashboard page."""
    symbol = st.session_state.get("selected_symbol", "NIFTY")

    st.title(f"📈 Technical Analysis & Price Action — {symbol}")

    # Provider latency and data timing notice
    provider = get_market_data_provider()
    provider_name = getattr(provider, "provider_name", "Public Feed")
    is_live_broker = "angel" in provider_name.lower() or "kite" in provider_name.lower()
    feed_badge = "⚡ REAL-TIME TICK FEED" if is_live_broker else "⏱️ 15-MIN DELAYED (PUBLIC FEED)"
    feed_color = "#10b981" if is_live_broker else "#f59e0b"

    st.markdown(
        f"""
        <div style="background: rgba(30, 41, 59, 0.6); border-left: 4px solid {feed_color}; border-radius: 6px; padding: 10px 14px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 13px; font-weight: 700; color: #f8fafc;">Active Market Feed: {provider_name}</span>
                    <span style="background: {feed_color}22; color: {feed_color}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; margin-left: 8px;">
                        {feed_badge}
                    </span>
                </div>
                <div style="font-size: 11px; color: #94a3b8;">
                    Time: <b>{now_ist().strftime('%I:%M:%S %p IST')}</b> &nbsp;|&nbsp; Market: <b>{'🟢 OPEN' if is_market_open() else '🔴 CLOSED'}</b>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_tf, col_lookback, col_refresh = st.columns([2, 2, 1])
    with col_tf:
        timeframe_str = st.radio(
            "Candle Timeframe",
            ["Daily (1D)", "Weekly (1W)"],
            horizontal=True,
        )
        tf_enum = TimeFrame.DAILY if "Daily" in timeframe_str else TimeFrame.WEEKLY
    with col_lookback:
        lookback_days = st.slider("Lookback Window (Days)", min_value=60, max_value=365, value=180, step=30)
    with col_refresh:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()

    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days * 2)

    with st.spinner(f"Fetching market data and computing price action features for {symbol}..."):
        try:
            df = provider.get_ohlcv(symbol=symbol, start=start_date, end=end_date)
        except Exception as e:
            st.error(f"Could not load market data for {symbol}: {e}")
            return

    if df.empty or len(df) < 15:
        st.warning(f"Insufficient historical data available for {symbol}.")
        return

    # If weekly selected, resample OHLCV
    if tf_enum == TimeFrame.WEEKLY:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").resample("W-FRI").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }).dropna().reset_index()

    # Compute technical features
    df_feat = compute_technical_features_df(df, symbol=symbol, timeframe=tf_enum)
    latest_feat = extract_latest_features(df, symbol=symbol, timeframe=tf_enum)

    # Detect price action patterns & key levels
    pa_engine = PriceActionEngine(timeframe=tf_enum)
    recent_patterns = pa_engine.detect_patterns(df)
    pattern_markers = pa_engine.scan_all_patterns(df_feat, max_bars=60)
    key_levels = pa_engine.get_key_levels(df)

    # 1. Metric Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Latest Close", f"₹{latest_feat.close:,.2f}")
    with c2:
        rsi_val = f"{latest_feat.rsi_14:.1f}" if latest_feat.rsi_14 else "N/A"
        st.metric("RSI (14)", rsi_val)
    with c3:
        adx_val = f"{latest_feat.adx_14:.1f}" if latest_feat.adx_14 else "N/A"
        st.metric("ADX (Trend)", adx_val)
    with c4:
        st.metric("Structure", key_levels.get("market_structure", "Range").split(" ")[0])
    with c5:
        rv20 = f"{latest_feat.realized_vol_20d * 100:.1f}%" if latest_feat.realized_vol_20d else "N/A"
        st.metric("20D Volatility", rv20)

    st.divider()

    # 2. Multi-Pane Candlestick & Technical Chart
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(
            f"{symbol} Candlesticks, Price Action Levels & Pattern Markers",
            "RSI (14)",
            "MACD (12, 26, 9)",
        ),
        row_heights=[0.58, 0.21, 0.21],
    )

    # Main Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df_feat["timestamp"],
            open=df_feat["open"],
            high=df_feat["high"],
            low=df_feat["low"],
            close=df_feat["close"],
            name="OHLC",
        ),
        row=1,
        col=1,
    )

    # Moving Averages
    if "sma_20" in df_feat.columns:
        fig.add_trace(
            go.Scatter(x=df_feat["timestamp"], y=df_feat["sma_20"], name="SMA 20", line=dict(color="#42a5f5", width=1.5)),
            row=1, col=1
        )
    if "sma_50" in df_feat.columns:
        fig.add_trace(
            go.Scatter(x=df_feat["timestamp"], y=df_feat["sma_50"], name="SMA 50", line=dict(color="#ffb74d", width=1.5)),
            row=1, col=1
        )
    if "sma_200" in df_feat.columns:
        fig.add_trace(
            go.Scatter(x=df_feat["timestamp"], y=df_feat["sma_200"], name="SMA 200", line=dict(color="#ef5350", width=1.5)),
            row=1, col=1
        )

    # Price Action Key Levels (Horizontal Lines)
    if key_levels.get("resistance_20", 0) > 0:
        fig.add_hline(
            y=key_levels["resistance_20"],
            line_dash="dash",
            line_color="#ef4444",
            annotation_text=f"20-Bar Resistance: ₹{key_levels['resistance_20']:,.1f}",
            annotation_position="top left",
            row=1,
            col=1,
        )
    if key_levels.get("support_20", 0) > 0:
        fig.add_hline(
            y=key_levels["support_20"],
            line_dash="dash",
            line_color="#10b981",
            annotation_text=f"20-Bar Support: ₹{key_levels['support_20']:,.1f}",
            annotation_position="bottom left",
            row=1,
            col=1,
        )

    # OVERLAY CANDLESTICK PATTERN MARKERS DIRECTLY ON CHART
    if pattern_markers:
        bull_markers = [m for m in pattern_markers if m["type"] == "BULLISH"]
        bear_markers = [m for m in pattern_markers if m["type"] == "BEARISH"]
        neut_markers = [m for m in pattern_markers if m["type"] == "NEUTRAL"]

        if bull_markers:
            fig.add_trace(
                go.Scatter(
                    x=[m["timestamp"] for m in bull_markers],
                    y=[m["price"] * 0.995 for m in bull_markers],
                    mode="markers+text",
                    marker=dict(symbol="triangle-up", size=11, color="#10b981"),
                    text=[m["pattern"] for m in bull_markers],
                    textposition="bottom center",
                    textfont=dict(size=10, color="#10b981"),
                    name="Bullish Pattern",
                    hoverinfo="text",
                    hovertext=[f"🟢 {m['pattern']}: {m['context']}" for m in bull_markers],
                ),
                row=1, col=1,
            )

        if bear_markers:
            fig.add_trace(
                go.Scatter(
                    x=[m["timestamp"] for m in bear_markers],
                    y=[m["price"] * 1.005 for m in bear_markers],
                    mode="markers+text",
                    marker=dict(symbol="triangle-down", size=11, color="#ef4444"),
                    text=[m["pattern"] for m in bear_markers],
                    textposition="top center",
                    textfont=dict(size=10, color="#ef4444"),
                    name="Bearish Pattern",
                    hoverinfo="text",
                    hovertext=[f"🔴 {m['pattern']}: {m['context']}" for m in bear_markers],
                ),
                row=1, col=1,
            )

        if neut_markers:
            fig.add_trace(
                go.Scatter(
                    x=[m["timestamp"] for m in neut_markers],
                    y=[m["price"] for m in neut_markers],
                    mode="markers",
                    marker=dict(symbol="diamond", size=8, color="#f59e0b"),
                    name="Indecision (Doji)",
                    hoverinfo="text",
                    hovertext=[f"🟡 {m['pattern']}: {m['context']}" for m in neut_markers],
                ),
                row=1, col=1,
            )

    # Bollinger Bands
    if "bb_upper" in df_feat.columns and "bb_lower" in df_feat.columns:
        fig.add_trace(
            go.Scatter(x=df_feat["timestamp"], y=df_feat["bb_upper"], name="BB Upper", line=dict(color="#78909c", width=1, dash="dot")),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_feat["timestamp"], y=df_feat["bb_lower"], name="BB Lower", line=dict(color="#78909c", width=1, dash="dot")),
            row=1, col=1
        )

    # RSI
    if "rsi_14" in df_feat.columns:
        fig.add_trace(
            go.Scatter(x=df_feat["timestamp"], y=df_feat["rsi_14"], name="RSI 14", line=dict(color="#ab47bc", width=1.5)),
            row=2, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#66bb6a", row=2, col=1)

    # MACD
    if "macd" in df_feat.columns:
        fig.add_trace(
            go.Scatter(x=df_feat["timestamp"], y=df_feat["macd"], name="MACD", line=dict(color="#29b6f6", width=1.5)),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=df_feat["timestamp"], y=df_feat["macd_signal"], name="Signal", line=dict(color="#ffa726", width=1.5)),
            row=3, col=1
        )
        colors = ["#26a69a" if val >= 0 else "#ef5350" for val in df_feat["macd_hist"].fillna(0)]
        fig.add_trace(
            go.Bar(x=df_feat["timestamp"], y=df_feat["macd_hist"], name="Histogram", marker_color=colors),
            row=3, col=1
        )

    fig.update_layout(
        template="plotly_dark",
        height=750,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_rangeslider_visible=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # 3. Institutional Price Action & Market Structure Desk
    st.subheader("⚡ Institutional Price Action & Market Structure")
    pa_col1, pa_col2, pa_col3 = st.columns(3)
    with pa_col1:
        st.markdown(f"**Structural Trend:** `{key_levels.get('market_structure')}`")
    with pa_col2:
        st.markdown(f"**20-Bar Resistance:** `₹{key_levels.get('resistance_20', 0):,.2f}` (+{key_levels.get('distance_to_resistance_pct', 0)}%)")
    with pa_col3:
        st.markdown(f"**20-Bar Support:** `₹{key_levels.get('support_20', 0):,.2f}` (-{key_levels.get('distance_to_support_pct', 0)}%)")

    # Pattern Evidence Table
    if recent_patterns:
        st.markdown("#### 🔍 Active Candlestick Pattern Formations")
        pat_data = []
        for p in recent_patterns:
            pat_data.append({
                "Pattern": p.pattern,
                "Confidence": f"{p.confidence*100:.0f}%",
                "Context": p.context,
                "Invalidation Level": p.invalidation_conditions,
                "Historical Behavior": p.historical_relevance or "N/A",
            })
        st.dataframe(pd.DataFrame(pat_data), use_container_width=True, hide_index=True)
    else:
        st.info("No active single-bar candlestick patterns detected on the latest bar.")

    st.divider()

    # 4. Realized Volatility Structure
    st.subheader("📊 Realized Volatility Structure")
    rv_dict = calculate_realized_volatility_table(df, windows=[5, 10, 20, 30, 60])
    rv_df = pd.DataFrame([
        {"Window": "5D", "Realized Volatility (%)": f"{(rv_dict['realized_vol_5d'] or 0)*100:.2f}%"},
        {"Window": "10D", "Realized Volatility (%)": f"{(rv_dict['realized_vol_10d'] or 0)*100:.2f}%"},
        {"Window": "20D", "Realized Volatility (%)": f"{(rv_dict['realized_vol_20d'] or 0)*100:.2f}%"},
        {"Window": "30D", "Realized Volatility (%)": f"{(rv_dict['realized_vol_30d'] or 0)*100:.2f}%"},
        {"Window": "60D", "Realized Volatility (%)": f"{(rv_dict['realized_vol_60d'] or 0)*100:.2f}%"},
    ])
    st.dataframe(rv_df, use_container_width=True, hide_index=True)

    st.caption("ℹ Technical indicators & candlestick patterns are quantitative features with probabilistic interpretations — NEVER deterministic buy/sell guarantees.")


if __name__ == "__main__":
    st.set_page_config(page_title="Technical Analysis", layout="wide")
    render_technical_analysis_page()
