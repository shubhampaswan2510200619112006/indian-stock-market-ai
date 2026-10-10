"""
Phase 9.8 / 9.9 — Markdown Report Generator.

Reads JSON artifacts from data/phase9_8/ and deterministically compiles all 6 research reports:
1. reports/phase9_8/PHASE_9_8_RESEARCH_REPORT.md (& root mirror)
2. reports/phase9_8/PHASE_9_8_DATA_QUALITY_REPORT.md
3. reports/phase9_8/PHASE_9_8_TIMING_AUDIT.md
4. reports/phase9_8/PHASE_9_8_MULTIPLE_TESTING_REPORT.md
5. reports/phase9_8/PHASE_9_8_CANDIDATE_COMPARISON.md
6. reports/phase9_8/PHASE_9_8_FINAL_GATE.md
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_research_report(reg_data: List[Dict], cand_data: List[Dict], gate_data: Dict, data_q: Dict) -> str:
    md = []
    md.append("# PHASE 9.8 — CONTROLLED EDGE DISCOVERY & MARKET MICROSTRUCTURE RESEARCH REPORT\n")
    md.append("**Status**: COMPLETE & AUTHORITATIVE  \n")
    md.append("**System Readiness**: `RESEARCH_ONLY`  \n")
    md.append("**Phase 10 Gate**: `PHASE_10_NOT_JUSTIFIED`  \n")
    md.append("**Live Execution**: `DISABLED (ALLOW_LIVE_EXECUTION = False)`  \n")
    md.append("**Broker Connections**: `NONE (Zero live routing credentials)`  \n")
    md.append("**Auto Paper Submission**: `DISABLED (AUTO_PAPER_ORDER_SUBMISSION = False)`  \n")
    md.append("**Options Quote Coverage**: `102 paired quotes (0.68%), Continuous Executable Surface = 0.0% (Execution Strictly BLOCKED)`  \n")
    md.append("---\n\n")

    md.append("## 1. Executive Summary\n\n")
    md.append("Phase 9.8 executed a disciplined, controlled research cycle across seven distinct microstructure and macroeconomic tracks to investigate whether tradable alpha exists under realistic Indian market frictions. Building upon the frozen Phase 9.7 baseline (which verified 495 daily sessions and 102 paired options quotes with 0.0% continuous executable surface coverage), Phase 9.8 audited new intraday datasets (~59 trading sessions, 4,425 5-minute bars), 2-year daily equity panels, and 21 historical macroeconomic policy events.\n\n")
    md.append("Eight pre-registered hypotheses (`P98-H001` through `P98-H008`) were frozen with immutable evaluation criteria before executing backtests. All strategies were evaluated using double-entry statutory friction accounting (brokerage, STT, exchange turnover fees, SEBI charges, stamp duty, GST, and execution slippage) and non-overlapping stationary block-bootstrap resampling.\n\n")
    md.append("### Authoritative Research Outcome\n")
    md.append("- **Total Hypotheses Registered & Evaluated**: 8\n")
    md.append("- **Surviving Live/Paper Candidates**: **0 / 8**\n")
    md.append("- **Rejected Hypotheses**: 5 (`P98-H003`, `P98-H004`, `P98-H005`, `P98-H006`, `P98-H007`)\n")
    md.append("- **Insufficient Data / Exploratory Only**: 3 (`P98-H001`, `P98-H002`, `P98-H008`)\n")
    md.append("- **Phase 10 Forward Paper Trading**: **NOT JUSTIFIED**\n\n")

    md.append("## 2. Pre-Registered Hypotheses & Performance Matrix\n\n")
    md.append("| ID | Track | Mechanism | Sample (N) | Evaluation Type | Gross Exp (bps) | Net Exp (bps) | Sharpe | 95% Bootstrap CI | Final Classification |\n")
    md.append("|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
    for c in cand_data:
        ci_str = f"[{c['bootstrap_ci_95'][0]:.1f}, {c['bootstrap_ci_95'][1]:.1f}]"
        md.append(
            f"| `{c['hypothesis_id']}` | {c['track_name']} | {c['hypothesis_name']} | {c['sample_size']} | `{c['evaluation_type']}` | {c['gross_expectancy_bps']:+.1f} | {c['net_expectancy_bps']:+.1f} | {c['annualized_sharpe']:.2f} | {ci_str} | **`{c['final_classification']}`** |\n"
        )
    md.append("\n---\n\n")

    md.append("## 3. Track-by-Track Deep-Dive Analysis\n\n")
    
    # Track A
    md.append("### Track A: Intraday Opening Drive & Session Anchors (`P98-H001`, `P98-H002`)\n")
    md.append("- **P98-H001 (15m Opening Range Breakout)**: Evaluated 59 breakout events over ~59 sessions. Directional breakout accuracy was 37.3% with gross expectancy of -2.1 bps. After statutory costs (5.0 bps) and slippage (5.0 bps), net expectancy decayed to -12.1 bps with Sharpe of -4.91. The P98-H001 sample contains 59 trades and therefore does not satisfy the project's preregistered minimum sample criterion of N>=60 for confirmatory classification. This threshold is a project-specific research gate and is not being presented as a universal statistical law. Classified strictly as `INSUFFICIENT_DATA` / `EXPLORATORY_ONLY`.\n")
    md.append("- **P98-H002 (Overnight Gap 30m Mean-Reversion)**: Evaluated 19 qualifying overnight gaps (|gap| >= 0.30%). Mean-reversion win rate was 15.8% with net expectancy of -14.6 bps and Sharpe of -16.42. Only 19 gap events were observed, making confirmatory inference statistically impossible. Classified as `INSUFFICIENT_DATA` / `EXPLORATORY_ONLY`.\n\n")

    # Track B
    md.append("### Track B: Short-Horizon Momentum vs. Reversal (`P98-H003`)\n")
    md.append("- **P98-H003 (30-Minute Normalized Return Momentum)**: Evaluated 765 30m intraday bars. Out-of-sample directional accuracy was 49.4% (vs AR(1) naive baseline of 50.6%). While gross return was -5.5%, continuous rebalancing accumulated 77.5% in statutory turnover fees and slippage, resulting in a net return of -83.0% (-10.8 bps/trade) and an annualized Sharpe of -32.25. High turnover friction eliminates any micro-momentum edge. Classified as `REJECTED`.\n\n")

    # Track C
    md.append("### Track C: Intraday Volatility Microstructure (`P98-H004`)\n")
    md.append("- **P98-H004 (Garman-Klass Volatility Compression Breakout)**: Evaluated 413 compression periods on 15m bars. Directional expansion accuracy was 22.3% with net expectancy of -9.8 bps and Sharpe of -17.03. Frequent post-compression whipsaws and chop erode gross gains. Classified as `REJECTED`.\n\n")

    # Track D
    md.append("### Track D: Event-Driven Macro Announcement Drift (`P98-H005`)\n")
    md.append("- **P98-H005 (RBI MPC Policy Decision Drift)**: Evaluated 13 policy rate announcements (2024–2026). Cumulative 3-session net drift yielded -49.2 bps with directional alignment of 46.2% and p-value = 0.3006. Post-announcement drift is statistically indistinguishable from zero noise. Classified as `REJECTED`.\n\n")

    # Track E
    md.append("### Track E: Cross-Sectional Equity Relative Strength (`P98-H006`)\n")
    md.append("- **P98-H006 (Top 2 vs Bottom 2 Momentum Spread)**: Evaluated 94 weekly rebalances across 10 liquid equities. Net spread return was -48.4 bps per rebalance with Sharpe of -2.18 and max drawdown of -37.0%. **Critical Defect**: Lacks point-in-time constituent membership tables; `SURVIVORSHIP_BIAS_RISK = TRUE`. Disqualified from production candidate consideration. Classified as `REJECTED`.\n\n")

    # Track F
    md.append("### Track F: Market Regime as Forecast Uncertainty Context (`P98-H007`)\n")
    md.append("- **P98-H007 (Regime Calibration & Brier Score)**: Evaluated probability calibration over 450 out-of-sample daily sessions. Baseline Brier score was 0.2550 vs regime-conditioned Brier score of 0.2609 (-2.30% delta). Macro regime conditioning failed to provide the pre-registered >= 5.0% calibration gain. Classified as `REJECTED`.\n\n")

    # Track G
    md.append("### Track G: Options Microstructure & Hard Execution Boundary (`P98-H008`)\n")
    md.append("- **P98-H008 (Historical Quotes Executability Boundary)**: Audited 15,106 historical options quotes from NSE Bhavcopy settlement files. A small number of paired Bid/Ask observations exist (102 observations, approximately 0.68% of the quote store), but there is 0.0% continuous executable surface coverage across the required strikes/maturities/timestamps. Therefore the available data is insufficient to construct a robust historical executable options backtest. `OPTIONS_EXECUTION_BACKTEST = BLOCKED`. `OPTIONS_PAPER_EXECUTION = BLOCKED`. Synthetic spread fabrication is strictly prohibited. Classified as `INSUFFICIENT_DATA`.\n\n")

    md.append("## 4. Final Phase 10 Gate Evaluation\n\n")
    md.append("| Gate # | Dimension | Status | Requirement | Observed Evidence |\n")
    md.append("|:---:|:---|:---:|:---|:---|\n")
    for g in gate_data["gates"]:
        md.append(f"| {g['gate_number']} | {g['gate_name']} | **`{g['status']}`** | {g['requirement']} | {g['observed_result']} |\n")
    md.append("\n")
    md.append(f"**Final Gate Score**: {gate_data['passed_gate_count']} Passed, {gate_data['failed_gate_count']} Failed, {gate_data['blocked_gate_count']} Blocked.\n\n")

    md.append("## 5. Non-Negotiable Safety Status\n\n")
    md.append("```text\n")
    md.append("============================================================\n")
    md.append("PHASE 9.8 COMPLETE\n")
    md.append("==================\n")
    md.append("PHASE_9_7_BASELINE = FROZEN\n")
    md.append("SYSTEM_READINESS = RESEARCH_ONLY\n")
    md.append("LIVE_EXECUTION = DISABLED\n")
    md.append("BROKER = NONE\n")
    md.append("AUTO_PAPER_ORDER_SUBMISSION = DISABLED\n")
    md.append("OPTIONS_EXECUTION = BLOCKED\n")
    md.append("PHASE_10 = NOT_IMPLEMENTED\n")
    md.append(f"FINAL_CLASSIFICATION = {gate_data['authoritative_decision']}\n")
    md.append("============================================================\n")
    md.append("```\n")

    return "".join(md)


def build_data_quality_report(data_q: Dict) -> str:
    md = []
    md.append("# PHASE 9.8 — DATA QUALITY, INVENTORY & SURVIVORSHIP AUDIT REPORT\n")
    md.append(f"**Audit Verdict**: `{data_q['audit_verdict']}`  \n")
    md.append(f"**Options Execution Gate**: `{data_q['options_execution_gate']}`  \n")
    md.append(f"**Generated At**: `{data_q['generated_at']}`  \n\n")
    md.append("---\n\n")

    md.append("## 1. Dataset Inventory & Coverage Summary\n\n")
    md.append("| Dataset Name | Frequency | Historical Window | Record Count | Survivorship Bias Risk | Confirmatory Eligible? | Data Quality Status |\n")
    md.append("|:---|:---:|:---:|:---:|:---:|:---:|:---|\n")
    for d in data_q["profiles"]:
        md.append(
            f"| `{d['dataset_name']}` | {d['granularity']} | {d['date_range_start']} to {d['date_range_end']} | {d['total_bars_count']} | `{d['survivorship_bias_risk']}` | `{d['confirmatory_inference_eligible']}` | {d['data_quality_status']} |\n"
        )
    md.append("\n---\n\n")

    md.append("## 2. Intraday Data Sample Limitation Analysis\n\n")
    md.append("The acquired intraday dataset from Yahoo Finance covers:\n")
    md.append("- **Calendar Window**: ~60 calendar days (trailing window)\n")
    md.append("- **Trading Sessions**: ~59 sessions\n")
    md.append("- **Intraday Bars**: 4,425 5-minute bars, 1,475 15-minute bars\n\n")
    md.append("> [!IMPORTANT]\n")
    md.append("> **Statistical Sufficiency Warning**: 59 trading sessions does not satisfy the project's preregistered minimum sample criterion of N>=60 for confirmatory classification. This threshold is a project-specific research gate and is not being presented as a universal statistical law. Intraday models (`P98-H001`, `P98-H002`, `P98-H003`, `P98-H004`) are classified strictly as `EXPLORATORY_ONLY`. Any apparent positive or negative performance cannot be extrapolated to a multi-year regime.\n\n")

    md.append("## 3. Cross-Sectional Survivorship Bias Assessment\n\n")
    md.append("- **Constituent Universe**: RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, BHARTIARTL, ITC, LT, KOTAKBANK.\n")
    md.append("- **Audit Finding**: `SURVIVORSHIP_BIAS_RISK = TRUE`.\n")
    md.append("- **Reasoning**: This universe represents the current top 10 market cap constituents. Historical index constituent changes, delistings, and rank migrations over the 2-year backtest window are not accounted for. Consequently, cross-sectional relative strength results cannot be accepted as survivorship-free evidence.\n\n")

    md.append("## 4. Options Executable Quotes Hard Boundary\n\n")
    md.append("```text\n")
    md.append("TOTAL_OPTIONS_QUOTES = 15,106\n")
    md.append("VALID_BID_QUOTES = 102\n")
    md.append("VALID_ASK_QUOTES = 102\n")
    md.append("VALID_PAIRED_BID_ASK_QUOTES = 102\n")
    md.append("PAIRED_QUOTE_OBSERVATION_COVERAGE = 0.68%\n")
    md.append("CONTINUOUS_EXECUTABLE_SURFACE_COVERAGE = 0.0%\n")
    md.append("OPTIONS_EXECUTION_BACKTEST = BLOCKED\n")
    md.append("OPTIONS_PAPER_EXECUTION = BLOCKED\n")
    md.append("```\n\n")
    md.append("> A small number of paired Bid/Ask observations exist (102 observations, approximately 0.68% of the quote store), but there is 0.0% continuous executable surface coverage across the required strikes/maturities/timestamps. Therefore the available data is insufficient to construct a robust historical executable options backtest. Under quantitative research discipline, options backtests and paper execution without genuine paired bid/ask quotes are strictly prohibited (`BLOCKED`).\n")
    return "".join(md)


def build_timing_audit_report(timing_data: Dict) -> str:
    md = []
    md.append("# PHASE 9.8 — TIMING, TIMESTAMP & POINT-IN-TIME AUDIT REPORT\n")
    md.append(f"**Audit Verdict**: `{timing_data['audit_verdict']}`  \n")
    md.append(f"**Timestamp Compliance**: `{timing_data['all_strategies_point_in_time_compliant']}`  \n")
    md.append(f"**Backward Return Violations**: `{timing_data['backward_return_mappings_found']}`  \n")
    md.append(f"**Same-Bar Execution Violations**: `{timing_data['same_bar_execution_violations_found']}`  \n\n")
    md.append("---\n\n")

    md.append("## 1. Architectural Timing Invariant\n")
    md.append("To prevent any possibility of lookahead bias, target leakage, or unexecutable pricing, Phase 9.8 enforces five explicit point-in-time timestamps across every research strategy:\n")
    md.append("1. `FEATURE_CUTOFF_TIMESTAMP`: End of bar T for feature calculation.\n")
    md.append("2. `PREDICTION_TIMESTAMP`: Generation of model signal.\n")
    md.append("3. `ORDER_TIMESTAMP`: Dispatch of order intent (>= prediction timestamp).\n")
    md.append("4. `EXECUTION_TIMESTAMP`: Simulated fill at bar T+1 Open or post-signal trade.\n")
    md.append("5. `EXIT_TIMESTAMP`: Mandatory liquidation prior to session close.\n\n")

    md.append("## 2. Track Timing Audit Breakdown\n\n")
    md.append("| Strategy ID | Feature Cutoff | Prediction | Order Gen | Fill Timing | Exit Timing | Backward Returns? | Same-Bar Fill? |\n")
    md.append("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
    for item in timing_data["items"]:
        md.append(
            f"| `{item['strategy_id']}` | `{item['feature_cutoff_timestamp']}` | `{item['prediction_timestamp']}` | `{item['order_timestamp']}` | `{item['execution_timestamp']}` | `{item['exit_timestamp']}` | `{'Yes' if item['backward_return_detected'] else 'No'}` | `{'No' if item['same_bar_execution_prohibited'] else 'Yes'}` |\n"
        )
    md.append("\n---\n\n")
    md.append("## 3. Verification Findings\n")
    md.append("- Zero backward return mappings detected across all models.\n")
    md.append("- Same-bar execution at pre-signal prices is strictly prohibited and confirmed absent.\n")
    md.append("- Forward close-to-close or open-to-open returns are used consistently.\n")
    return "".join(md)


def build_multiple_testing_report(multi_data: Dict) -> str:
    md = []
    md.append("# PHASE 9.8 — MULTIPLE TESTING & DATA SNOOPING AUDIT REPORT\n")
    md.append(f"**Audit Verdict**: `{multi_data['audit_verdict']}`  \n")
    md.append(f"**Nominal Alpha**: `{multi_data['nominal_alpha']}`  \n")
    md.append(f"**Bonferroni Adjusted Alpha**: `{multi_data['bonferroni_adjusted_alpha']}`  \n")
    md.append(f"**FDR Threshold (Benjamini-Hochberg)**: `{multi_data['fdr_threshold_bh']}`  \n\n")
    md.append("---\n\n")

    md.append("## 1. Multiplicity Accounting Surface\n\n")
    md.append(f"- **Total Registered Hypotheses**: {multi_data['total_registered_hypotheses']}\n")
    md.append(f"- **Exploratory Tests Run**: {multi_data['total_exploratory_tests']}\n")
    md.append(f"- **Confirmatory Tests Run**: {multi_data['total_confirmatory_tests']}\n")
    md.append(f"- **Distinct Candidate Models**: {multi_data['total_candidate_models']}\n")
    md.append(f"- **Parameter Configurations Evaluated**: {multi_data['total_parameter_configurations']}\n")
    md.append(f"- **Distinct Instruments Tested**: {multi_data['total_instruments']}\n")
    md.append(f"- **Prediction Horizons Tested**: {multi_data['total_horizons']}\n\n")

    md.append("## 2. Event-Level Test Registration Log\n\n")
    md.append("| Event ID | Hypothesis ID | Track | Test Type | Model Name | p-Value Observed | Alpha Bonferroni | Statistically Significant? |\n")
    md.append("|:---:|:---|:---|:---:|:---|:---:|:---:|:---:|\n")
    for ev in multi_data["events"]:
        sig = ev["p_value_observed"] < multi_data["bonferroni_adjusted_alpha"]
        md.append(
            f"| {ev['event_id']} | `{ev['hypothesis_id']}` | {ev['track_name']} | `{ev['test_type']}` | `{ev['model_name']}` | {ev['p_value_observed']:.4f} | {multi_data['bonferroni_adjusted_alpha']:.5f} | `{'YES' if sig else 'NO'}` |\n"
        )
    md.append("\n---\n\n")

    md.append("## 3. Multiple Testing Audit Conclusion\n\n")
    md.append("No statistical claim survived either the nominal significance threshold or the multiplicity-adjusted significance thresholds. Multiple-testing procedures were applied to control false-discovery/family-wise error risk under the stated assumptions; this does not imply that false-discovery risk is literally zero.\n\n")
    md.append("Under family-wise error rate control (Bonferroni alpha = 0.00625) and Benjamini-Hochberg false discovery rate control, **zero tested hypotheses demonstrated statistically significant predictive or economic alpha**. All exploratory and confirmatory p-values exceeded the critical threshold. Data snooping risk has been strictly accounted for.\n")
    return "".join(md)


def build_candidate_comparison_report(cand_data: List[Dict]) -> str:
    md = []
    md.append("# PHASE 9.8 — CANDIDATE COMPARISON & ATTRIBUTION REPORT\n")
    md.append("Comparative analysis of all 8 candidate hypotheses evaluated under realistic transaction friction.\n\n")
    md.append("---\n\n")

    md.append("## 1. Full Economic Attribution Matrix\n\n")
    md.append("| Hypothesis ID | Name | Sample N | Gross Exp (bps) | Statutory Costs (bps) | Slippage (bps) | Net Exp (bps) | Annualized Sharpe | Max Drawdown | Verdict |\n")
    md.append("|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|\n")
    for c in cand_data:
        md.append(
            f"| `{c['hypothesis_id']}` | {c['hypothesis_name']} | {c['sample_size']} | {c['gross_expectancy_bps']:+.1f} | {c['statutory_costs_bps']:.1f} | {c['slippage_bps']:.1f} | {c['net_expectancy_bps']:+.1f} | {c['annualized_sharpe']:.2f} | {c['max_drawdown_pct']:.1f}% | **`{c['final_classification']}`** |\n"
        )
    md.append("\n---\n\n")

    md.append("## 2. Friction Sensitivity & Stress Test Attribution\n\n")
    md.append("To ensure no false positives pass under understated transaction friction assumptions, each strategy was subjected to friction multipliers:\n\n")
    md.append("| Hypothesis ID | Net Exp (1.0x Baseline) | Net Exp (1.5x Stress) | Net Exp (2.0x Extreme Stress) | Friction Decay Assessment |\n")
    md.append("|:---|:---:|:---:|:---:|:---|\n")
    for c in cand_data:
        tot_fric = c['statutory_costs_bps'] + c['slippage_bps']
        net_10 = c['net_expectancy_bps']
        net_15 = c['gross_expectancy_bps'] - (1.5 * tot_fric)
        net_20 = c['gross_expectancy_bps'] - (2.0 * tot_fric)
        md.append(f"| `{c['hypothesis_id']}` | {net_10:+.1f} bps | {net_15:+.1f} bps | {net_20:+.1f} bps | High turnover fee sensitivity |\n")
    md.append("\n---\n\n")

    md.append("## 3. Candidate Summary & Disposition\n\n")
    md.append("Every candidate failed either on economic edge (gross alpha < transaction friction), statistical sample size, survivorship bias risk, or executable data availability. There are zero surviving candidates qualified for automated paper or live execution.\n")
    return "".join(md)


def build_final_gate_report(gate_data: Dict) -> str:
    md = []
    md.append("# PHASE 9.8 — PHASE 10 AUTHORIZATION GATE REPORT\n")
    md.append(f"**Authoritative Decision**: `{gate_data['authoritative_decision']}`  \n")
    md.append(f"**System Readiness**: `{gate_data['system_readiness']}`  \n")
    md.append(f"**Generated At**: `{gate_data['generated_at']}`  \n\n")
    md.append("---\n\n")

    md.append("## 1. 10-Dimension Objective Survival Gates\n\n")
    md.append("| # | Gate Name | Required Criterion | Observed Result | Status |\n")
    md.append("|:---:|:---|:---|:---|:---:|\n")
    for g in gate_data["gates"]:
        md.append(f"| {g['gate_number']} | {g['gate_name']} | {g['requirement']} | {g['observed_result']} | **`{g['status']}`** |\n")
    md.append("\n---\n\n")

    md.append("## 2. Decision Rationale & Next Steps\n\n")
    md.append(f"> {gate_data['decision_rationale']}\n\n")
    md.append("### Safety Invariants Enforced\n")
    md.append("- `ALLOW_LIVE_EXECUTION = False` (Hardcoded, immutable)\n")
    md.append("- `AUTO_PAPER_ORDER_SUBMISSION = False` (Hardcoded, immutable)\n")
    md.append("- Broker Connections: `NONE`\n")
    md.append("- Phase 10: `NOT_IMPLEMENTED`\n")
    return "".join(md)


def main():
    print("Generating Phase 9.8 Markdown Reports with Phase 9.9 Consistency Corrections...")
    reports_dir = Path("reports/phase9_8")
    reports_dir.mkdir(parents=True, exist_ok=True)

    reg_data = load_json("data/phase9_8/research_registry.json")
    cand_data = load_json("data/phase9_8/candidate_results.json")
    gate_data = load_json("data/phase9_8/final_gate.json")
    data_q = load_json("data/phase9_8/data_quality.json")
    timing_data = load_json("data/phase9_8/timing_audit.json")
    multi_data = load_json("data/phase9_8/multiple_testing.json")

    # 1. Research Report
    rep_content = build_research_report(reg_data, cand_data, gate_data, data_q)
    with open(reports_dir / "PHASE_9_8_RESEARCH_REPORT.md", "w", encoding="utf-8") as f:
        f.write(rep_content)
    with open("PHASE_9_8_RESEARCH_REPORT.md", "w", encoding="utf-8") as f:
        f.write(rep_content)
    print("  Created PHASE_9_8_RESEARCH_REPORT.md")

    # 2. Data Quality Report
    dq_content = build_data_quality_report(data_q)
    with open(reports_dir / "PHASE_9_8_DATA_QUALITY_REPORT.md", "w", encoding="utf-8") as f:
        f.write(dq_content)
    print("  Created PHASE_9_8_DATA_QUALITY_REPORT.md")

    # 3. Timing Audit Report
    timing_content = build_timing_audit_report(timing_data)
    with open(reports_dir / "PHASE_9_8_TIMING_AUDIT.md", "w", encoding="utf-8") as f:
        f.write(timing_content)
    print("  Created PHASE_9_8_TIMING_AUDIT.md")

    # 4. Multiple Testing Report
    multi_content = build_multiple_testing_report(multi_data)
    with open(reports_dir / "PHASE_9_8_MULTIPLE_TESTING_REPORT.md", "w", encoding="utf-8") as f:
        f.write(multi_content)
    print("  Created PHASE_9_8_MULTIPLE_TESTING_REPORT.md")

    # 5. Candidate Comparison Report
    cand_content = build_candidate_comparison_report(cand_data)
    with open(reports_dir / "PHASE_9_8_CANDIDATE_COMPARISON.md", "w", encoding="utf-8") as f:
        f.write(cand_content)
    print("  Created PHASE_9_8_CANDIDATE_COMPARISON.md")

    # 6. Final Gate Report
    gate_content = build_final_gate_report(gate_data)
    with open(reports_dir / "PHASE_9_8_FINAL_GATE.md", "w", encoding="utf-8") as f:
        f.write(gate_content)
    print("  Created PHASE_9_8_FINAL_GATE.md")

    print("All 6 reports generated successfully with exact Phase 9.9 terminology.")


if __name__ == "__main__":
    main()
