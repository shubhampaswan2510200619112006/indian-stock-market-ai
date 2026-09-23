"""
Phase 14 Report Generator.

Generates the 8 canonical Markdown reports for Phase 14:
1. PHASE14_FINAL_REPORT.md
2. FULL_DATASET_CERTIFICATION_REPORT.md
3. INTRADAY_CERTIFICATION_REPORT.md
4. OPTIONS_CERTIFICATION_REPORT.md
5. DATA_QUALITY_REPORT.md
6. PROVENANCE_AND_LICENSE_REPORT.md
7. RESEARCH_READINESS_REPORT.md
8. DATASET_FAILURE_DIAGNOSTICS.md

Every report includes standard traceable metadata headers and machine-readable data.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.research.phase14.baseline_verifier import BaselineVerificationResult
from src.research.phase14.certifier import DatasetCertificationResult
from src.research.phase14.readiness_engine import ResearchReadinessReport


class Phase14ReportGenerator:
    """
    Generates all auditable Markdown reports for Phase 14.
    """

    @classmethod
    def generate_all(
        cls,
        workspace_root: str,
        cert_results: List[DatasetCertificationResult],
        readiness_report: ResearchReadinessReport,
        scorecards: List[Dict[str, Any]],
        baseline_result: BaselineVerificationResult,
        overall_status: str,
    ) -> None:
        reports_dir = os.path.join(workspace_root, "reports", "phase14")
        os.makedirs(reports_dir, exist_ok=True)

        now_str = datetime.now(timezone.utc).isoformat()

        # 1. PHASE14_FINAL_REPORT.md
        final_rep_path = os.path.join(reports_dir, "PHASE14_FINAL_REPORT.md")
        with open(final_rep_path, "w", encoding="utf-8") as f:
            f.write(f"""# Phase 14 — Final Full Dataset Qualification & Data Certification Report

## 1. Authoritative Summary Block
```text
PHASE_14_STATUS={overall_status}
FULL_DATASET_CERTIFICATION={readiness_report.technical_data_certified}
RESEARCH_READINESS={'PASS' if readiness_report.capability_readiness.get('INTRADAY_RESEARCH_CAPABILITY', {}).state == 'PASS' else 'BLOCKED'}

INTRADAY_1M_READY={readiness_report.aggregate_gates.get('INTRADAY_1M_READY', 'BLOCKED')}
INTRADAY_5M_READY={readiness_report.aggregate_gates.get('INTRADAY_5M_READY', 'BLOCKED')}

OPTIONS_LTP_READY={readiness_report.aggregate_gates.get('OPTIONS_LTP_READY', 'PASS')}
OPTIONS_BID_ASK_READY={readiness_report.aggregate_gates.get('OPTIONS_BID_ASK_READY', 'BLOCKED')}
OPTIONS_EXECUTION_READY={readiness_report.aggregate_gates.get('OPTIONS_EXECUTION_READY', 'BLOCKED')}

PURCHASE_AUTHORIZED=FALSE
BROKER=NONE
LIVE_EXECUTION=DISABLED
AUTO_PAPER_ORDER_SUBMISSION=DISABLED
NEW_UNPREREGISTERED_ALPHA_RESEARCH=DISABLED
AUTOMATED_VENDOR_CONTACT=DISABLED
AUTOMATED_DATA_PURCHASE=DISABLED

FROZEN_BASELINES={'INTACT' if baseline_result.all_baselines_intact else 'FAILED'}
PHASE_15_UNLOCKED=FALSE
```

## 2. Core Operational Metrics
- **Assessment Timestamp**: `{now_str}`
- **Datasets Evaluated**: `{len(cert_results)}`
- **Certified Datasets**: `{sum(1 for c in cert_results if c.is_certified)}`
- **Quarantined Datasets**: `{sum(1 for c in cert_results if c.is_quarantined)}`
- **Project Full Market Data Ready**: `{readiness_report.project_full_market_data_ready}`
- **Technical Data Certified**: `{readiness_report.technical_data_certified}`

## 3. Capability-Scoped Readiness Summary
- **INTRADAY_RESEARCH_CAPABILITY**: `{readiness_report.capability_readiness.get('INTRADAY_RESEARCH_CAPABILITY', {}).state.value}`
- **OPTIONS_EXECUTION_RESEARCH_CAPABILITY**: `{readiness_report.capability_readiness.get('OPTIONS_EXECUTION_RESEARCH_CAPABILITY', {}).state.value}`
- **EQUITY_CROSS_SECTIONAL_RESEARCH_CAPABILITY**: `{readiness_report.capability_readiness.get('EQUITY_CROSS_SECTIONAL_RESEARCH_CAPABILITY', {}).state.value}`

