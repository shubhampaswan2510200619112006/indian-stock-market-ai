"""
Streamlit Dashboard Page — Phase 9.5 Large-Sample ML & Statistical Validation Terminal.

Presents rigorous quantitative research results:
- Dataset Coverage & Capability Sufficiency Gates
- Progressive Model Hierarchy (Levels 0-4 + Deep Learning Gate)
- 5-Tier Feature Ablation Analysis (Tiers A-E)
- Chronological Walk-Forward Folds with Dynamic Purging
- Indian Market Transaction Frictions & Economic Metrics
- Robustness Testing: Cost Stress, Slippage Stress, Timing Delay, Regimes
- 95% Block Bootstrap Confidence Intervals
- Final Primary Research Classification & Readiness Matrix
"""

import sys
from pathlib import Path

# Ensure project root is on Python path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))



from datetime import date
import json
from pathlib import Path
import pandas as pd
import streamlit as st

from src.database.connection import get_session
from src.database.models import EquityPriceDB, OptionsContractDB, OptionsQuoteDB
from src.ml.validation_report import Phase95ValidationOrchestrator
from src.paper_trading.execution_guard import ExecutionGuard


def render():
    st.title("🔬 Phase 9.5 — Large-Sample ML & Statistical Validation Terminal")
    st.caption("Point-in-Time Discipline, 5-Tier Ablation, Indian Frictions, Block Bootstrap & Readiness Matrix")

    # Safety Invariant Banner
    guard = ExecutionGuard.get_execution_status()
    st.info(
        f"🔒 **HARD SAFETY INVARIANTS**: Live Execution: `{guard['LIVE_EXECUTION']}` | "
        f"Broker Connections: `{guard['BROKER_CONNECTIONS']}` | "
        f"Paper Options Execution: `BLOCKED (Zero Real-Time Options Feed)`"
    )

    # Load validation report from disk if exists
    report_path = Path("data/phase9_5_validation.json")
    val_data = None
    if report_path.exists():
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                val_data = json.load(f)
        except Exception:
            pass

    if st.button("🔄 Run / Refresh Complete Phase 9.5 Validation Engine"):
        with st.spinner("Executing point-in-time walk-forward validation and stress testing..."):
            session = get_session()
            try:
                eq_rows = session.query(EquityPriceDB).filter(EquityPriceDB.symbol == "NIFTY").order_by(EquityPriceDB.date.asc()).all()
                opt_rows = (
                    session.query(OptionsQuoteDB, OptionsContractDB)
                    .join(OptionsContractDB, OptionsQuoteDB.contract_id == OptionsContractDB.id)
                    .order_by(OptionsQuoteDB.timestamp.asc())
                    .all()
                )
                df_eq = pd.DataFrame([{"date": r.date, "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume} for r in eq_rows])
                df_opt = pd.DataFrame([{"timestamp": q.timestamp, "strike_price": c.strike_price, "option_type": c.option_type, "last_price": q.last_price, "volume": q.volume, "open_interest": q.open_interest} for q, c in opt_rows])
            finally:
                session.close()

            orch = Phase95ValidationOrchestrator()
            res = orch.run_full_validation(df_eq, df_opt, symbol="NIFTY")
            val_data = json.loads(json.dumps(res, default=lambda o: getattr(o, '__dict__', str(o))))
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(val_data, f, indent=2)
            st.success("Phase 9.5 Statistical Validation updated successfully!")

    if not val_data:
        st.warning("No Phase 9.5 validation run found. Click the button above to execute the research pipeline.")
        return

    # Top Verdict Banner
    verdict = val_data.get("primary_classification", "UNKNOWN")
    reason = val_data.get("primary_classification_reason", "")
    if verdict == "STATISTICALLY_PROMISING":
        st.success(f"🏆 **PRIMARY CLASSIFICATION**: `{verdict}`\n\n{reason}")
    elif verdict == "WEAK_INCONCLUSIVE":
        st.warning(f"⚠️ **PRIMARY CLASSIFICATION**: `{verdict}`\n\n{reason}")
    elif verdict == "NO_EVIDENCE_OF_EDGE":
        st.error(f"🛑 **PRIMARY CLASSIFICATION**: `{verdict}`\n\n{reason}")
    else:
        st.info(f"ℹ️ **PRIMARY CLASSIFICATION**: `{verdict}`\n\n{reason}")

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📋 Dataset & Sufficiency",
        "🤖 Model Hierarchy",
        "🧩 5-Tier Ablation",
        "💰 Economic Metrics",
        "⚡ Robustness & Regimes",
        "🎯 Bootstrap CIs",
        "🚦 Readiness Matrix",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: Dataset & Sufficiency
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("Historical Dataset Coverage & Sufficiency Gates")
        d_sum = val_data.get("dataset_summary", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Underlying Sessions", d_sum.get("trading_sessions", 0))
        c2.metric("Date Range", d_sum.get("date_range", "N/A"))
        c3.metric("Option Observations", d_sum.get("option_observations", 0))
        c4.metric("Bid/Ask Coverage", f"{d_sum.get('bid_ask_coverage_pct', 0.0):.1f}%")

        st.markdown("#### Capability-Specific Sufficiency Gates")
        gates = val_data.get("sufficiency_gates", {})
        gate_df = pd.DataFrame([{"Capability": k, "Sufficiency Status": v} for k, v in gates.items()])
        st.dataframe(gate_df, use_container_width=True)

        st.markdown("#### Point-in-Time Leakage Checks")
        leakage = val_data.get("leakage_guard_status", {})
        l_df = pd.DataFrame([{"Check Name": k, "Result": "PASS" if v else "FAIL"} for k, v in leakage.items()])
        st.dataframe(l_df, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 2: Model Hierarchy & Baselines
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("Progressive Model Hierarchy (Levels 0 to 4)")
        models = val_data.get("model_hierarchy_comparison", {})
        m_rows = []
        for m_name, m_data in models.items():
            if isinstance(m_data, dict) and "mean_accuracy" in m_data:
                m_rows.append({
                    "Model": m_name,
                    "Hierarchy Level": m_data.get("level", "N/A"),
                    "Mean OOS Acc": f"{m_data.get('mean_accuracy', 0):.2%}",
                    "Median OOS Acc": f"{m_data.get('median_accuracy', 0):.2%}",
                    "Mean Brier Score": f"{m_data.get('mean_brier_score', 0):.4f}",
                    "OOS Observations": m_data.get("total_oos_predictions", 0),
                })
        st.dataframe(pd.DataFrame(m_rows), use_container_width=True)

        dl = models.get("Level_4_DeepLearning", {})
        if dl:
            st.info(f"🧠 **Level 4 Deep Learning Status**: `{dl.get('DEEP_LEARNING', 'N/A')}`\n\n*Rationale*: {dl.get('reason', '')}")

    # -------------------------------------------------------------------------
    # TAB 3: 5-Tier Ablation Analysis
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("5-Tier Feature Ablation (Incremental Predictive Value)")
        ablation = val_data.get("ablation_results", {})
        ab_rows = []
        for t_name, t_data in ablation.items():
            ab_rows.append({
                "Tier": t_name,
                "Feature Count": t_data.get("feature_count", 0),
                "Mean OOS Acc": f"{t_data.get('mean_accuracy', 0):.2%}",
                "Best OOS Acc": f"{t_data.get('best_accuracy', 0):.2%}",
                "Worst OOS Acc": f"{t_data.get('worst_accuracy', 0):.2%}",
                "Incremental Delta vs Tier A": f"{t_data.get('incremental_accuracy_vs_tier_a', 0):+.2%}",
            })
        st.dataframe(pd.DataFrame(ab_rows), use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 4: Economic Metrics & Realistic Indian Frictions
    # -------------------------------------------------------------------------
    with tab4:
        st.subheader("Economic Performance after Realistic Indian Market Costs")
        econ = val_data.get("economic_evaluation", {})
        if "net_return" in econ:
            ec1, ec2, ec3, ec4 = st.columns(4)
            ec1.metric("Gross Return", f"{econ.get('gross_return', 0):+.2%}")
            ec2.metric("Total Statutory Fees", f"INR {econ.get('total_fees', 0):.4f}")
            ec3.metric("Total Slippage", f"INR {econ.get('total_slippage', 0):.4f}")
            ec4.metric("Net Compounded Return", f"{econ.get('net_return', 0):+.2%}")

            ec5, ec6, ec7, ec8 = st.columns(4)
            ec5.metric("Sharpe Ratio", f"{econ.get('sharpe_ratio', 0):.2f}")
            ec6.metric("Buy & Hold Benchmark Sharpe", f"{econ.get('benchmark_sharpe', 0):.2f}")
            ec7.metric("Max Drawdown", f"{econ.get('max_drawdown', 0):.2%}")
            ec8.metric("Sample Reliability", econ.get("sample_reliability", "N/A"))

    # -------------------------------------------------------------------------
    # TAB 5: Robustness & Market Regimes
    # -------------------------------------------------------------------------
    with tab5:
        st.subheader("Robustness Stress Testing & Market Regime Analysis")
        rob = val_data.get("robustness_summary", {})
        st.write(f"• **Transaction Cost Robust (1.0x to 2.0x)**: `{rob.get('is_cost_robust', False)}`")
        st.write(f"• **Slippage Robust (1.0x to 3.0x)**: `{rob.get('is_slippage_robust', False)}`")
        st.write(f"• **Dominant Regime Concentration**: `{rob.get('dominant_regime_dependence', 'N/A')}`")

        st.markdown("#### Performance Breakdown across 6 Market Regimes")
        reg_data = rob.get("regime_breakdowns", [])
        if reg_data:
            st.dataframe(pd.DataFrame(reg_data), use_container_width=True)

        st.markdown("#### Cost Stress Scenarios")
        st.dataframe(pd.DataFrame(rob.get("cost_stress_scenarios", [])), use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 6: Block Bootstrap 95% Confidence Intervals
    # -------------------------------------------------------------------------
    with tab6:
        st.subheader("Block Bootstrap 95% Confidence Intervals (Accounting for Serial Dependence)")
        boot = val_data.get("bootstrap_results", {})
        if "sharpe_95_ci" in boot:
            s_ci = boot["sharpe_95_ci"]
            e_ci = boot["expectancy_95_ci"]
            b1, b2 = st.columns(2)
            b1.metric("Sharpe 95% CI Lower Bound", f"{s_ci.get('ci_lower', 0):.2f}")
            b1.metric("Sharpe 95% CI Upper Bound", f"{s_ci.get('ci_upper', 0):.2f}")
            b2.metric("Expectancy 95% CI Lower", f"{e_ci.get('ci_lower', 0):.4f}")
            b2.metric("Expectancy 95% CI Upper", f"{e_ci.get('ci_upper', 0):.4f}")
            st.caption(f"Resampling Methodology: {s_ci.get('resampling_unit', '')} | Iterations: {s_ci.get('bootstrap_iterations', 1000)}")
            st.info(s_ci.get("dependence_disclaimer", ""))

    # -------------------------------------------------------------------------
    # TAB 7: Readiness Matrix
    # -------------------------------------------------------------------------
    with tab7:
        st.subheader("Final Phase 9.5 Readiness Matrix")
        matrix = val_data.get("readiness_matrix", {})
        m_df = pd.DataFrame([{"Capability": k, "Readiness State": v} for k, v in matrix.items()])
        st.dataframe(m_df, use_container_width=True)

    # =========================================================================
    # PHASE 9.6: RESEARCH RECALIBRATION & EDGE DISCOVERY
    # =========================================================================
    st.divider()
    st.header("🔭 Phase 9.6 — Research Recalibration & Edge Discovery")
    st.caption("Pre-Registered Hypotheses (H001–H008), Volatility Forecasters, Cost Decomposition & Phase 10 Gate")

    p96_path = Path("data/phase9_6_research_validation.json")
    if p96_path.exists():
        with open(p96_path, "r", encoding="utf-8") as f:
            p96_data = json.load(f)

        # Gate Banner
        p10_gate = p96_data.get("phase_10_gate", "UNKNOWN")
        p10_reason = p96_data.get("phase_10_gate_reason", "")
        p96_class = p96_data.get("primary_classification", "UNKNOWN")
        p96_class_reason = p96_data.get("primary_classification_reason", "")

        c1, c2 = st.columns(2)
        c1.error(f"🛑 **PHASE 10 GATE**: `{p10_gate}`\n\n{p10_reason}")
        c2.warning(f"📊 **HYPOTHESIS STATUS**: `{p96_class}`\n\n{p96_class_reason}")

        t96_1, t96_2, t96_3, t96_4, t96_5 = st.tabs([
            "📜 Pre-Registered Hypotheses",
            "🎯 Multi-Horizon Targets",
            "📈 Volatility Forecasters (H001)",
            "💸 Cost Breakdown (Case A/B/C)",
            "🏆 100-Pt Scores & Shortlist",
        ])

        with t96_1:
            st.subheader("8 Pre-Registered Hypotheses (Audit)")
            evals = p96_data.get("hypothesis_evaluations", {})
            h_rows = []
            for hid, hres in evals.items():
                h_rows.append({
                    "Hypothesis ID": hid,
                    "Status": hres.get("status"),
                    "Primary Metric": hres.get("primary_metric_name"),
                    "Observed Val": f"{hres.get('observed_value', 0):.4f}" if isinstance(hres.get('observed_value'), (int, float)) else str(hres.get('observed_value')),
                    "Threshold": f"{hres.get('threshold_required', 0):.4f}" if isinstance(hres.get('threshold_required'), (int, float)) else str(hres.get('threshold_required')),
                    "Sample Size": hres.get("sample_size"),
                    "Success Met": hres.get("success_criteria_met"),
                })
            st.dataframe(pd.DataFrame(h_rows), use_container_width=True)

        with t96_2:
            st.subheader("Target Reformulation Reassessment")
            tr = p96_data.get("target_reassessment", {})
            st.markdown("#### Directional Targets across Horizons")
            m_dir = tr.get("multi_horizon_direction", {})
            dir_rows = []
            for horiz, dinfo in m_dir.items():
                dir_rows.append({
                    "Horizon": horiz,
                    "Target": dinfo.get("target_name"),
                    "Mean OOS Acc": f"{dinfo.get('mean_oos_accuracy', 0):.2%}",
                    "Baseline Acc": f"{dinfo.get('baseline_accuracy', 0):.2%}",
                    "Incremental": f"{dinfo.get('incremental_accuracy', 0):.2%}",
                    "Brier Score": f"{dinfo.get('brier_score_or_mse', 0):.4f}",
                    "Superior": dinfo.get("is_statistically_superior_to_baseline"),
                })
            st.dataframe(pd.DataFrame(dir_rows), use_container_width=True)

        with t96_3:
            st.subheader("H001: Volatility Persistence vs Forecasting Quality")
            vol = p96_data.get("volatility_research", {})
            st.write(f"• **Volatility Predictability Status**: `{vol.get('predictability_status')}`")
            st.write(f"• **Trading Value Status**: `{vol.get('trading_value_status')}`")
            
            st.markdown("##### Autocorrelation Profile")
            st.json(vol.get("autocorrelation_by_lag", {}))

            st.markdown("##### Out-of-Sample Forecasting Model Quality vs Baselines")
            fc = vol.get("forecasting_models", {})
            fc_rows = []
            for mname, minfo in fc.items():
                fc_rows.append({
                    "Model": mname,
                    "RMSE": f"{minfo.get('rmse', 0):.6f}",
                    "MAE": f"{minfo.get('mae', 0):.6f}",
                    "MAPE (%)": f"{minfo.get('mape', 0):.2f}%",
                    "Direction Acc": f"{minfo.get('directional_accuracy', 0):.2%}",
                    "Beats Naive": minfo.get("beats_naive"),
                    "Beats EWMA": minfo.get("beats_ewma"),
                })
            st.dataframe(pd.DataFrame(fc_rows), use_container_width=True)

        with t96_4:
            st.subheader("Cost Decomposition: Gross Alpha vs Frictions")
            cost_d = p96_data.get("cost_decomposition", {})
            case = cost_d.get("case_classification", "UNKNOWN")
            st.info(f"🏷️ **DIAGNOSTIC CLASSIFICATION**: `{case}`\n\n{cost_d.get('diagnostic_verdict', '')}")

            c_col1, c_col2, c_col3 = st.columns(3)
            c_col1.metric("Gross Return", f"{cost_d.get('gross_return_pct', 0):.2%}")
            c_col2.metric("Statutory Fees + Slippage Drag", f"{cost_d.get('statutory_fees_pct', 0) + cost_d.get('slippage_drag_pct', 0):.2%}")
            c_col3.metric("Net Return", f"{cost_d.get('net_return_pct', 0):.2%}")

            st.markdown("#### Holding Period Turnover Reduction vs Fee Drag")
            turn = p96_data.get("turnover_friction_analysis", {})
            hp_data = turn.get("holding_periods", {})
            turn_rows = []
            for hp, hinfo in hp_data.items():
                turn_rows.append({
                    "Holding Period": hp,
                    "Trades / Session": f"{hinfo.get('trades_per_session', 0):.2f}",
                    "Annualized Turnover": f"{hinfo.get('annualized_turnover', 0):.1f}x",
                    "Annualized Drag": f"{hinfo.get('annualized_friction_drag_pct', 0):.2%}",
                    "Fee Drag Reduction": f"{hinfo.get('fee_drag_reduction_vs_1d_pct', 0):.1%}",
                })
            st.dataframe(pd.DataFrame(turn_rows), use_container_width=True)

        with t96_5:
            st.subheader("100-Point Research Scoring & Top 3 Shortlist")
            scores = p96_data.get("research_scores", [])
            st.dataframe(pd.DataFrame(scores), use_container_width=True)

            shortlist = p96_data.get("top_3_shortlist", [])
            if not shortlist:
                st.warning("⚠️ **Top 3 Candidate Shortlist**: EMPTY (`NO_SURVIVING_HYPOTHESIS`). All candidates disqualified due to negative net Sharpe or failing out-of-sample baselines.")
            else:
                st.success(f"Shortlisted Hypotheses: {shortlist}")
    else:
        st.info("Phase 9.6 results file `data/phase9_6_research_validation.json` not found.")

if __name__ == "__main__":
    st.set_page_config(page_title="Ml Research", layout="wide")
    render()

