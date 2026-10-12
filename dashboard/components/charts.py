"""
Reusable Plotly chart components.

Professional dark theme, interactive charts for:
- OI distribution (horizontal bar)
- OI change by strike
- IV smile across strikes
- Candlestick with volume
"""

from __future__ import annotations

from typing import Optional

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Consistent dark theme for all charts
CHART_THEME = {
    "paper_bgcolor": "#0e1117",
    "plot_bgcolor": "#0e1117",
    "font_color": "#fafafa",
    "gridcolor": "#1e2530",
    "ce_color": "#ef5350",        # Red for calls
    "pe_color": "#26a69a",        # Green for puts
    "accent_color": "#42a5f5",
    "spot_color": "#ffc107",
    "atm_color": "#ff9800",
    "warning_color": "#ff5722",
}


def oi_distribution_chart(
    strikes: list[float],
    ce_oi: list[int],
    pe_oi: list[int],
    spot_price: float,
    atm_strike: Optional[float] = None,
    title: str = "Open Interest Distribution",
) -> go.Figure:
    """
    Horizontal bar chart showing Call OI (left/red) and Put OI (right/green).
    Spot price overlay as horizontal line.
    """
    fig = go.Figure()

    clean_strikes = [float(s) for s in strikes]
    clean_ce_oi = [int(v) if v is not None else 0 for v in ce_oi]
    clean_pe_oi = [int(v) if v is not None else 0 for v in pe_oi]

    # Calls (negative for left side)
    fig.add_trace(go.Bar(
        y=clean_strikes,
        x=[-oi for oi in clean_ce_oi],
        orientation="h",
        name="Call OI",
        marker_color=CHART_THEME["ce_color"],
        opacity=0.8,
        hovertemplate="Strike: ₹%{y:,.0f}<br>Call OI: %{customdata:,.0f}<extra></extra>",
        customdata=clean_ce_oi,
    ))

    # Puts
    fig.add_trace(go.Bar(
        y=clean_strikes,
        x=clean_pe_oi,
        orientation="h",
        name="Put OI",
        marker_color=CHART_THEME["pe_color"],
        opacity=0.8,
        hovertemplate="Strike: ₹%{y:,.0f}<br>Put OI: %{x:,.0f}<extra></extra>",
    ))

    # Spot price line
    if spot_price and clean_strikes:
        fig.add_hline(
            y=float(spot_price),
            line_dash="dash",
            line_color=CHART_THEME["spot_color"],
            annotation_text=f"Spot: ₹{spot_price:,.2f}",
            annotation_position="top right",
        )

    fig.update_layout(
        title=title,
        barmode="overlay",
        paper_bgcolor=CHART_THEME["paper_bgcolor"],
        plot_bgcolor=CHART_THEME["plot_bgcolor"],
        font=dict(color=CHART_THEME["font_color"], size=12),
        xaxis_title="Open Interest",
        yaxis_title="Strike Price",
        height=max(400, len(strikes) * 20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=80, r=20, t=60, b=40),
    )
    fig.update_xaxes(gridcolor=CHART_THEME["gridcolor"])
    fig.update_yaxes(gridcolor=CHART_THEME["gridcolor"])

    return fig


