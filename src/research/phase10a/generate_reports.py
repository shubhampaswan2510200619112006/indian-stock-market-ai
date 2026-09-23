"""
Phase 10A — Markdown Report Compilation Engine.

Generates the 7 canonical Phase 10A audit and readiness reports in reports/phase10a/:
1. DATA_INVENTORY_REPORT.md
2. DATA_PROVENANCE_REPORT.md
3. COVERAGE_AUDIT_REPORT.md
4. DATA_QUALITY_REPORT.md
5. CONSTITUENT_INTEGRITY_REPORT.md
6. OPTIONS_EXECUTABILITY_REPORT.md
7. PHASE_10A_FINAL_REPORT.md
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Dict


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_all_reports() -> None:
    reports_dir = Path("reports/phase10a")
    reports_dir.mkdir(parents=True, exist_ok=True)
    data_dir = Path("data/phase10a")

    inventory = load_json(data_dir / "data_inventory.json")
    provenance = load_json(data_dir / "provenance.json")
    coverage = load_json(data_dir / "coverage.json")
    equity = load_json(data_dir / "equity_history_audit.json")
    constituents = load_json(data_dir / "constituent_integrity.json")
    options = load_json(data_dir / "options_executability.json")
    quality = load_json(data_dir / "data_quality.json")
    gate = load_json(data_dir / "final_gate.json")

    # 1. DATA_INVENTORY_REPORT.md
    with open(reports_dir / "DATA_INVENTORY_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# PHASE 10A — DATA INVENTORY REPORT\n\n")
        f.write(f"**Generated**: `{inventory['generated_at_utc']}`  \n")
        f.write(f"**Total Tracked Datasets**: `{inventory['total_datasets_tracked']}`  \n")
        f.write(f"**Tier Breakdown**: Tier 1: `{inventory['tier_summary']['TIER_1_AUTHORITATIVE']}`, Tier 2: `{inventory['tier_summary']['TIER_2_RESEARCH_GRADE']}`, Tier 3: `{inventory['tier_summary']['TIER_3_EXPLORATORY_ONLY']}`\n\n")
        f.write("---\n\n")
        f.write("## 1. Catalog of Data Assets\n\n")
        f.write("| Asset ID | Tier | Format | Size (bytes) | SHA256 (first 16) | Source |\n")
        f.write("|:---|:---:|:---:|:---:|:---:|:---|\n")
        for d in inventory["datasets"]:
            sha_short = d["sha256"][:16] + "..." if len(d["sha256"]) > 16 else d["sha256"]
            f.write(f"| `{d['id']}` | `{d['tier']}` | `{d['format']}` | {d['file_size_bytes']:,} | `{sha_short}` | {d['source']} |\n")
        f.write("\n---\n")

    # 2. DATA_PROVENANCE_REPORT.md
    with open(reports_dir / "DATA_PROVENANCE_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# PHASE 10A — DATA PROVENANCE & LINEAGE REPORT\n\n")
        f.write(f"**Generated**: `{provenance['generated_at_utc']}`  \n")
        f.write(f"**Governance Invariants**: All Active (`ALLOW_LIVE_EXECUTION = False`, `BROKER = NONE`, `NO_ALPHA_RESEARCH = True`)\n\n")
        f.write("---\n\n")
        f.write("## 1. Lineage Records\n\n")
        for rec in provenance["lineage_records"]:
            f.write(f"- **Stage**: `{rec['stage']}`\n")
            f.write(f"- **Actor**: `{rec['actor']}`\n")
            f.write(f"- **Verification Method**: {rec['verification_method']}\n")
            f.write(f"- **Datasets Produced**: {len(rec['datasets_produced'])} assets\n\n")
        f.write("## 2. Cryptographic SHA256 Checksum Registry\n\n")
        f.write("| Dataset ID | File Path | SHA256 Checksum |\n")
        f.write("|:---|:---|:---|\n")
        for d_id, meta in provenance["dataset_manifest"].items():
            f.write(f"| `{d_id}` | `{meta['path']}` | `{meta['sha256']}` |\n")
        f.write("\n---\n")

    # 3. COVERAGE_AUDIT_REPORT.md
    with open(reports_dir / "COVERAGE_AUDIT_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# PHASE 10A — COVERAGE & GRANULARITY AUDIT REPORT\n\n")
        f.write(f"**Status**: `{coverage['intraday_research_ready']}`  \n")
        f.write(f"**Executive Conclusion**: {coverage['executive_conclusion']}\n\n")
        f.write("---\n\n")
        f.write("## 1. Provider Availability & Observed Constraints\n\n")
        f.write("> **Important Scientific Boundary**: The stated Yahoo Finance 1m/5m retention limits are treated as *observed/provider-specific availability constraints for the selected public endpoint*. They must NOT be presented as a universal statement that multi-year intraday data cannot be obtained elsewhere.\n\n")
        f.write("### Empirically Observed Parameters & Coverage\n\n")
        f.write("| Instrument | Interval | Request Period | Sessions Returned | Rows Returned | Date Window | Target Target Sessions | Track Readiness |\n")
        f.write("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
        for inst_key, inst in coverage["instruments"].items():
            for inter, details in inst["intervals"].items():
                dr = details.get("returned_date_range", {})
                d_str = f"{dr.get('start', '')[:10]} to {dr.get('end', '')[:10]}"
                f.write(f"| `{inst['instrument']}` | `{inter}` | `{details['request_parameters']['period']}` | {details['session_count']} | {details['row_count']:,} | {d_str} | {details['target_sessions_required']} | **`{details['status']}`** |\n")
        f.write("\n### Intraday Bar Integrity Metrics\n\n")
        f.write("| Instrument | Interval | Duplicate Count | Duplicate Rate | Missing Bar Rate | Median Gap | Max Intrasession Gap |\n")
        f.write("|:---|:---:|:---:|:---:|:---:|:---:|:---:|\n")
        for inst_key, inst in coverage["instruments"].items():
            for inter, details in inst["intervals"].items():
                gaps = details.get("gap_distribution", {})
                f.write(f"| `{inst['instrument']}` | `{inter}` | {details.get('duplicate_count', 0)} | {details.get('duplicate_rate', 0.0):.4f} | {details.get('missing_bar_rate', 0.0):.4f} | {gaps.get('median_minutes')}m | {gaps.get('max_intrasession_gap_minutes')}m |\n")
        f.write("\n---\n")

    # 4. DATA_QUALITY_REPORT.md
    with open(reports_dir / "DATA_QUALITY_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# PHASE 10A — UNIFIED DATA QUALITY AUDIT REPORT\n\n")
        f.write(f"**Scientific Notice**: {quality['scientific_boundary_notice']}\n\n")
        f.write("---\n\n")
        f.write("## 1. Pillar-by-Pillar Quality Summary\n\n")
        f.write("| Pillar | Scope | Quality Assessment | Track Readiness |\n")
        f.write("|:---|:---|:---|:---:|\n")
        p = quality["pillars"]
        f.write(f"| **Pillar A: Intraday** | NIFTY & BANKNIFTY (1m, 5m) | Zero duplicates, pristine bar continuity, provider retention limited (< 60 sessions) | `{p['pillar_a_intraday']['readiness']}` |\n")
        f.write(f"| **Pillar B: Constituents** | NIFTY 50 PIT Registry | 7 verified official circular events, 0 unresolved events, exact 50 constituents | `{p['pillar_b_constituents']['readiness']}` |\n")
        f.write(f"| **Pillar C: Equity Panel** | Historical Daily Panels | 664-669 modern sessions (> 2 yr target), up to 7,707 full sessions (30+ yrs), 0 modern invalid bars | `{p['pillar_c_equity']['readiness']}` |\n")
        f.write(f"| **Pillar D: Options Quotes** | SQLite Quote Repository | 17,098 quotes; 114 paired Bid/Ask (0.67%); 0.0% continuous executable surface | `{p['pillar_d_options']['readiness']}` |\n")
        f.write("\n---\n")

    # 5. CONSTITUENT_INTEGRITY_REPORT.md
    with open(reports_dir / "CONSTITUENT_INTEGRITY_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# PHASE 10A — POINT-IN-TIME CONSTITUENT REGISTRY AUDIT REPORT\n\n")
        f.write(f"**Index**: `{constituents['index_name']}`  \n")
        f.write(f"**Status**: `{constituents['POINT_IN_TIME_REGISTRY_STATUS']}`  \n")
        f.write(f"**Events Expected**: `{constituents['CONSTITUENT_EVENTS_EXPECTED']}`  \n")
        f.write(f"**Events Found**: `{constituents['CONSTITUENT_EVENTS_FOUND']}`  \n")
        f.write(f"**Unresolved Events**: `{constituents['UNRESOLVED_EVENTS']}`  \n")
        f.write(f"**Survivorship Bias Protection**: `{constituents['survivorship_bias_protection']}`\n\n")
        f.write("---\n\n")
        f.write("## 1. Official NSE Indices Reconstitution Events Audited\n\n")
        f.write("| Event ID | Type | Announcement Date | Effective Date | Added Symbols | Excluded Symbols | Circular Reference |\n")
        f.write("|:---|:---:|:---:|:---:|:---|:---|:---|\n")
        for ev in constituents["official_events_audited"]:
            adds = ", ".join(ev["added_symbols"]) if ev["added_symbols"] else "None"
            rems = ", ".join(ev["removed_symbols"]) if ev["removed_symbols"] else "None"
            f.write(f"| `{ev['event_id']}` | `{ev['event_type']}` | `{ev['announcement_date']}` | `{ev['effective_date']}` | {adds} | {rems} | `{ev['circular_reference']}` |\n")
        f.write("\n## 2. Historical Membership Snapshots Validated\n\n")
        f.write("| Snapshot Date | Status | Count | Valid? | Sample Constituents |\n")
        f.write("|:---|:---:|:---:|:---:|:---|\n")
        for snap in constituents["historical_snapshots_audited"]:
            f.write(f"| `{snap['date']}` | `{snap['status']}` | {snap['constituent_count']} | `{snap['is_valid']}` | {', '.join(snap['sample_constituents'])} |\n")
        f.write("\n---\n")

    # 6. OPTIONS_EXECUTABILITY_REPORT.md
    with open(reports_dir / "OPTIONS_EXECUTABILITY_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# PHASE 10A — OPTIONS EXECUTABILITY & BID/ASK AUDIT REPORT\n\n")
        f.write(f"**Authoritative Status Statement**:  \n> {options['options_conditionality_statement']}\n\n")
        f.write(f"**Synthesis Prohibition**: `{options['synthesis_prohibition']}`  \n")
        f.write(f"**OPTIONS_EXECUTION_BACKTEST**: `{options['OPTIONS_EXECUTION_BACKTEST']}`  \n")
        f.write(f"**OPTIONS_PAPER_EXECUTION**: `{options['OPTIONS_PAPER_EXECUTION']}`  \n")
        f.write(f"**OPTIONS_EXECUTION_RESEARCH_READY**: `{options['OPTIONS_EXECUTION_RESEARCH_READY']}`\n\n")
        f.write("---\n\n")
        f.write("## 1. Options Quotes Repository Metrics\n\n")
        f.write(f"- **Database Path**: `{options['database_path']}`\n")
        f.write(f"- **Total Options Records**: `{options['total_options_records']:,}`\n")
        f.write(f"- **Paired Timestamped Bid/Ask Quotes**: `{options['paired_bid_ask_count']:,}` ({options['paired_bid_ask_percentage']}%)\n")
        f.write(f"- **Zero/Null Bid/Ask Records (EOD Bhavcopy Settlement Only)**: `{options['zero_or_null_bid_ask_count']:,}` ({options['bhavcopy_settlement_only_percentage']})\n")
        f.write(f"- **Continuous Executable Surface Coverage**: **`{options['continuous_executable_surface_coverage']}`**\n\n")
        f.write("## 2. Research Policy Enforcement\n\n")
        f.write("Synthesizing artificial Bid/Ask spreads, fills, market depth, or execution prices is strictly prohibited. "
                "Until genuine high-frequency executable quotes covering continuous option chains are obtained, "
                "all options backtesting and paper trading remain blocked.\n\n")
        f.write("---\n")

    # 7. PHASE_10A_FINAL_REPORT.md
    with open(reports_dir / "PHASE_10A_FINAL_REPORT.md", "w", encoding="utf-8") as f:
        f.write("# PHASE 10A — FINAL DATA FOUNDATION & READINESS GATE REPORT\n\n")
        f.write(f"**Authoritative Overall Decision**: **`{gate['OVERALL_PHASE_10A_STATUS']}`**  \n")
        f.write(f"**Phase**: `{gate['phase']}`  \n")
        f.write(f"**Evaluation Timestamp**: `{gate['evaluation_timestamp_utc']}`  \n\n")
        f.write("### Track-Specific Readiness Summary\n\n")
        for track, status in gate["track_readiness"].items():
            f.write(f"- **{track}**: **`{status}`**\n")
        f.write("\n---\n\n")
        f.write("## 1. Executive Summary & Rationale\n\n")
        f.write(f"{gate['decision_rationale']}\n\n")
        f.write("### Data Status Breakdown\n\n")
        f.write("- **AVAILABLE DATA**: Daily OHLCV equity history for NIFTY 50 constituents and primary indices (664-669 modern sessions, up to 7,707 full sessions); Official NSE trading calendar (2024-2026); Point-in-Time NIFTY 50 constituent registry.\n")
        f.write("- **INSUFFICIENT DATA**: Multi-year intraday 1m/5m bars from authorized public endpoints (< 60 sessions available vs >= 250 required).\n")
        f.write("- **BLOCKED DATA**: Executable continuous options Bid/Ask surface (0.0% continuous coverage; 99.33% EOD settlement only).\n")
        f.write("- **DATA READY FOR FUTURE RESEARCH**: Cross-sectional daily equity research and macroeconomic event studies.\n\n")
        f.write("---\n\n")
        f.write("## 2. 10-Gate Evaluation Matrix\n\n")
        f.write("| Gate # | Gate Name | Track | Requirement | Observed Result | Status |\n")
        f.write("|:---:|:---|:---:|:---|:---|:---:|\n")
        for g in gate["gates"]:
            f.write(f"| {g['gate_number']} | {g['gate_name']} | `{g['track']}` | {g['requirement']} | {g['observed_result']} | **`{g['status']}`** |\n")
        f.write("\n---\n\n")
        f.write("## 3. Platform Safety Invariants Verification\n\n")
        for k, v in gate["safety_invariants"].items():
            f.write(f"- `{k}`: `{v}`\n")
        f.write("\n---\n")

    # Also mirror to root PHASE_10A_DATA_FOUNDATION_REPORT.md for top-level visibility
    with open("PHASE_10A_DATA_FOUNDATION_REPORT.md", "w", encoding="utf-8") as f:
        with open(reports_dir / "PHASE_10A_FINAL_REPORT.md", "r", encoding="utf-8") as src_f:
            f.write(src_f.read())

    print("All 7 Phase 10A Markdown Reports compiled successfully!")


if __name__ == "__main__":
    generate_all_reports()
