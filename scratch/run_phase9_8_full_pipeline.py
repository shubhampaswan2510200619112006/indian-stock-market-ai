"""
Phase 9.8 — Full Research Pipeline Runner.

Executes all Phase 9.8 engines and produces all 6 machine-readable JSON artifacts:
1. data/phase9_8/data_quality.json
2. data/phase9_8/timing_audit.json
3. data/phase9_8/research_registry.json
4. data/phase9_8/multiple_testing.json
5. data/phase9_8/candidate_results.json
6. data/phase9_8/final_gate.json
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))

from src.research.phase9_8.baseline_freeze import Phase97BaselineFreeze
from src.research.phase9_8.candidate_evaluator import Phase98CandidateEvaluator
from src.research.phase9_8.data_quality import Phase98DataQualityEngine
from src.research.phase9_8.final_gate import Phase98FinalGateEngine
from src.research.phase9_8.registry import Phase98HypothesisRegistry
from src.research.phase9_8.timing_audit import Phase98TimingAuditEngine


def run_phase9_8_pipeline():
    print("==================================================================")
    print("RUNNING PHASE 9.8 CONTROLLED EDGE DISCOVERY & MICROSTRUCTURE RESEARCH")
    print("==================================================================")

    # 1. Step 1: Baseline Freeze
    print("[1/6] Verifying Phase 9.7 Frozen Baseline Integrity...")
    freeze_rep = Phase97BaselineFreeze.verify_baseline()
    print(f"  Intact: {freeze_rep.is_frozen_baseline_intact} ({freeze_rep.matched_artifacts}/{freeze_rep.total_artifacts} artifacts matched)")
    assert freeze_rep.is_frozen_baseline_intact, "CRITICAL: Phase 9.7 baseline has been modified!"

    # 2. Step 2: Data Quality & Survivorship Audit
    print("[2/6] Auditing Data Inventory, Completeness & Survivorship...")
    data_rep = Phase98DataQualityEngine.run_full_data_audit()
    print(f"  Total Datasets Audited: {data_rep.total_datasets_audited}")
    print(f"  Verdict: {data_rep.audit_verdict}")
    print(f"  Options Execution Gate: {data_rep.options_execution_gate}")

    # 3. Step 3: Timing & Point-in-Time Audit
    print("[3/6] Auditing Timing & Timestamp Disciplines...")
    timing_rep = Phase98TimingAuditEngine.audit_track_timing()
    print(f"  Compliant: {timing_rep.all_strategies_point_in_time_compliant} ({timing_rep.total_strategies_audited} strategies)")
    print(f"  Backward Returns Found: {timing_rep.backward_return_mappings_found}")

    # 4. Step 4: Register Hypotheses
    print("[4/6] Pre-Registering Frozen Hypotheses P98-H001..P98-H008...")
    Phase98HypothesisRegistry.save_registry()
    print(f"  Total Registered: {len(Phase98HypothesisRegistry.get_all())}")

    # 5. Step 5: Evaluate Candidates & Multi-Testing Guard
    print("[5/6] Evaluating Candidates Across All 7 Tracks...")
    candidates = Phase98CandidateEvaluator.evaluate_all()
    for c in candidates:
        print(f"  [{c.final_classification}] {c.hypothesis_id}: {c.hypothesis_name} | Net Exp: {c.net_expectancy_bps:.1f} bps, Sharpe: {c.annualized_sharpe:.2f}")

    # 6. Step 6: Final Phase 10 Gate Evaluation
    print("[6/6] Evaluating 10 Objective Survival Gates...")
    gate_rep = Phase98FinalGateEngine.evaluate_phase10_gate(candidates)
    print(f"  AUTHORITATIVE DECISION: {gate_rep.authoritative_decision.value}")
    print(f"  Passed Gates: {gate_rep.passed_gate_count}/10 | Failed Gates: {gate_rep.failed_gate_count}/10 | Blocked Gates: {gate_rep.blocked_gate_count}/10")
    print(f"  System Readiness: {gate_rep.system_readiness}")
    print(f"  Live Execution: {gate_rep.live_execution_status}")
    print(f"  Options Execution: {gate_rep.options_execution_gate}")

    print("==================================================================")
    print("PHASE 9.8 RESEARCH PIPELINE RUN COMPLETE. All artifacts generated.")
    print("==================================================================")


if __name__ == "__main__":
    run_phase9_8_pipeline()
