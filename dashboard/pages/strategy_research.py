"""
Options Strategy Research Page for Streamlit Dashboard.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on Python path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


from datetime import date, timedelta

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from src.features.market_regime import MarketRegimeEngine
from src.ingestion.base import DataUnavailableError
from src.ingestion.provider_factory import get_market_data_provider, get_options_provider
from src.ingestion.yfinance_provider import YFinanceProvider
from src.options.surface import compute_expected_move, compute_volatility_surface
from src.preprocessing.cleaning import clean_option_chain
from src.strategies.engine import StrategyResearchEngine
from src.strategies.payoff import generate_payoff_grid
from src.strategies.position_sizing import calculate_position_size
from src.strategies.scenario import compute_scenario_analysis
from src.strategies.suitability import MarketThesis


def render_strategy_research_page():
    """Renders the Options Strategy Research dashboard page."""
    symbol = st.session_state.get("selected_symbol", "NIFTY")

    st.title(f"🎯 Options Strategy Research — {symbol}")

    options_provider = get_options_provider()
    market_provider = get_market_data_provider()

    with st.spinner("Fetching option chain & synthesizing market thesis..."):
        try:
            expiries = options_provider.get_expiry_dates(symbol)
            if not expiries:
                st.warning(f"No active expiries available for {symbol}.")
                return
            selected_expiry = expiries[0]
            chain = options_provider.get_option_chain(symbol, selected_expiry)
            chain = clean_option_chain(chain)
        except Exception as e:
            st.error(f"Could not load option chain for {symbol}: {e}")
            return

    # Synthesize Market Thesis
    end_d = date.today()
    start_d = end_d - timedelta(days=120)

    try:
        nifty_df = market_provider.get_ohlcv(symbol="NIFTY", start=start_d, end=end_d)
        regime_engine = MarketRegimeEngine()
        vix_val = market_provider.get_india_vix() if isinstance(market_provider, YFinanceProvider) else None
        regime_res = regime_engine.evaluate_regime(nifty_df, vix_value=vix_val, symbol=symbol)
    except Exception:
        regime_res = None
        vix_val = None

    surface = compute_volatility_surface(chain)
    atm_iv = surface.atm_iv or 0.15

    d_view = "BULLISH" if (regime_res and "BULL" in regime_res.regime.value) else ("BEARISH" if (regime_res and "BEAR" in regime_res.regime.value) else "NEUTRAL")
    v_view = "IV_HIGH" if (vix_val and vix_val >= 22.0) or atm_iv > 0.22 else ("IV_LOW" if atm_iv < 0.12 else "IV_FAIR")

    thesis = MarketThesis(
        symbol=symbol,
        regime=regime_res,
        surface=surface,
        vix_value=vix_val,
        direction_view=d_view,
        direction_confidence=regime_res.confidence if regime_res else 0.5,
        volatility_view=v_view,
        iv_rv_spread=(atm_iv - 0.15),
    )

    # Execute Strategy Research Engine
    engine = StrategyResearchEngine()
    result = engine.evaluate_strategies(chain, thesis)

    # 1. Market Thesis & Regime Summary Card
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.metric("Regime", regime_res.regime.value if regime_res else "N/A")
    with t2:
        st.metric("Directional Thesis", thesis.direction_view)
    with t3:
        st.metric("Volatility View", thesis.volatility_view)
    with t4:
        st.metric("ATM IV", f"{atm_iv*100:.1f}%")

    st.divider()

    # 2. Mandatory NO-TRADE Decision Banner
    if result.no_trade_decision:
        st.error("🚨 MANDATORY NO-TRADE DECISION TRIGGERED")
        st.markdown("**Reasons:**")
        for reason in result.no_trade_reasons:
            st.markdown(f"- 🛑 {reason}")
        st.caption("The engine enforces strict risk & data-quality gating — never forcing a trade recommendation.")

    # 3. Strategy Candidates Comparison Table
    st.subheader("📊 Evaluated Strategy Candidates")

    if result.candidates:
        comparison_rows = []
        for item in result.candidates:
            c = item.candidate
            s = item.score
            cost_str = f"Debit ₹{c.net_cost_or_credit:,.2f}" if c.net_cost_or_credit > 0 else f"Credit ₹{abs(c.net_cost_or_credit):,.2f}"
            max_p_str = f"₹{c.max_profit:,.2f}" if (c.max_profit is not None and c.max_profit != float("inf")) else "Unlimited"
            max_l_str = f"₹{abs(c.max_loss):,.2f}" if (c.max_loss is not None and c.max_loss != float("-inf")) else "Unlimited"

            comparison_rows.append({
                "Strategy": c.strategy_name,
                "Score": f"{s.overall_score:.1f} / 100",
                "Cost / Credit": cost_str,
                "Capital Req": f"₹{c.capital_required:,.2f}",
                "Max Loss": max_l_str,
                "Max Profit": max_p_str,
                "Net Delta": f"{c.net_greeks.net_delta:.2f}",
                "Regime Match Score": f"{s.confidence*100:.0f}%",
            })
        st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True)
        st.caption("ℹ *Regime Match Score* reflects heuristic alignment with current macro/volatility indicators — NOT an empirical profit probability.")

        st.divider()

        # 4. Strategy Deep-Dive Selection
        selected_strat_name = st.selectbox(
            "Select Strategy for Detailed Payoff & Scenario Analysis",
            [item.candidate.strategy_name for item in result.candidates],
        )

        selected_item = next(item for item in result.candidates if item.candidate.strategy_name == selected_strat_name)
        cand = selected_item.candidate
        score = selected_item.score

        # Explicit Legs Breakdown
        st.subheader(f"📌 Explicit Legs Breakdown — {cand.strategy_name}")
        leg_rows = []
        for leg in cand.legs:
            leg_rows.append({
                "Action": leg.action,
                "Quantity": leg.quantity,
                "Option Type": leg.option_type.value,
                "Strike": f"₹{leg.strike_price:,.0f}",
                "Entry Price": f"₹{leg.entry_price:.2f}",
                "Bid": f"₹{leg.bid:.2f}" if leg.bid else "N/A",
                "Ask": f"₹{leg.ask:.2f}" if leg.ask else "N/A",
                "Spread": f"₹{leg.spread:.2f}" if leg.spread else "N/A",
                "Delta": f"{leg.delta:.3f}" if leg.delta else "N/A",
            })
        st.table(pd.DataFrame(leg_rows))

        # 5. Interactive Payoff Graph
        st.subheader("📈 Expiry Payoff Diagram")
        grid_min = cand.spot_price * 0.90
        grid_max = cand.spot_price * 1.10
        grid_spots = np.linspace(grid_min, grid_max, 200)

        # Convert StrategyLegDetail -> OptionLeg for payoff generator
        from src.options.portfolio_greeks import OptionLeg
        from src.options.pricing import black_scholes_greeks
        t_legs = []
        t_prices = []
        for leg in cand.legs:
            g_obs = black_scholes_greeks(cand.spot_price, leg.strike_price, cand.dte/365.0, 0.07, 0.20, leg.option_type)
            qty_val = leg.quantity if leg.action == "BUY" else -leg.quantity
            t_legs.append(OptionLeg(symbol=cand.symbol, strike_price=leg.strike_price, option_type=leg.option_type, quantity=qty_val, lot_size=leg.lot_size, greeks=g_obs))
            t_prices.append(leg.entry_price)

        payoff_df = generate_payoff_grid(grid_spots, t_legs, t_prices)

        fig_payoff = go.Figure()
        fig_payoff.add_trace(go.Scatter(
            x=payoff_df["underlying_price"],
            y=payoff_df["payoff"],
            name="Expiry P/L (₹)",
            line=dict(color="#42a5f5", width=2.5),
        ))
        fig_payoff.add_hline(y=0.0, line_dash="solid", line_color="#757575")
        fig_payoff.add_vline(x=cand.spot_price, line_dash="dash", line_color="#ffee58", annotation_text=f"Spot: {cand.spot_price:,.2f}")

        for be in cand.breakevens:
            fig_payoff.add_vline(x=be, line_dash="dot", line_color="#66bb6a", annotation_text=f"Breakeven: {be:,.2f}")

        fig_payoff.update_layout(
            template="plotly_dark",
            height=450,
            xaxis_title="Underlying Spot Price at Expiry",
            yaxis_title="Profit / Loss (₹)",
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(fig_payoff, use_container_width=True)

        # 6. Scenario Analysis Matrix
        st.subheader("📉 Price Shock Scenario Matrix")
        exp_move = compute_expected_move(cand.spot_price, cand.expiry_date, atm_iv=atm_iv)
        scen_res = compute_scenario_analysis(cand, t_legs, t_prices, expected_move_pts=exp_move.model_implied_move_pts)

        scen_rows = []
        for sc in scen_res.scenarios:
            scen_rows.append({
                "Scenario": sc.scenario_label,
                "Spot Price": f"₹{sc.underlying_price:,.2f}",
                "Change (%)": f"{sc.price_change_pct:+.2f}%",
                "Expiry P/L (₹)": f"₹{sc.expiry_pl_amount:+,.2f}",
                "Estimated Pre-Expiry P/L (pts)": f"{sc.estimated_pre_expiry_pl_pts:+.2f}",
            })
        st.table(pd.DataFrame(scen_rows))

        # 7. Transparent Decomposable Score Breakdown
        st.subheader("🔎 Transparent Decomposable Score Breakdown")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Directional (25)", f"{score.components.directional_alignment:.1f}")
        with c2:
            st.metric("Volatility (25)", f"{score.components.volatility_alignment:.1f}")
        with c3:
            st.metric("Expected Move (15)", f"{score.components.expected_move_alignment:.1f}")
        with c4:
            st.metric("Liquidity (15)", f"{score.components.liquidity:.1f}")
        with c5:
            st.metric("Risk/Reward (20)", f"{score.components.risk_reward:.1f}")

        col_pos, col_neg = st.columns(2)
        with col_pos:
            st.markdown("**Positive Evidence:**")
            for item in score.positive_evidence:
                st.markdown(f"- ✅ {item}")
        with col_neg:
            st.markdown("**Negative Evidence & Major Risks:**")
            for item in score.negative_evidence + score.major_risks:
                st.markdown(f"- ⚠️ {item}")

        # 8. Interactive Position Sizer
        st.subheader("🧮 Position Sizing Calculator")
        cs1, cs2 = st.columns(2)
        with cs1:
            acc_equity = st.number_input("Account Equity (₹)", min_value=10000.0, max_value=100000000.0, value=500000.0, step=50000.0)
        with cs2:
            max_risk = st.slider("Max Risk per Trade (%)", min_value=0.5, max_value=5.0, value=2.0, step=0.5)

        size_res = calculate_position_size(cand, account_equity=acc_equity, max_risk_pct=max_risk)
        st.info(f"💡 **Position Sizing Output:** {size_res.sizing_explanation}")
        st.markdown(f"- **Suggested Quantity:** {size_res.suggested_lots} Lot(s) ({size_res.suggested_quantity} Units)")
        st.markdown(f"- **Capital Required:** ₹{size_res.capital_required:,.2f}")
        st.markdown(f"- **Max Defined Risk:** ₹{size_res.max_loss_amount:,.2f} ({size_res.actual_risk_pct_of_account:.2f}% of Account)")

        st.warning(f"⚠️ **Disclaimer:** {cand.disclaimer}")

if __name__ == "__main__":
    st.set_page_config(page_title="Strategy Research", layout="wide")
    render_strategy_research_page()