## 4. Current State & Next Steps
The platform operates safely in dormant waiting mode because no commercial vendor archive has been acquired yet. All safety invariants remain locked. No broker connectivity or alpha discovery has occurred.
""")

        # 2. FULL_DATASET_CERTIFICATION_REPORT.md
        cert_rep_path = os.path.join(reports_dir, "FULL_DATASET_CERTIFICATION_REPORT.md")
        with open(cert_rep_path, "w", encoding="utf-8") as f:
            f.write(f"""# Full Dataset Certification Report

## Metadata Header
```text
VALIDATION_VERSION=cert_v1
CALENDAR_VERSION=nse_cal_v1
SCHEMA_VERSION=phase14_v1
CERTIFICATION_TIMESTAMP={now_str}
```

## Evaluated Datasets
""")
            for c in cert_results:
                f.write(f"""
### Dataset: `{c.dataset_id}` ({c.version_id})
- **Vendor**: `{c.vendor}`
- **Underlying / Interval**: `{c.underlying}` `{c.interval}`
- **Certified**: `{c.is_certified}`
- **License Status**: `{c.license_status}`
- **Provenance Status**: `{c.provenance_status}`
- **Stages Passed**: `{', '.join(c.stages_passed)}`
- **Stages Failed**: `{', '.join(c.stages_failed) if c.stages_failed else 'NONE'}`
- **Rejection Reasons**: `{'; '.join(c.rejection_reasons) if c.rejection_reasons else 'NONE'}`
""")

        # 3. INTRADAY_CERTIFICATION_REPORT.md
        intra_rep_path = os.path.join(reports_dir, "INTRADAY_CERTIFICATION_REPORT.md")
        with open(intra_rep_path, "w", encoding="utf-8") as f:
            f.write(f"""# Intraday Certification Report

## Metadata Header
```text
CALENDAR_VERSION=nse_cal_v1
MIN_VALID_SESSIONS_THRESHOLD=250
SESSION_TIMING=09:15-15:30 IST (375 minutes derived)
CERTIFICATION_TIMESTAMP={now_str}
```

## Evaluated Intraday Datasets
""")
            for c in cert_results:
                if c.intraday_metrics:
                    im = c.intraday_metrics
                    f.write(f"""
### `{c.dataset_id}` ({c.underlying} {c.interval})
- **Total Records**: `{im.total_records}`
- **Expected Bars / Session**: `{im.expected_bars_per_session}` (Derived from canonical session: 375m / {c.interval})
- **Total Sessions Observed**: `{im.total_sessions_observed}`
- **Valid Trading Sessions**: `{im.valid_trading_sessions}` (Requires >= 250)
- **Sessions Threshold Met**: `{im.sessions_threshold_met}`
- **OHLC Violations Count**: `{im.ohlc_violations_count}`
- **Total Missing Bars**: `{im.total_missing_bars}`
- **Session Completeness Status**: `{'PASS' if '7. SESSION COMPLETENESS' in c.stages_passed else 'FAIL'}`
""")

        # 4. OPTIONS_CERTIFICATION_REPORT.md
        opt_rep_path = os.path.join(reports_dir, "OPTIONS_CERTIFICATION_REPORT.md")
        with open(opt_rep_path, "w", encoding="utf-8") as f:
            f.write(f"""# Options Certification Report

## Metadata Header
```text
CONTINUOUS_EXECUTABLE_SURFACE_THRESHOLD=70.0%
STALE_QUOTE_POLICY=NOT_INVENTED (STALE_QUOTE_NOT_ASSESSED unless authoritative threshold provided)
CERTIFICATION_TIMESTAMP={now_str}
```

## Evaluated Options Datasets
""")
            for c in cert_results:
                if c.options_metrics:
                    om = c.options_metrics
                    f.write(f"""
### `{c.dataset_id}` ({c.underlying} {c.interval})
- **Total Option Records**: `{om.total_option_records}`
- **Paired Bid/Ask Quotes**: `{om.paired_bid_ask_records}` ({om.paired_quote_coverage_pct}%)
- **Crossed Market Observations**: `{om.crossed_quotes_count}`
- **Continuous Executable Surface**: `{om.continuous_executable_surface_pct}%` (Target: >= 70.0%)
- **Continuity Threshold Met**: `{om.continuity_threshold_met}`
- **Options Quality Level**: `{om.options_quality_level}`
- **Stale Quote Assessment**: `{om.stale_quote_status}`
- **Depth Verification Level**: `{om.depth_verification_level}`
""")

        # 5. DATA_QUALITY_REPORT.md
        qual_rep_path = os.path.join(reports_dir, "DATA_QUALITY_REPORT.md")
        with open(qual_rep_path, "w", encoding="utf-8") as f:
            f.write(f"""# Data Quality Scorecard Report

