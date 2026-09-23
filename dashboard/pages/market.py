"""
Market Overview page.

Shows current spot prices, price chart, and basic statistics.
All data comes from real providers — no fake data.
"""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from dashboard.components.data_quality import (
    render_freshness_badge,
    render_provider_info,
)
from src.utils.config import get_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def render_market_page():
    """Render the Market Overview page."""
    st.title("🏠 Market Overview")

    symbol = st.session_state.get("selected_symbol", "NIFTY")
    config = get_config()

    # --- Live Quote ---
    st.subheader(f"{symbol} — Current Quote")

    try:
        from src.ingestion.provider_factory import get_market_provider

        provider = get_market_provider()
        quote = provider.get_quote(symbol)

        render_freshness_badge(quote.timestamp, "Quote")
        render_provider_info(provider.provider_name)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Last Price", f"₹{quote.last_price:,.2f}")
        col2.metric(
            "Change",
            f"₹{quote.change:,.2f}" if quote.change is not None else "N/A",
            delta=f"{quote.change_pct:+.2f}%" if quote.change_pct is not None else None,
        )
        col3.metric("Open", f"₹{quote.open:,.2f}" if quote.open else "N/A")
        col4.metric("Prev Close", f"₹{quote.close:,.2f}" if quote.close else "N/A")

        if quote.high and quote.low:
            col5, col6, col7, col8 = st.columns(4)
            col5.metric("High", f"₹{quote.high:,.2f}")
            col6.metric("Low", f"₹{quote.low:,.2f}")
            day_range = quote.high - quote.low
            col7.metric("Day Range", f"₹{day_range:,.2f}")
            if quote.close and quote.close > 0:
                day_range_pct = (day_range / quote.close) * 100
                col8.metric("Range %", f"{day_range_pct:.2f}%")

    except Exception as e:
        st.error(f"⚠ Cannot retrieve quote for {symbol}: {e}")
        st.info("Check your network connection and data provider configuration.")

    st.divider()

    # --- Price Chart ---
    st.subheader(f"{symbol} — Price History")

    days = st.slider("History (days)", min_value=7, max_value=365, value=90, step=7)

    try:
        from src.ingestion.yfinance_provider import YFinanceProvider
        from dashboard.components.charts import candlestick_chart

        yf_provider = YFinanceProvider()
        end = date.today()
        start = end - timedelta(days=days)
        df = yf_provider.get_ohlcv(symbol, start, end)

        if not df.empty:
            render_provider_info("yfinance")

            fig = candlestick_chart(
                dates=df["date"].tolist(),
                opens=df["open"].tolist(),
                highs=df["high"].tolist(),
                lows=df["low"].tolist(),
                closes=df["close"].tolist(),
                volumes=df["volume"].tolist() if "volume" in df.columns else [0] * len(df),
                title=f"{symbol} — {days}D Price Chart",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Basic stats
            with st.expander("📊 Price Statistics"):
                col1, col2, col3 = st.columns(3)
                col1.metric(f"{days}D High", f"₹{df['high'].max():,.2f}")
                col2.metric(f"{days}D Low", f"₹{df['low'].min():,.2f}")
                if len(df) > 1:
                    returns = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
                    col3.metric(f"{days}D Return", f"{returns:+.2f}%")
        else:
            st.warning("No historical price data available.")

    except Exception as e:
        st.error(f"⚠ Cannot retrieve price history: {e}")

    st.divider()

    # --- Multi-underlying Overview ---
    st.subheader("📈 All Underlyings")

    underlying_data = []
    for u in config.enabled_underlyings:
        try:
            from src.ingestion.provider_factory import get_market_provider
            provider = get_market_provider()
            q = provider.get_quote(u["symbol"])
            underlying_data.append({
                "Symbol": u["symbol"],
                "Name": u["name"],
                "Last Price": f"₹{q.last_price:,.2f}",
                "Change": f"{q.change_pct:+.2f}%" if q.change_pct else "N/A",
                "Lot Size": u.get("lot_size", "N/A"),
            })
        except Exception:
            underlying_data.append({
                "Symbol": u["symbol"],
                "Name": u["name"],
                "Last Price": "Unavailable",
                "Change": "N/A",
                "Lot Size": u.get("lot_size", "N/A"),
            })

    if underlying_data:
        st.dataframe(underlying_data, use_container_width=True, hide_index=True)
