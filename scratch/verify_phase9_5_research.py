"""
Phase 9.5 — Large-Sample ML + Strategy Statistical Validation Verification Script.

Executes rigorous out-of-sample research methodology against genuine market observations:
- Validates point-in-time timestamp precedence and leakage guards.
- Evaluates progressive model hierarchy (Levels 0-3 + Level 4 Deep Learning Gate).
- Evaluates 5-tier feature ablation (Tiers A-E).
- Evaluates chronological walk-forward with dynamic purging and embargo.
- Models realistic Indian market frictions (STT, NSE turnover, GST, Stamp duty, Slippage).
- Executes cost and slippage stress scenarios and regime analysis.
- Computes 95% Block Bootstrap Confidence Intervals.
- Records all experiments into ExperimentRegistry.
- Exports complete findings to data/phase9_5_validation.json.
- Strictly adheres to ALLOW_LIVE_EXECUTION = False and zero broker connections.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pandas as pd
from src.database.connection import get_session
from src.database.models import EquityPriceDB, OptionsContractDB, OptionsQuoteDB
from src.ml.validation_report import Phase95ValidationOrchestrator
from src.paper_trading.execution_guard import ExecutionGuard


def run_phase9_5_research_validation():
    print("=" * 85)
    print("PHASE 9.5: LARGE-SAMPLE ML + STRATEGY STATISTICAL VALIDATION")
    print("=" * 85)

    # 1. Hard Safety Invariant Check
    guard = ExecutionGuard.get_execution_status()
    print(f"Safety Guard: LIVE_EXECUTION={guard['LIVE_EXECUTION']}, BROKER={guard['BROKER_CONNECTIONS']}")
    assert guard["ALLOW_LIVE_EXECUTION"] is False, "CRITICAL SAFETY VIOLATION: Live execution is enabled!"
    print("Hard Safety Guard: PASS (ALLOW_LIVE_EXECUTION = False, Broker = None)")

    # 2. Ingest & Load Historical Data from DB
    session = get_session()
    try:
        eq_rows = (
            session.query(EquityPriceDB)
            .filter(EquityPriceDB.symbol == "NIFTY")
            .order_by(EquityPriceDB.date.asc())
            .all()
        )
        opt_rows = (
            session.query(OptionsQuoteDB, OptionsContractDB)
            .join(OptionsContractDB, OptionsQuoteDB.contract_id == OptionsContractDB.id)
            .order_by(OptionsQuoteDB.timestamp.asc())
            .all()
        )

        df_equity = pd.DataFrame([
            {
                "date": r.date,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in eq_rows
        ])

        df_options = pd.DataFrame([
            {
                "timestamp": q.timestamp,
                "strike_price": c.strike_price,
                "option_type": c.option_type,
                "last_price": q.last_price,
                "volume": q.volume,
                "open_interest": q.open_interest,
            }
            for q, c in opt_rows
        ]) if opt_rows else pd.DataFrame()

    finally:
        session.close()

    print(f"\nLoaded Historical Data:")
    print(f"  Underlying Equity Sessions: {len(df_equity)} sessions ({df_equity['date'].min()} to {df_equity['date'].max()})")
    print(f"  Options Quotes Available:   {len(df_options)} observations")

    # 3. Master Orchestration
    orchestrator = Phase95ValidationOrchestrator()
    print("\nExecuting Phase 9.5 Research Validation Engine...")
    result = orchestrator.run_full_validation(
        equity_df=df_equity,
        option_quotes_df=df_options,
        symbol="NIFTY",
    )

    # 4. Display Core Findings
    print("\n--- Capability-Specific Data Sufficiency ---")
    for cap, status in result.sufficiency_gates.items():
        print(f"  {cap:<35}: {status}")

    print("\n--- Leakage & Contamination Guard Status ---")
    for chk, clean in result.leakage_guard_status.items():
        print(f"  {chk:<35}: {'CLEAN (PASS)' if clean else 'LEAKAGE DETECTED (FAIL)'}")

    print("\n--- Progressive Model Hierarchy (OOS Accuracy vs Baselines) ---")
    for m_name, metrics in result.model_hierarchy_comparison.items():
        if isinstance(metrics, dict) and "mean_accuracy" in metrics:
            print(f"  {m_name:<30}: Acc={metrics['mean_accuracy']:.2%}, Brier={metrics['mean_brier_score']:.4f}, OOS N={metrics['total_oos_predictions']}")
        elif isinstance(metrics, dict) and "DEEP_LEARNING" in metrics:
            print(f"  {m_name:<30}: {metrics['DEEP_LEARNING']} (Reason: {metrics['reason'][:60]}...)")

    print("\n--- 5-Tier Feature Ablation (Incremental Contribution) ---")
    for tier, res in result.ablation_results.items():
        print(f"  {tier:<30}: Feats={res['feature_count']}, Acc={res['mean_accuracy']:.2%}, Delta={res['incremental_accuracy_vs_tier_a']:+.2%}")

    print("\n--- Economic Metrics & Indian Market Frictions ---")
    econ = result.economic_evaluation
    if "net_return" in econ:
        print(f"  Gross Return:       {econ['gross_return']:+.2%}")
        print(f"  Total Fees:         INR {econ['total_fees']:.4f} (STT + Exchange + GST + Stamp)")
        print(f"  Total Slippage:     INR {econ['total_slippage']:.4f}")
        print(f"  Net Return:         {econ['net_return']:+.2%}")
        print(f"  Sharpe Ratio:       {econ['sharpe_ratio']:.2f} (Benchmark B&H: {econ['benchmark_sharpe']:.2f})")
        print(f"  Max Drawdown:       {econ['max_drawdown']:.2%}")
        print(f"  Sample Status:      {econ['sample_reliability']}")

    print("\n--- Robustness & Stress Scenarios ---")
    rob = result.robustness_summary
    print(f"  Cost Robust (1.0x-2.0x):     {rob.get('is_cost_robust', False)}")
    print(f"  Slippage Robust (1.0x-3.0x): {rob.get('is_slippage_robust', False)}")
    print(f"  Dominant Regime:             {rob.get('dominant_regime_dependence', 'UNKNOWN')}")

    print("\n--- Block Bootstrap 95% Confidence Intervals ---")
    boot = result.bootstrap_results
    if "sharpe_95_ci" in boot:
        shp_ci = boot["sharpe_95_ci"]
        exp_ci = boot["expectancy_95_ci"]
        print(f"  Sharpe Ratio 95% CI: [{shp_ci.get('ci_lower', 0):.2f}, {shp_ci.get('ci_upper', 0):.2f}] (Mean={shp_ci.get('mean_estimate', 0):.2f})")
        print(f"  Expectancy 95% CI:   [{exp_ci.get('ci_lower', 0):.4f}, {exp_ci.get('ci_upper', 0):.4f}] (Mean={exp_ci.get('mean_estimate', 0):.4f})")

    print("\n--- Final Primary Research Classification ---")
    print(f"  PRIMARY CLASSIFICATION: {result.primary_classification}")
    print(f"  RATIONALE:              {result.primary_classification_reason}")

    print("\n--- Final Readiness Matrix ---")
    for k, v in result.readiness_matrix.items():
        print(f"  {k:<35}: {v}")

    # 5. Export JSON Artifacts
    output_dict = {
        "generated_at": result.generated_at,
        "phase": "PHASE_9_5_STATISTICAL_VALIDATION",
        "safety_status": result.safety_status,
        "dataset_summary": result.dataset_summary,
        "sufficiency_gates": result.sufficiency_gates,
        "leakage_guard_status": result.leakage_guard_status,
        "model_hierarchy_comparison": result.model_hierarchy_comparison,
        "ablation_results": result.ablation_results,
        "calibration_results": result.calibration_results,
        "walk_forward_summary": result.walk_forward_summary,
        "economic_evaluation": result.economic_evaluation,
        "options_research_status": result.options_research_status,
        "strategy_validation": result.strategy_validation,
        "ml_incremental_value": result.ml_incremental_value,
        "robustness_summary": result.robustness_summary,
        "bootstrap_results": result.bootstrap_results,
        "multiple_testing_audit": result.multiple_testing_audit,
        "primary_classification": result.primary_classification,
        "primary_classification_reason": result.primary_classification_reason,
        "readiness_matrix": result.readiness_matrix,
    }

    out_file1 = _project_root / "data" / "phase9_5_validation.json"
    out_file2 = _project_root / "data" / "phase9_5_research_validation.json"
    out_file1.parent.mkdir(parents=True, exist_ok=True)

    with open(out_file1, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, indent=2)
    with open(out_file2, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, indent=2)

    print(f"\nArtifact saved to: {out_file1}")
    print(f"Artifact saved to: {out_file2}")
    print("=" * 85)
    return output_dict


if __name__ == "__main__":
    run_phase9_5_research_validation()