## Policy Declaration
```text
DATA_QUALITY_SCORE=DIAGNOSTIC_ONLY
POLICY=Quality scores summarize diagnostics but NEVER override hard certification gates.
CERTIFICATION_TIMESTAMP={now_str}
```

## Scorecards
""")
            for sc in scorecards:
                f.write(f"""
### Dataset: `{sc['dataset_id']}`
- **Diagnostic Score**: `{sc['overall_diagnostic_score']} / 100.0`
- **Hard Gates Intact**: `{sc['hard_gates_intact']}`
- **Certification Eligible by Hard Gates**: `{sc['certification_eligible_by_gates']}`
- **Dimensions Evaluated**:
""")
                for dim in sc.get("dimensions", []):
                    f.write(f"  - **{dim['dimension_name']}**: `{dim['status']}` (Score: {dim['diagnostic_score']}, HardGatePassed: {dim['hard_gate_passed']}) — {dim['details']}\n")

        # 6. PROVENANCE_AND_LICENSE_REPORT.md
        prov_rep_path = os.path.join(reports_dir, "PROVENANCE_AND_LICENSE_REPORT.md")
        with open(prov_rep_path, "w", encoding="utf-8") as f:
            f.write(f"""# Provenance and License Report

## Metadata Header
```text
PROVENANCE_POLICY=Cryptographic SHA256 content verification
LICENSE_POLICY=Explicit permission verification (Unknown -> BLOCKED)
CERTIFICATION_TIMESTAMP={now_str}
```

## Registry Status
""")
            for c in cert_results:
                f.write(f"""
### `{c.dataset_id}` ({c.version_id})
- **Vendor**: `{c.vendor}`
- **Provenance Status**: `{c.provenance_status}`
- **License Status**: `{c.license_status}`
- **Research Permission**: `{'GRANTED' if c.license_status in ['LICENSE_VERIFIED', 'COMMERCIAL_RESEARCH'] else 'BLOCKED'}`
""")

        # 7. RESEARCH_READINESS_REPORT.md
        rr_rep_path = os.path.join(reports_dir, "RESEARCH_READINESS_REPORT.md")
        with open(rr_rep_path, "w", encoding="utf-8") as f:
            f.write(f"""# Research Readiness Report

## Metadata Header
```text
POLICY=TECHNICAL_DATA_CERTIFIED != RESEARCH_UNLOCKED
CERTIFICATION_TIMESTAMP={now_str}
PHASE_15_UNLOCKED=FALSE
```

## Capability-Scoped Readiness Gates
""")
            for name, cap in readiness_report.capability_readiness.items():
                f.write(f"""
### Capability: `{name}`
- **Readiness State**: `{cap.state.value}`
- **Required Gates**: `{', '.join(cap.required_gates)}`
- **Passed Gates**: `{', '.join(cap.passed_gates) if cap.passed_gates else 'NONE'}`
- **Missing Gates**: `{', '.join(cap.missing_gates) if cap.missing_gates else 'NONE'}`
- **Research Unlocked**: `{cap.research_unlocked}`
- **Details**: {cap.details}
""")
            f.write("\n## Blocking Reasons\n")
            for b in readiness_report.blocking_reasons:
                f.write(f"- {b}\n")

        # 8. DATASET_FAILURE_DIAGNOSTICS.md
        diag_rep_path = os.path.join(reports_dir, "DATASET_FAILURE_DIAGNOSTICS.md")
        with open(diag_rep_path, "w", encoding="utf-8") as f:
            f.write(f"""# Dataset Failure Diagnostics Report

## Metadata Header
```text
DIAGNOSTICS_POLICY=Machine-readable deterministic failure codes
CERTIFICATION_TIMESTAMP={now_str}
```

## Diagnostics by Dataset
""")
            for c in cert_results:
                f.write(f"""
### Dataset: `{c.dataset_id}`
- **Certified**: `{c.is_certified}`
- **Quarantined**: `{c.is_quarantined}` ({c.quarantine_reason if c.is_quarantined else 'N/A'})
- **Failure Codes**: `{', '.join(c.failure_codes) if c.failure_codes else 'NONE'}`
- **Rejection Reasons**:
""")
                if c.rejection_reasons:
                    for r in c.rejection_reasons:
                        f.write(f"  - `{r}`\n")
                else:
                    f.write("  - None (All hard gates passed)\n")
