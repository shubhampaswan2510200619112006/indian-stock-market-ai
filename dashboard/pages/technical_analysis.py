"""
Technical Analysis Page for Streamlit Dashboard.
"""

from __future__ import annotations

from datetime import date, timedelta

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st

from src.features.price_action import PriceActionEngine
from src.features.technical import compute_technical_features_df, extract_latest_features
from src.features.volatility import calculate_realized_volatility_table
from src.ingestion.provider_factory import get_market_data_provider
from src.ingestion.schemas import TimeFrame


def render_technical_analysis_page():
    """Renders the Technical Analysis dashboard page."""
    symbol = st.session_state.get("selected_symbol", "NIFTY")

    st.title(f"📈 Technical Analysis — {symbol}")

    col_tf, col_lookback = st.columns([2, 2])
    with col_tf:
        timeframe_str = st.radio(
            "Timeframe",
            ["Daily (1D)", "Weekly (1W)"],
            horizontal=True,
        )
        tf_enum = TimeFrame.DAILY if "Daily" in timeframe_str else TimeFrame.WEEKLY
    with col_lookback:
        lookback_days = st.slider("Lookback Window (Days)", min_value=60, max_value=365, value=180, step=30)

    provider = get_market_data_provider()
    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days * 2)

    with st.spinner(f"Fetching market data for {symbol}..."):
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

    # Detect price action patterns
    pa_engine = PriceActionEngine(timeframe=tf_enum)
    patterns = pa_engine.detect_patterns(df)

    # Metric Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Close Price", f"₹{latest_feat.close:,.2f}")
    with c2:
        rsi_val = f"{latest_feat.rsi_14:.1f}" if latest_feat.rsi_14 else "N/A"
        st.metric("RSI (14)", rsi_val)
    with c3:
        adx_val = f"{latest_feat.adx_14:.1f}" if latest_feat.adx_14 else "N/A"
        st.metric("ADX (14)", adx_val)
    with c4:
        trend_val = f"{latest_feat.trend_strength:.1f}/100" if latest_feat.trend_strength else "N/A"
        st.metric("Trend Strength", trend_val)
    with c5:
        rv20 = f"{latest_feat.realized_vol_20d * 100:.1f}%" if latest_feat.realized_vol_20d else "N/A"
        st.metric("20D Realized Vol", rv20)

    st.divider()

    # Create Multi-Pane Chart
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f"{symbol} Price & Moving Averages", "RSI (14)", "MACD (12, 26, 9)"),
        row_heights=[0.55, 0.22, 0.23],
    )

    # Candlestick
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
        fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", row=2, col=1)
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
        height=700,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_rangeslider_visible=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Realized Volatility Section
    st.subheader("📊 Realized Volatility Structure")
    rv_dict = calculate_realized_volatility_table(df, windows=[5, 10, 20, 30, 60])
    rv_df = pd.DataFrame([
        {"Window": "5D", "Realized Volatility (%)": f"{(rv_dict['realized_vol_5d'] or 0)*100:.2f}%"},
        {"Window": "10D", "Realized Volatility (%)": f"{(rv_dict['realized_vol_10d'] or 0)*100:.2f}%"},
        {"Window": "20D", "Realized Volatility (%)": f"{(rv_dict['realized_vol_20d'] or 0)*100:.2f}%"},
        {"Window": "30D", "Realized Volatility (%)": f"{(rv_dict['realized_vol_30d'] or 0)*100:.2f}%"},
        {"Window": "60D", "Realized Volatility (%)": f"{(rv_dict['realized_vol_60d'] or 0)*100:.2f}%"},
    ])
    st.table(rv_df)

    # Price Action Patterns Section
    st.subheader("🔍 Detected Price Action Patterns")
    if patterns:
        pat_data = []
        for p in patterns:
            pat_data.append({
                "Pattern": p.pattern,
                "Pattern Match Score (Heuristic)": f"{p.confidence*100:.0f}%",
                "Context": p.context,
                "Invalidation Condition": p.invalidation_conditions,
                "Historical Relevance": p.historical_relevance or "N/A",
            })
        st.dataframe(pd.DataFrame(pat_data), use_container_width=True)
    else:
        st.info("No notable candlestick patterns detected on recent price bars.")

    st.caption("ℹ Technical indicators & price patterns are quantitative features with probabilistic interpretations — NEVER deterministic buy/sell signals.")