def oi_change_chart(
    strikes: list[float],
    ce_change: list[int],
    pe_change: list[int],
    spot_price: float,
    title: str = "Change in Open Interest",
) -> go.Figure:
    """Bar chart showing change in OI for CE and PE by strike."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=[str(s) for s in strikes],
        y=ce_change,
        name="Call ΔOI",
        marker_color=CHART_THEME["ce_color"],
        opacity=0.8,
    ))

    fig.add_trace(go.Bar(
        x=[str(s) for s in strikes],
        y=pe_change,
        name="Put ΔOI",
        marker_color=CHART_THEME["pe_color"],
        opacity=0.8,
    ))

    fig.update_layout(
        title=title,
        barmode="group",
        paper_bgcolor=CHART_THEME["paper_bgcolor"],
        plot_bgcolor=CHART_THEME["plot_bgcolor"],
        font=dict(color=CHART_THEME["font_color"], size=12),
        xaxis_title="Strike Price",
        yaxis_title="Change in OI",
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=60, b=40),
    )
    fig.update_xaxes(gridcolor=CHART_THEME["gridcolor"])
    fig.update_yaxes(gridcolor=CHART_THEME["gridcolor"])

    return fig


def iv_smile_chart(
    strikes: list[float],
    ce_iv: list[Optional[float]],
    pe_iv: list[Optional[float]],
    spot_price: float,
    title: str = "IV by Strike (Smile/Skew)",
) -> go.Figure:
    """Line chart showing IV across strikes for CE and PE."""
    fig = go.Figure()

    # Filter None values
    valid_ce = [(s, iv) for s, iv in zip(strikes, ce_iv) if iv is not None and iv > 0]
    valid_pe = [(s, iv) for s, iv in zip(strikes, pe_iv) if iv is not None and iv > 0]

    if valid_ce:
        fig.add_trace(go.Scatter(
            x=[s for s, _ in valid_ce],
            y=[iv for _, iv in valid_ce],
            mode="lines+markers",
            name="Call IV",
            line=dict(color=CHART_THEME["ce_color"], width=2),
            marker=dict(size=5),
        ))

    if valid_pe:
        fig.add_trace(go.Scatter(
            x=[s for s, _ in valid_pe],
            y=[iv for _, iv in valid_pe],
            mode="lines+markers",
            name="Put IV",
            line=dict(color=CHART_THEME["pe_color"], width=2),
            marker=dict(size=5),
        ))

    # Spot price line
    fig.add_vline(
        x=spot_price,
        line_dash="dash",
        line_color=CHART_THEME["spot_color"],
        annotation_text=f"Spot: {spot_price:,.0f}",
    )

    fig.update_layout(
        title=title,
        paper_bgcolor=CHART_THEME["paper_bgcolor"],
        plot_bgcolor=CHART_THEME["plot_bgcolor"],
        font=dict(color=CHART_THEME["font_color"], size=12),
        xaxis_title="Strike Price",
        yaxis_title="Implied Volatility (%)",
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=60, b=40),
    )
    fig.update_xaxes(gridcolor=CHART_THEME["gridcolor"])
    fig.update_yaxes(gridcolor=CHART_THEME["gridcolor"])

    return fig


def candlestick_chart(
    dates: list,
    opens: list[float],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    volumes: list[int],
    title: str = "Price Chart",
) -> go.Figure:
    """Candlestick chart with volume subplot."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.05,
    )

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=dates,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        increasing=dict(line=dict(color=CHART_THEME["pe_color"])),
        decreasing=dict(line=dict(color=CHART_THEME["ce_color"])),
        name="Price",
    ), row=1, col=1)

    # Volume bars
    colors = [
        CHART_THEME["pe_color"] if c >= o else CHART_THEME["ce_color"]
        for o, c in zip(opens, closes)
    ]
    fig.add_trace(go.Bar(
        x=dates,
        y=volumes,
        marker_color=colors,
        opacity=0.5,
        name="Volume",
    ), row=2, col=1)

    fig.update_layout(
        title=title,
        paper_bgcolor=CHART_THEME["paper_bgcolor"],
        plot_bgcolor=CHART_THEME["plot_bgcolor"],
        font=dict(color=CHART_THEME["font_color"], size=12),
        xaxis_rangeslider_visible=False,
        height=500,
        showlegend=False,
        margin=dict(l=60, r=20, t=60, b=40),
    )
    fig.update_xaxes(gridcolor=CHART_THEME["gridcolor"])
    fig.update_yaxes(gridcolor=CHART_THEME["gridcolor"])

    return fig
