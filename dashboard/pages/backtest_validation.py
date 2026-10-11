"""
Streamlit Dashboard Page: ⏳ Backtesting & Validation (Phase 5.5).

FEATURES & SCIENTIFIC AUDIT:
- Historical Data Availability & Audit Report.
- Ingestion & Data Quality Pipeline.
- Trade Reconciliation Engine.
- Machine Learning (Phase 6) Gate Checklist Evaluator.
- Explicit Labels: "HISTORICAL OPTIONS DATA INSUFFICIENT FOR VALID BACKTEST", "SYNTHETIC TEST DATA — SOFTWARE TESTING ONLY".
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
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.backtesting.models import (
    BacktestConfig,
    CostModelType,
    ExecutionCostModel,
    LiquidityMode,
)
from src.backtesting.engine import BacktestEngine
from src.backtesting.data_gate import DataGate, DataAvailabilityStatus
from src.backtesting.walk_forward import WalkForwardSplitter
from src.backtesting.robustness import RobustnessTester
from src.backtesting.baselines import compute_baseline_comparison
from src.backtesting.reconciliation import reconcile_backtest_trades
from src.backtesting.ml_gate import MLGateEvaluator
from src.ingestion.historical_provider import DatabaseHistoricalOptionsProvider


def render_backtest_validation_page():
    st.title("⏳ Options Strategy Backtesting & Validation Engine")
    st.caption("Phase 5.5: Historical Options Integration, Ingestion Audit, Point-in-Time Isolation & ML Gate Checklist")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Backtest Engine",
        "🔍 Data Quality Audit",
        "🧾 Trade Reconciliation",
        "🚦 Machine Learning Gate",
    ])

    # Sidebar / Top Config Controls
    with st.sidebar.expander("⚙️ Backtest Configuration", expanded=True):
        symbol = st.selectbox("Underlying Symbol", ["NIFTY", "BANKNIFTY", "RELIANCE"], index=0)
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_d = st.date_input("Start Date", date(2026, 1, 1))
        with col_d2:
            end_d = st.date_input("End Date", date(2026, 2, 1))

        strategy_name = st.selectbox(
            "Strategy Template",
            ["Bull Call Spread", "Bear Put Spread", "Long Straddle", "Iron Condor", "Long Call"],
            index=0,
        )

        initial_equity = st.number_input("Initial Equity (INR)", min_value=50000.0, value=1000000.0, step=100000.0)
        max_risk_pct = st.slider("Max Risk per Trade (%)", 1.0, 10.0, 2.0) / 100.0
        min_score = st.slider("Min Strategy Score Threshold", 40.0, 90.0, 60.0)

        liquidity_mode = st.selectbox("Liquidity Filter", ["NORMAL", "STRICT", "RELAXED"], index=0)
        cost_model_choice = st.selectbox("Cost Model", ["BASE", "CONSERVATIVE", "HIGH_COST", "ZERO_COST"], index=0)

        use_synthetic = st.checkbox("Allow Synthetic Test Fixtures if DB Empty", value=True)

    # -------------------------------------------------------------------------
    # TAB 1: Backtest Engine
    # -------------------------------------------------------------------------
    with tab1:
        gate = DataGate()
        availability = gate.evaluate_availability(symbol=symbol, start_date=start_d, end_date=end_d)

        st.subheader("1. Historical Data Availability Report")
        
        if availability.status == DataAvailabilityStatus.AVAILABLE:
            st.success(f"✅ **DATA AVAILABLE**: {availability.message}")
        elif availability.status == DataAvailabilityStatus.PARTIAL:
            st.warning(f"⚠️ **PARTIAL DATA**: {availability.message}")
        else:
            st.error(f"🚫 **{availability.message}**")
            st.info(f"💡 **Recommendation**: {availability.recommendation}")

        st.markdown("---")

        if st.button("🚀 Run Options Strategy Backtest", type="primary"):
            cost_model = ExecutionCostModel(model_type=CostModelType[cost_model_choice])
            if cost_model_choice == "CONSERVATIVE":
                cost_model.slippage_pct = 0.01
            elif cost_model_choice == "HIGH_COST":
                cost_model.slippage_pct = 0.02

            config = BacktestConfig(
                symbol=symbol,
                start_date=start_d,
                end_date=end_d,
                initial_equity=initial_equity,
                max_risk_pct_per_trade=max_risk_pct,
                strategy_name=strategy_name,
                min_strategy_score=min_score,
                liquidity_mode=LiquidityMode[liquidity_mode],
                cost_model=cost_model,
                use_synthetic_if_unavailable=use_synthetic,
            )

            engine = BacktestEngine(config)
            with st.spinner("Executing chronological point-in-time backtest simulation..."):
                result = engine.run()
                st.session_state["latest_backtest_result"] = result

            # Display Critical Labels
            st.subheader("2. Backtest Verification Badges")
            badge_cols = st.columns(len(result.critical_labels))
            for idx, lbl in enumerate(result.critical_labels):
                with badge_cols[idx]:
                    if "SYNTHETIC" in lbl:
                        st.warning(f"🏷️ `{lbl}`")
                    elif "INSUFFICIENT" in lbl or "FRAGILE" in lbl:
                        st.error(f"🏷️ `{lbl}`")
                    else:
                        st.success(f"🏷️ `{lbl}`")

            # Performance Summary Cards
            m = result.metrics
            st.subheader("3. Quantitative Performance Summary")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Net P/L", f"₹{m.net_pnl:,.2f}", f"{m.total_return_pct:.2%}")
            c2.metric("CAGR", f"{m.cagr_pct:.2%}")
            c3.metric("Win Rate", f"{m.win_rate:.1%}", f"{m.winning_trades}W / {m.losing_trades}L")
            c4.metric("Profit Factor", f"{m.profit_factor:.2f}")
            c5.metric("Max Drawdown", f"{m.max_drawdown_pct:.2%}")

            c6, c7, c8, c9, c10 = st.columns(5)
            c6.metric("Sharpe Ratio", f"{m.sharpe_ratio:.2f}")
            c7.metric("Sortino Ratio", f"{m.sortino_ratio:.2f}")
            c8.metric("Expectancy", f"₹{m.expectancy:,.2f}")
            c9.metric("Avg Holding (Days)", f"{m.avg_holding_days:.1f}")
            c10.metric("Total Costs", f"₹{m.total_costs:,.2f}")

            # Equity & Drawdown Chart
            st.subheader("4. Equity & Drawdown Curve")
            if result.equity_curve:
                df_eq = pd.DataFrame([s.model_dump() for s in result.equity_curve])
                fig_eq = go.Figure()
                fig_eq.add_trace(go.Scatter(x=df_eq['timestamp'], y=df_eq['equity'], mode='lines', name='Portfolio Equity (INR)', line=dict(color='#00CC96', width=2)))
                fig_eq.add_trace(go.Scatter(x=df_eq['timestamp'], y=df_eq['cash_balance'], mode='lines', name='Cash Balance', line=dict(color='#636EFA', dash='dot')))
                fig_eq.update_layout(title="Portfolio Equity Curve", xaxis_title="Date", yaxis_title="INR", template="plotly_dark")
                st.plotly_chart(fig_eq, use_container_width=True)

            # Baseline Comparison
            st.subheader("5. Baseline Comparison")
            comp = compute_baseline_comparison(
                strategy_return_pct=m.total_return_pct,
                underlying_start_price=24000.0,
                underlying_end_price=24000.0 * (1 + result.baseline_underlying_return_pct),
            )
            bc1, bc2, bc3 = st.columns(3)
            bc1.metric("Strategy Return", f"{comp.strategy_total_return_pct:.2%}")
            bc2.metric("Buy & Hold Return", f"{comp.underlying_buy_hold_return_pct:.2%}")
            bc3.metric("Outperformance", f"{comp.outperformance_vs_buy_hold_pct:+.2%}")
            st.info(f"📊 **Benchmark Analysis**: {comp.comparison_summary}")

            # Trade Journal Table
            st.subheader("6. Detailed Trade Journal")
            if result.trades:
                df_trades = pd.DataFrame([t.model_dump() for t in result.trades])
                cols_to_show = ["trade_id", "entry_timestamp", "exit_timestamp", "exit_reason", "lots", "gross_pnl", "total_costs", "net_pnl", "holding_days"]
                st.dataframe(df_trades[cols_to_show], use_container_width=True)
            else:
                st.info("No trades executed during this simulation period.")

    # -------------------------------------------------------------------------
    # TAB 2: Data Quality Audit
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("🔍 Historical Options Data Quality Audit")
        provider = DatabaseHistoricalOptionsProvider()
        audit_report = provider.audit_dataset_quality(symbol=symbol, start_date=start_d, end_date=end_d)

        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Total Quote Records", f"{audit_report.total_quote_records:,}")
        a2.metric("Unique Expiries", f"{audit_report.unique_expiries_count}")
        a3.metric("Unique Strikes", f"{audit_report.unique_strikes_count}")
        a4.metric("Total Contracts", f"{audit_report.total_contracts_count}")

        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Missing LTP %", f"{audit_report.missing_ltp_pct:.1%}")
        b2.metric("Missing Bid/Ask %", f"{audit_report.missing_bid_ask_pct:.1%}")
        b3.metric("Missing OI %", f"{audit_report.missing_oi_pct:.1%}")
        b4.metric("Missing Volume %", f"{audit_report.missing_volume_pct:.1%}")

        if audit_report.is_suitable_for_backtesting:
            st.success("✅ **Dataset Audit Passed**: Suitable for historical backtesting.")
        else:
            st.warning("⚠️ **Dataset Audit Alert**: Database currently lacks genuine historical option quote time series.")

        if audit_report.audit_notes:
            st.subheader("Audit Findings & Notes")
            for note in audit_report.audit_notes:
                st.write(f"- 📌 {note}")

    # -------------------------------------------------------------------------
    # TAB 3: Trade Reconciliation
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("🧾 Independent Trade Cashflow & Reconciliation")
        res = st.session_state.get("latest_backtest_result")
        if res and res.trades:
            rec = reconcile_backtest_trades(res)
            
            r1, r2, r3 = st.columns(3)
            r1.metric("Evaluated Trades", rec.total_trades_evaluated)
            r2.metric("100% Reconciled", rec.fully_reconciled_count)
            r3.metric("Discrepancies", rec.discrepancies_count)

            if rec.is_100_pct_reconciled:
                st.success("✅ **100% Reconciliation Verification**: All trade cashflows, fees, and P/L arithmetic match independent calculations.")
            else:
                st.error("❌ Discrepancies detected in trade cashflows.")

            df_rec = pd.DataFrame([item.model_dump() for item in rec.items])
            st.dataframe(df_rec, use_container_width=True)
        else:
            st.info("Run a backtest in Tab 1 to generate trades for independent reconciliation.")

    # -------------------------------------------------------------------------
    # TAB 4: Machine Learning Gate
    # -------------------------------------------------------------------------
    with tab4:
        st.subheader("🚦 Phase 6 Machine Learning Gate Checklist")
        st.markdown("> **Rule**: Phase 6 ML will NOT be started until all 8 criteria pass verification.")

        evaluator = MLGateEvaluator()
        latest_res = st.session_state.get("latest_backtest_result")
        gate_status = evaluator.evaluate_gate(symbol=symbol, recent_backtest_result=latest_res)

        if gate_status.ready_for_phase_6_ml:
            st.success("🎉 **ML GATE UNLOCKED**: All historical data, point-in-time isolation, backtest, and reconciliation criteria passed!")
        else:
            st.error("🛑 **ML GATE LOCKED**: Phase 6 ML cannot be unlocked yet.")
            st.markdown("**Blocking Reasons:**")
            for reason in gate_status.blocking_reasons:
                st.write(f"- ⛔ {reason}")

        st.subheader("Verification Checklist Status")
        for item in gate_status.checklist:
            icon = "✅" if item.is_satisfied else "❌"
            st.write(f"{icon} **{item.criterion}**: {item.details}")

if __name__ == "__main__":
    st.set_page_config(page_title="Backtest Validation", layout="wide")
    render_backtest_validation_page()

