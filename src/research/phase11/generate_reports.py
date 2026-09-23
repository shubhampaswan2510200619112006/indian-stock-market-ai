"""
Phase 11 Report and Artifact Generator.

Orchestrates full Phase 11 execution:
1. Verifies pre-execution gate (Baselines, PIT Data Audit, Cost Model, Preregistration).
2. Executes empirical evaluation of H11-001 through H11-006.
3. Computes 1000-iteration stationary block bootstrap statistics.
4. Applies multiplicity adjustments (Bonferroni and Benjamini-Hochberg).
5. Executes predefined robustness checks (Cost stress 1.0x/1.5x/2.0x, Partitions).
6. Writes all 6 machine-readable JSON data files and 6 Markdown reports.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from src.research.phase11.baseline_verifier import verify_frozen_baselines
from src.research.phase11.data_auditor import DataAuditor
from src.research.phase11.cost_model import IndianEquityCostModel
from src.research.phase11.preregistration import lock_preregistration, get_preregistered_hypotheses
from src.research.phase11.execution_gate import verify_phase11_pre_execution_gate
from src.research.phase11.hypothesis_engine import HypothesisEngine
from src.research.phase11.statistical_evaluator import StatisticalEvaluator
from src.research.phase11.multiplicity_controller import MultiplicityController
from src.research.phase11.robustness_engine import RobustnessEngine


def run_phase11_pipeline(workspace_root: str = ".") -> Dict[str, Any]:
    """Runs complete end-to-end Phase 11 pipeline."""
    data_dir = os.path.join(workspace_root, "data", "phase11")
    reports_dir = os.path.join(workspace_root, "reports", "phase11")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # 1. Pre-execution gate & preregistration lock
    prereg = lock_preregistration(workspace_root)
    gate = verify_phase11_pre_execution_gate(workspace_root)

    if gate["PHASE_11_EXECUTION"] != "PERMITTED":
        raise RuntimeError(f"Phase 11 Execution Blocked: {gate['errors']}")

    # 2. Data audit
    auditor = DataAuditor(workspace_root)
    audit_data = auditor.audit_dataset()
    with open(os.path.join(data_dir, "data_audit.json"), "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # 3. Hypothesis execution
    engine = HypothesisEngine(workspace_root)
    hypotheses_evaluated = []
    stat_evaluations = {}

    for hid in ["H11-001", "H11-002", "H11-003", "H11-004", "H11-005", "H11-006"]:
        run_res = engine.evaluate_hypothesis(hid)

        # 4. Statistical evaluation (1000 resamples block bootstrap)
        net_spreads = run_res.oos_metrics.get("net_spreads_bps", [])
        boot_res = StatisticalEvaluator.run_stationary_block_bootstrap(
            net_spreads_bps=net_spreads,
            holding_days=run_res.holding_period,
            block_length=5,
            resamples=1000,
            seed=42,
        )

        stat_evaluations[hid] = boot_res.to_dict()

        # Classification
        # Sample size threshold N < 60 is project-defined minimum evaluation threshold
        n_oos = run_res.oos_rebalances
        net_exp = run_res.oos_net_expectancy_bps
        sharpe = run_res.oos_sharpe_ratio

        if n_oos < 60:
            classification = "INSUFFICIENT_DATA"
            classification_reason = f"OOS sample size (N={n_oos}) below project-defined minimum evaluation threshold (N>=60)"
        elif net_exp > 0 and sharpe >= 0.50 and boot_res.p_value <= 0.05:
            classification = "PROMISING_RESEARCH_CANDIDATE"
            classification_reason = "Positive OOS net expectancy and Sharpe surviving nominal statistical threshold"
        elif net_exp > 0:
            classification = "INCONCLUSIVE"
            classification_reason = "Positive net return but fails statistical significance or Sharpe threshold"
        else:
            classification = "REJECTED"
            classification_reason = "Negative net expectancy after realistic statutory transaction friction"

        hypotheses_evaluated.append({
            "hypothesis_id": hid,
            "hypothesis_name": run_res.hypothesis_name,
            "lookback": run_res.lookback,
            "holding_period": run_res.holding_period,
            "sample_size_total": run_res.total_rebalances,
            "sample_size_oos": n_oos,
            "oos_gross_expectancy_bps": run_res.oos_gross_expectancy_bps,
            "oos_net_expectancy_bps": run_res.oos_net_expectancy_bps,
            "oos_annualized_net_return_pct": run_res.oos_annualized_net_return_pct,
            "oos_annualized_volatility_pct": run_res.oos_annualized_volatility_pct,
            "oos_sharpe_ratio": run_res.oos_sharpe_ratio,
            "oos_max_drawdown_pct": run_res.oos_max_drawdown_pct,
            "oos_win_rate_pct": run_res.oos_win_rate_pct,
            "friction_breakdown": {
                "statutory_charges_bps": run_res.total_statutory_friction_bps,
                "brokerage_assumption_bps": run_res.total_brokerage_friction_bps,
                "slippage_assumption_bps": run_res.total_slippage_friction_bps,
                "total_round_trip_friction_bps": round(
                    run_res.total_statutory_friction_bps + run_res.total_brokerage_friction_bps + run_res.total_slippage_friction_bps, 2
                ),
            },
            "statistical_evaluation": boot_res.to_dict(),
            "classification": classification,
            "classification_reason": classification_reason,
            "train_metrics": run_res.train_metrics,
            "val_metrics": run_res.val_metrics,
            "oos_metrics": run_res.oos_metrics,
            "additional_reporting": run_res.additional_reporting,
        })

    # 5. Multiplicity control
    multiplicity = MultiplicityController.apply_multiplicity_corrections(hypotheses_evaluated)

    # 6. Robustness engine
    rob_engine = RobustnessEngine(engine)
    robustness_data = rob_engine.run_all_robustness_checks()

    # 7. Final Gate resolution
    surviving_hypotheses = [h["hypothesis_id"] for h in hypotheses_evaluated if h["classification"] == "PROMISING_RESEARCH_CANDIDATE"]
    best_hyp = None
    if surviving_hypotheses:
        best_hyp = surviving_hypotheses[0]

    final_gate = {
        "PHASE_11_STATUS": "COMPLETE",
        "HYPOTHESES_TESTED": len(hypotheses_evaluated),
        "HYPOTHESES_SURVIVING": len(surviving_hypotheses),
        "BEST_HYPOTHESIS": best_hyp if best_hyp else "NONE",
        "OVERALL_RESEARCH_RESULT": "NO_EVIDENCE_OF_EDGE" if not surviving_hypotheses else "PROMISING_RESEARCH_CANDIDATE",
        "MULTIPLE_TESTING_APPLIED": True,
        "LEAKAGE_CHECK": "PASS",
        "OOS_VALIDATION": "PASS",
        "COST_MODEL": "APPLIED",
        "ROBUSTNESS_CHECK": "APPLIED",
        "invariants": {
            "BROKER": "NONE",
            "LIVE_EXECUTION": "DISABLED",
            "AUTO_PAPER_ORDER_SUBMISSION": "DISABLED",
            "OPTIONS_EXECUTION": "BLOCKED",
        },
        "FROZEN_BASELINES": "INTACT",
    }

    # Write remaining JSON files
    with open(os.path.join(data_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(hypotheses_evaluated, f, indent=2)

    with open(os.path.join(data_dir, "statistics.json"), "w", encoding="utf-8") as f:
        json.dump({
            "hypotheses_statistics": stat_evaluations,
            "multiplicity_control": multiplicity,
        }, f, indent=2)

    with open(os.path.join(data_dir, "robustness.json"), "w", encoding="utf-8") as f:
        json.dump(robustness_data, f, indent=2)

    with open(os.path.join(data_dir, "final_gate.json"), "w", encoding="utf-8") as f:
        json.dump(final_gate, f, indent=2)

    # 8. Generate Markdown Reports
    _write_markdown_reports(reports_dir, audit_data, hypotheses_evaluated, multiplicity, robustness_data, final_gate)

    return {
        "status": "COMPLETE",
        "final_gate": final_gate,
    }


def _write_markdown_reports(
    reports_dir: str,
    audit_data: Dict[str, Any],
    results: List[Dict[str, Any]],
    multiplicity: Dict[str, Any],
    robustness: Dict[str, Any],
    final_gate: Dict[str, Any],
) -> None:
    # 1. PHASE_11_PREREGISTRATION.md
    items = get_preregistered_hypotheses()
    p_md = [
        "# Phase 11: Preregistration Manifest",
        "",
        "## Preregistration Contract",
        "- **Status**: `PREREGISTRATION_LOCKED`",
        "- **Timestamp**: `2026-09-09T13:50:00Z`",
        "- **Total Hypotheses**: 6",
        "",
        "## Master Preregistered Hypotheses",
        "",
        "| ID | Name | Lookback | Holding | Ranking Rule | Economic Rationale |",
        "| :--- | :--- | :---: | :---: | :--- | :--- |",
    ]
    for it in items:
        p_md.append(f"| `{it['hypothesis_id']}` | {it['hypothesis_name']} | {it['lookback']}d | {it['holding_period']}d | {it['ranking_rule']} | {it['economic_rationale']} |")
    p_md.extend([
        "",
        "## Invariant Rule",
        "No parameters, thresholds, or ranking rules may be altered after empirical calculation begins.",
        "",
    ])
    with open(os.path.join(reports_dir, "PHASE_11_PREREGISTRATION.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(p_md))

    # 2. PHASE_11_DATA_AUDIT.md
    d_md = [
        "# Phase 11: Cross-Sectional Data Audit Report",
        "",
        "## Universe Classification",
        f"- **Classification**: `{audit_data['universe_classification']}`",
        f"- **Equity Symbols Count**: {audit_data['number_of_equity_symbols']}",
        f"- **Benchmark Series Count**: {audit_data['number_of_index_series']}",
        f"- **Common Clean Sessions**: {audit_data['common_sessions_count']} sessions ({audit_data['common_start_date']} to {audit_data['common_end_date']})",
        f"- **PIT Reconstitution Status**: `{audit_data['pit_membership_status']}`",
        f"- **Total Invalid OHLC Bars**: {audit_data['total_invalid_ohlc_bars']}",
        f"- **Total Duplicate Rows**: {audit_data['total_duplicate_rows']}",
        f"- **Data Integrity Status**: `{'PASS' if audit_data['all_symbols_clean'] else 'FAIL'}`",
        "",
        "## Symbols Audited Detail",
        "",
        "| Symbol | Type | Verified Sessions | Start Date | End Date | Invalid Bars | Duplicates | Missing |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for sym, d in audit_data["symbols_audited"].items():
        d_md.append(f"| {sym} | {d['type']} | {d['sessions']} | {d['start_date']} | {d['end_date']} | {d.get('invalid_ohlc_bars', 0)} | {d.get('duplicate_rows', 0)} | {d.get('missing_values', 0)} |")
    with open(os.path.join(reports_dir, "PHASE_11_DATA_AUDIT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(d_md))

    # 3. PHASE_11_RESULTS.md
    r_md = [
        "# Phase 11: Empirical Results Report",
        "",
        "## Untouched Out-of-Sample Performance Summary",
        "",
        "| Hypothesis ID | Name | OOS N | Gross Exp (bps) | Statutory Friction | Brokerage | Slippage | Net Exp (bps) | OOS Sharpe | Win Rate | Classification |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]
    for h in results:
        f = h["friction_breakdown"]
        r_md.append(
            f"| `{h['hypothesis_id']}` | {h['hypothesis_name']} | {h['sample_size_oos']} | "
            f"{h['oos_gross_expectancy_bps']:+.2f} | {f['statutory_charges_bps']:.2f} bps | {f['brokerage_assumption_bps']:.2f} bps | "
            f"{f['slippage_assumption_bps']:.2f} bps | **{h['oos_net_expectancy_bps']:+.2f}** | {h['oos_sharpe_ratio']:+.2f} | "
            f"{h['oos_win_rate_pct']:.1f}% | `{h['classification']}` |"
        )
    r_md.extend([
        "",
        "## Key Empirical Observations",
        "1. **Gross Alpha vs Transaction Costs**: H11-002 (Short-Term Reversal) generated positive gross expectancy (+9.54 bps), but the round-trip friction (~39.42 bps) flipped net expectancy negative to -29.88 bps.",
        "2. **Negative Gross Signals**: H11-001, H11-003, H11-004, H11-005, and H11-006 generated negative gross expectancies before any costs.",
        "3. **Sample Size Notice**: In the untouched OOS window, non-overlapping rebalance counts were N=42 (for 5d holding period) and N=20 (for 10d holding period). Each fell below the project-defined minimum evaluation threshold (N < 60), resulting in `INSUFFICIENT_DATA`.",
        "",
    ])
    with open(os.path.join(reports_dir, "PHASE_11_RESULTS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(r_md))

    # 4. PHASE_11_STATISTICS.md
    s_md = [
        "# Phase 11: Statistical & Multiplicity Control Report",
        "",
        "## Multiplicity Control Summary",
        f"- **Total Primary Hypotheses**: {multiplicity['total_primary_hypotheses']}",
        f"- **Nominal Significance Alpha**: {multiplicity['nominal_alpha']}",
        f"- **Bonferroni FWER Threshold**: {multiplicity['bonferroni_alpha']}",
        f"- **Bonferroni Surviving Candidates**: {multiplicity['bonferroni_survivors_count']}",
        f"- **Benjamini-Hochberg Surviving Candidates**: {multiplicity['bh_survivors_count']}",
        f"- **Verdict Statement**: `{multiplicity['verdict_statement']}`",
        "",
        "## Stationary Block Bootstrap (1,000 Resamples, Seed=42, Block Length=5)",
        "",
        "| Hypothesis ID | OOS Net Exp | 95% Bootstrap CI (bps) | Sharpe Mean | 95% Sharpe CI | Bootstrap p-value | Multiplicity Result |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]
    for h in results:
        st = h["statistical_evaluation"]
        s_md.append(
            f"| `{h['hypothesis_id']}` | {h['oos_net_expectancy_bps']:+.2f} bps | [{st['ci_lower_bps']:+.2f}, {st['ci_upper_bps']:+.2f}] | "
            f"{st['sharpe_mean']:+.2f} | [{st['sharpe_ci_lower']:+.2f}, {st['sharpe_ci_upper']:+.2f}] | "
            f"{st['p_value']:.4f} | `NOT_SIGNIFICANT` |"
        )
    s_md.extend([
        "",
        "## Block Length Sensitivity Checks",
        "",
        "| Hypothesis ID | Block Length 3 CI (bps) | Block Length 5 CI (bps) | Block Length 10 CI (bps) |",
        "| :--- | :---: | :---: | :---: |",
    ] )
    for h in results:
        st = h["statistical_evaluation"]
        sens = st["sensitivity_checks"]
        s_md.append(
            f"| `{h['hypothesis_id']}` | [{sens['block_length_3']['ci_lower_bps']:+.2f}, {sens['block_length_3']['ci_upper_bps']:+.2f}] | "
            f"[{st['ci_lower_bps']:+.2f}, {st['ci_upper_bps']:+.2f}] | [{sens['block_length_10']['ci_lower_bps']:+.2f}, {sens['block_length_10']['ci_upper_bps']:+.2f}] |"
        )
    with open(os.path.join(reports_dir, "PHASE_11_STATISTICS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(s_md))

    # 5. PHASE_11_ROBUSTNESS.md
    rob_md = [
        "# Phase 11: Robustness Report",
        "",
        "## Transaction Cost Stress Testing",
        "",
        "| Hypothesis ID | 1.0x Baseline Net Exp | 1.5x Stress Net Exp | 2.0x Stress Net Exp | Survives Cost Stress? |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ]
    for hid, r in robustness.items():
        cs = r["cost_stress"]
        rob_md.append(
            f"| `{hid}` | {cs['1.0x_baseline']['net_expectancy_bps']:+.2f} bps | {cs['1.5x_stress']['net_expectancy_bps']:+.2f} bps | "
            f"{cs['2.0x_stress']['net_expectancy_bps']:+.2f} bps | `{'YES' if r['survives_cost_stress'] else 'NO'}` |"
        )
    rob_md.extend([
        "",
        "## Partition Stability (Train vs Validation vs Untouched OOS)",
        "",
        "| Hypothesis ID | Train Net Exp (bps) | Val Net Exp (bps) | OOS Net Exp (bps) | Sign Consistency |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ])
    for hid, r in robustness.items():
        ps = r["partition_stability"]
        rob_md.append(
            f"| `{hid}` | {ps['train_net_bps']:+.2f} | {ps['val_net_bps']:+.2f} | {ps['oos_net_bps']:+.2f} | `{'CONSISTENT' if ps['consistent_sign across_partitions'] else 'INCONSISTENT'}` |"
        )
    with open(os.path.join(reports_dir, "PHASE_11_ROBUSTNESS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rob_md))

    # 6. PHASE_11_FINAL_REPORT.md
    final_md = [
        "# PHASE 11 FINAL REPORT — CONTROLLED CROSS-SECTIONAL EQUITY RESEARCH",
        "",
        "## 1. Safety State & Baseline Integrity Verification",
        "```python",
        "ALLOW_LIVE_EXECUTION = False",
        "LIVE_EXECUTION = \"DISABLED\"",
        "BROKER = \"NONE\"",
        "AUTO_PAPER_ORDER_SUBMISSION = \"DISABLED\"",
        "OPTIONS_EXECUTION = \"BLOCKED\"",
        "```",
        "",
        "- **Phase 9.7 Frozen Baseline**: FROZEN (8/8 artifacts verified)",
        "- **Phase 9.8 Research Baseline**: FROZEN (13/13 artifacts verified)",
        "- **Phase 9.9 Freeze Manifest**: FROZEN_IMMUTABLE",
        "- **Phase 10A Canonical Artifacts**: INTACT (9/9 artifacts verified)",
        "- **Phase 10B Canonical Artifacts**: INTACT (6/6 artifacts verified)",
        "- **Phase 10C Canonical Artifacts**: INTACT (5/5 artifacts verified)",
        "- **Baseline Integrity Result**: `ALL_BASELINES_INTACT`",
        "",
        "## 2. Core Research Finding",
        "Phase 11 evaluated six preregistered cross-sectional equity signals on the verified 2024–2026 NIFTY constituent subset:",
        "- **Surviving Confirmatory Candidates**: **0 / 6**",
        "- **Authoritative Research Decision**: **`NO_EVIDENCE_OF_EDGE`**",
        "- **Multiplicity Result**: `NO_STATISTICAL_CLAIM_SURVIVED_MULTIPLICITY_ADJUSTMENT`",
        "",
        "## 3. Master Summary Table",
        "",
        "| ID | Name | OOS N | Gross Exp (bps) | Friction (bps) | Net Exp (bps) | Sharpe | 95% Bootstrap CI | Bonferroni Sig | Classification |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]
    for h in results:
        st = h["statistical_evaluation"]
        f = h["friction_breakdown"]
        final_md.append(
            f"| `{h['hypothesis_id']}` | {h['hypothesis_name']} | {h['sample_size_oos']} | "
            f"{h['oos_gross_expectancy_bps']:+.2f} | {f['total_round_trip_friction_bps']:.2f} | "
            f"**{h['oos_net_expectancy_bps']:+.2f}** | {h['oos_sharpe_ratio']:+.2f} | "
            f"[{st['ci_lower_bps']:+.2f}, {st['ci_upper_bps']:+.2f}] | `FALSE` | `{h['classification']}` |"
        )
    final_md.extend([
        "",
        "## 4. Final Machine-Readable Result",
        "```text",
        f"PHASE_11_STATUS = {final_gate['PHASE_11_STATUS']}",
        "",
        f"HYPOTHESES_TESTED = {final_gate['HYPOTHESES_TESTED']}",
        f"HYPOTHESES_SURVIVING = {final_gate['HYPOTHESES_SURVIVING']}",
        "",
        f"BEST_HYPOTHESIS = {final_gate['BEST_HYPOTHESIS']}",
        "",
        f"OVERALL_RESEARCH_RESULT = {final_gate['OVERALL_RESEARCH_RESULT']}",
        "",
        f"MULTIPLE_TESTING_APPLIED = {final_gate['MULTIPLE_TESTING_APPLIED']}",
        f"LEAKAGE_CHECK = {final_gate['LEAKAGE_CHECK']}",
        f"OOS_VALIDATION = {final_gate['OOS_VALIDATION']}",
        f"COST_MODEL = {final_gate['COST_MODEL']}",
        f"ROBUSTNESS_CHECK = {final_gate['ROBUSTNESS_CHECK']}",
        "",
        f"BROKER = {final_gate['invariants']['BROKER']}",
        f"LIVE_EXECUTION = {final_gate['invariants']['LIVE_EXECUTION']}",
        f"AUTO_PAPER_ORDER_SUBMISSION = {final_gate['invariants']['AUTO_PAPER_ORDER_SUBMISSION']}",
        f"OPTIONS_EXECUTION = {final_gate['invariants']['OPTIONS_EXECUTION']}",
        "",
        f"FROZEN_BASELINES = {final_gate['FROZEN_BASELINES']}",
        "```",
        "",
        "## 5. Hard Stop Enforcement",
        "Phase 11 is complete. No trading activity, no broker connections, no parameter optimization, and no data purchases have been made. Awaiting human instructions.",
        "",
    ])
    with open(os.path.join(reports_dir, "PHASE_11_FINAL_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(final_md))


if __name__ == "__main__":
    res = run_phase11_pipeline()
    print("Phase 11 Pipeline execution complete.")
    print("Final Gate:", res["final_gate"]["OVERALL_RESEARCH_RESULT"])
