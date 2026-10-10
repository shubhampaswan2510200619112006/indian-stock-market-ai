"""
Phase 9.6 — Research Recalibration & Edge Discovery Verification Script.

Executes master research evaluator across genuine historical data:
- Preserves Phase 9.5 baseline reference.
- Evaluates 8 pre-registered hypotheses (H001 to H008).
- Audits targets, volatility predictability vs baselines, regimes, conviction, holding periods,
  feature information, options information, cost decomposition, and strategy mapping.
- Verifies data-snooping guard.
- Computes transparent 100-point research scores.
- Determines Top 3 Shortlist and Phase 10 Gate decision.
- Exports complete findings to data/phase9_6_research_validation.json.
- Zero broker connections, zero live trading, options paper execution remains BLOCKED.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import numpy as np
import pandas as pd
from src.database.connection import get_session
from src.database.models import EquityPriceDB, OptionsContractDB, OptionsQuoteDB
from src.paper_trading.execution_guard import ExecutionGuard
from src.research.hypothesis_evaluator import Phase96MasterEvaluator


def run_phase9_6_research_validation():
    print("=" * 85)
    print("PHASE 9.6: RESEARCH RECALIBRATION & EDGE DISCOVERY")
    print("=" * 85)

    # 1. Hard Safety Invariant Check
    guard = ExecutionGuard.get_execution_status()
    print(f"Safety Guard: LIVE_EXECUTION={guard['LIVE_EXECUTION']}, BROKER={guard['BROKER_CONNECTIONS']}")
    assert guard["ALLOW_LIVE_EXECUTION"] is False, "CRITICAL SAFETY VIOLATION: Live execution is enabled!"
    print("Hard Safety Invariant: PASS (ALLOW_LIVE_EXECUTION = False, Broker = None, Options Paper = Blocked)")

    # 2. Verify Phase 9.5 Baseline Integrity
    p95_path = _project_root / "data" / "phase9_5_validation.json"
    assert p95_path.exists(), "Phase 9.5 baseline artifact missing! Phase 9.5 must be preserved."
    with open(p95_path, "r", encoding="utf-8") as f:
        p95_data = json.load(f)
    print(f"\nPhase 9.5 Frozen Baseline: Classification = {p95_data.get('primary_classification')}, Sharpe = {p95_data.get('economic_evaluation', {}).get('sharpe_ratio')}")

    # 3. Ingest & Load Historical Data
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

    print(f"\nDataset Inventory: {len(df_equity)} Sessions, {len(df_options)} Options Quotes (Bid/Ask = 0.0%)")

    # 4. Master Research Evaluation
    evaluator = Phase96MasterEvaluator()
    print("\nExecuting Phase 9.6 Master Research Evaluator...")
    output = evaluator.run_full_recalibration(
        equity_df=df_equity,
        option_quotes_df=df_options,
        symbol="NIFTY",
    )

    # 5. Display Core Research Findings
    print("\n--- Pre-Registered Hypothesis Audit ---")
    audit = output.hypothesis_audit
    print(f"  Total Registered:  {audit.get('total_hypotheses_registered')}")
    print(f"  Total Evaluated:   {audit.get('total_hypotheses_evaluated')}")
    print(f"  Total Surviving:   {audit.get('total_hypotheses_surviving')}")
    print(f"  Total Rejected:    {audit.get('total_hypotheses_rejected')}")
    print(f"  Total Inconclusive:{audit.get('total_hypotheses_inconclusive')}")

    print("\n--- Research Question A: Target Reassessment ---")
    tgt = output.target_reassessment.get("multi_horizon_direction", {})
    for k, v in tgt.items():
        print(f"  {k:<10}: OOS Acc={v.get('mean_oos_accuracy'):.2%}, Baseline={v.get('baseline_accuracy'):.2%}, Delta={v.get('incremental_accuracy'):+.2%}")

    print("\n--- Research Question B: Volatility Predictability vs Tradable Edge ---")
    vol = output.volatility_investigation
    persist = vol.get("persistence", {})
    print(f"  Autocorr Lag 1:    {persist.get('autocorr_lag_1', 0):.4f}, Lag 5: {persist.get('autocorr_lag_5', 0):.4f}")
    print(f"  Best Vol Model:    {vol.get('best_model_name')}")
    print(f"  Superior to EWMA:  {vol.get('is_statistically_superior_to_ewma')}")
    print(f"  Directional Vol Acc:{vol.get('directional_vol_change_accuracy'):.2%}")
    print(f"  Verdict:           {vol.get('trading_edge_verdict')[:80]}...")

    print("\n--- Research Question C: Regime Investigation ---")
    reg = output.regime_investigation
    print(f"  Failure Mode:      {reg.get('primary_failure_mode')}")
    print(f"  Conclusion:        {reg.get('conclusion')[:80]}...")

    print("\n--- Research Question D: Signal Strength & Conviction Buckets ---")
    sig_str = output.signal_strength_investigation
    for b in sig_str.get("bucket_reports", []):
        print(f"  {b.get('bucket_label'):<28}: Count={b.get('observation_count')}, Net PnL={b.get('net_return'):+.2%}, Status={b.get('sample_status')}")

    print("\n--- Research Question E: Long/Short Asymmetry ---")
    asym = output.asymmetry_investigation
    long_rep = asym.get("long_only_report", {})
    short_rep = asym.get("short_only_report", {})
    print(f"  Long Only Net Return:  {long_rep.get('net_return', 0):+.2%}, Sharpe={long_rep.get('sharpe_ratio', 0):.2f}")
    print(f"  Short Only Net Return: {short_rep.get('net_return', 0):+.2%}, Sharpe={short_rep.get('sharpe_ratio', 0):.2f}")
    print(f"  Asymmetry Conclusion:  {asym.get('asymmetry_conclusion')}")

    print("\n--- Research Question F: Holding Period Comparison ---")
    hp = output.holding_period_investigation
    for r in hp.get("results", []):
        print(f"  Holding {r.get('holding_period_sessions')} Session(s): Trades={r.get('total_trades')}, Fee Drag Red={r.get('turnover_reduction_pct'):.1f}%, Net Ret={r.get('net_return'):+.2%}")

    print("\n--- Research Question J: Cost Decomposition ---")
    cost = output.cost_decomposition
    print(f"  Failure Mode:      {cost.get('failure_mode')}")
    print(f"  Gross Return:      {cost.get('gross_pnl_pct'):+.2%}")
    print(f"  Statutory Fees:    {cost.get('statutory_fees_pct'):.4f}")
    print(f"  Execution Slippage:{cost.get('slippage_pct'):.4f}")
    print(f"  Net Return:        {cost.get('net_pnl_pct'):+.2%}")

    print("\n--- Research Question L: Strategy Mapping (LTP Research) ---")
    for sm in output.strategy_mapping:
        print(f"  {sm.get('signal_type'):<24} -> {sm.get('mapped_strategy'):<20} (Win Rate={sm.get('theoretical_win_rate'):.1%}, Status={sm.get('execution_validity_status')[:25]}...)")

    print("\n--- Data-Snooping Audit ---")
    snoop = output.data_snooping_audit
    print(f"  Test Accesses:     {snoop.get('final_untouched_test_accesses')}")
    print(f"  Audit Status:      {snoop.get('status')}")

    print("\n--- Top 3 Research Shortlist ---")
    if output.top_3_shortlist:
        for idx, sl in enumerate(output.top_3_shortlist):
            print(f"  #{idx+1}: {sl.get('hypothesis_id')} (Score: {sl.get('total_score')}/100)")
    else:
        print("  NO_SURVIVING_HYPOTHESIS (Zero hypotheses satisfied all mandatory gating criteria)")

    print("\n--- Primary Research Classification ---")
    print(f"  PRIMARY CLASSIFICATION: {output.primary_classification}")
    print(f"  RATIONALE:              {output.primary_classification_reason}")

    print("\n--- Phase 10 Gate Recommendation ---")
    print(f"  PHASE 10 GATE:          {output.phase_10_gate}")
    print(f"  RATIONALE:              {output.phase_10_gate_reason}")

    def _json_serial(obj):
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, (np.integer, int)):
            return int(obj)
        if isinstance(obj, (np.floating, float)):
            return float(obj)
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return str(obj)

    # 6. Export Report JSON
    out_file = _project_root / "data" / "phase9_6_research_validation.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(asdict(output), f, indent=2, default=_json_serial)

    print(f"\nReport written to: {out_file}")
    print("=" * 85)
    return output


if __name__ == "__main__":
    run_phase9_6_research_validation()
