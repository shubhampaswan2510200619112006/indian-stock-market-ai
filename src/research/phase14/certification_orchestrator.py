"""
Phase 14 Certification Orchestrator.

Coordinates upstream Phase 13 evidence ingestion, dormant waiting state management,
dataset qualification, quality scorecard generation, dynamic capability readiness,
and publication of all 9 JSON artifacts and 8 Markdown reports.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd

from src.research.phase14.safety_policy import SafetyPolicy
from src.research.phase14.baseline_verifier import Phase14BaselineVerifier
from src.research.phase14.certification_state import CertificationState, CertificationStateMachine
from src.research.phase14.versioning import DatasetVersionRegistry
from src.research.phase14.certifier import Phase14DataCertifier, DatasetCertificationResult
from src.research.phase14.scorecard import Phase14QualityScorecard
from src.research.phase14.readiness_engine import Phase14ReadinessEngine, ResearchReadinessReport
from src.research.phase14.reports import Phase14ReportGenerator


class Phase14Orchestrator:
    """
    Main orchestration engine for Phase 14 Certification and Research Readiness.
    """

    @classmethod
    def run(cls, workspace_root: str = ".") -> Dict[str, Any]:
        SafetyPolicy.assert_safety_invariants(context="Phase14Orchestrator.run:start")

        # 1. Baseline Verification (Non-destructive)
        baseline_res = Phase14BaselineVerifier.verify(workspace_root=workspace_root)
        if not baseline_res.all_baselines_intact:
            return {
                "status": "ABORTED",
                "reason": "BASELINE_INTEGRITY_FAILED",
                "baseline_verification": baseline_res.to_dict(),
            }

        data_dir = os.path.join(workspace_root, "data", "phase14")
        reports_dir = os.path.join(workspace_root, "reports", "phase14")
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)

        # 2. Ingest upstream Phase 13 artifacts
        p13_registry_path = os.path.join(workspace_root, "data", "phase13", "phase13_dataset_registry.json")
        upstream_datasets = {}
        if os.path.exists(p13_registry_path):
            try:
                with open(p13_registry_path, "r", encoding="utf-8") as f:
                    upstream_datasets = json.load(f).get("datasets", {})
            except Exception:
                upstream_datasets = {}

        # 3. Initialize Version Registry and State Machine
        version_registry = DatasetVersionRegistry()
        sm = CertificationStateMachine(initial_state=CertificationState.WAITING_FOR_VENDOR_DATA)

        # 4. Process and Certify Datasets
        cert_results: List[DatasetCertificationResult] = []
        scorecards: List[Dict[str, Any]] = []

        # Load available datasets from Phase 13 registry
        # A. Yahoo 1m sample
        p10a_1m_path = os.path.join(workspace_root, "data", "phase10a", "intraday", "nsei_1m.csv")
        df_1m = None
        if os.path.exists(p10a_1m_path):
            try:
                df_1m = pd.read_csv(p10a_1m_path)
            except Exception:
                df_1m = None

        v_rec_1m = version_registry.register_version(
            dataset_id="YAHOO_PUBLIC_NIFTY_1M_SAMPLE",
            sha256="sha256_public_sample_1m",
            source=p10a_1m_path,
            vendor="Yahoo Finance",
            license_record="LICENSE_RESTRICTED",
        )
        cert_1m = Phase14DataCertifier.certify_dataset(
            df=df_1m,
            dataset_id="YAHOO_PUBLIC_NIFTY_1M_SAMPLE",
            version_id=v_rec_1m.version_id,
            underlying="NIFTY",
            interval="1m",
            vendor="Yahoo Finance",
            source_file=p10a_1m_path,
            dataset_type="INTRADAY_1M",
            license_status="LICENSE_RESTRICTED",
        )
        cert_results.append(cert_1m)
        scorecards.append(Phase14QualityScorecard.evaluate(cert_1m).to_dict())

        # B. Yahoo 5m sample
        p10a_5m_path = os.path.join(workspace_root, "data", "phase10a", "intraday", "nsei_5m.csv")
        df_5m = None
        if os.path.exists(p10a_5m_path):
            try:
                df_5m = pd.read_csv(p10a_5m_path)
            except Exception:
                df_5m = None

        v_rec_5m = version_registry.register_version(
            dataset_id="YAHOO_PUBLIC_NIFTY_5M_SAMPLE",
            sha256="sha256_public_sample_5m",
            source=p10a_5m_path,
            vendor="Yahoo Finance",
            license_record="LICENSE_RESTRICTED",
        )
        cert_5m = Phase14DataCertifier.certify_dataset(
            df=df_5m,
            dataset_id="YAHOO_PUBLIC_NIFTY_5M_SAMPLE",
            version_id=v_rec_5m.version_id,
            underlying="NIFTY",
            interval="5m",
            vendor="Yahoo Finance",
            source_file=p10a_5m_path,
            dataset_type="INTRADAY_5M",
            license_status="LICENSE_RESTRICTED",
            df_1m_reference=df_1m,
        )
        cert_results.append(cert_5m)
        scorecards.append(Phase14QualityScorecard.evaluate(cert_5m).to_dict())

        # C. NSE Options Bhavcopy Sample (sqlite)
        options_db_path = os.path.join(workspace_root, "data", "indian_options.db")
        df_opt = None
        if os.path.exists(options_db_path):
            try:
                import sqlite3
                conn = sqlite3.connect(options_db_path)
                query = """
                    SELECT q.timestamp, c.underlying, c.expiry_date as expiry,
                           c.strike_price as strike, c.option_type, MAX(q.last_price) as close,
                           MAX(q.bid_price) as bid, MAX(q.ask_price) as ask
                    FROM options_quotes q
                    JOIN options_contracts c ON q.contract_id = c.id
                    WHERE q.timestamp IS NOT NULL
                    GROUP BY q.timestamp, c.underlying, c.expiry_date, c.strike_price, c.option_type
                    LIMIT 1000
                """
                df_opt = pd.read_sql_query(query, conn)
                conn.close()
            except Exception:
                df_opt = None

        v_rec_opt = version_registry.register_version(
            dataset_id="NSE_BHAVCOPY_OPTIONS_LTP_SAMPLE",
            sha256="sha256_bhavcopy_db",
            source=options_db_path,
            vendor="NSE Public Web",
            license_record="LICENSE_VERIFIED",
        )
        cert_opt = Phase14DataCertifier.certify_dataset(
            df=df_opt,
            dataset_id="NSE_BHAVCOPY_OPTIONS_LTP_SAMPLE",
            version_id=v_rec_opt.version_id,
            underlying="NIFTY",
            interval="eod",
            vendor="NSE Public Web",
            source_file=options_db_path,
            dataset_type="OPTIONS_QUOTES",
            license_status="LICENSE_VERIFIED",
        )
        cert_results.append(cert_opt)
        scorecards.append(Phase14QualityScorecard.evaluate(cert_opt).to_dict())

        # 5. Evaluate Readiness Engine
        readiness_report = Phase14ReadinessEngine.evaluate(cert_results)

        # 6. Check whether genuine production vendor data exists
        # In current repo, all datasets are samples/auxiliary; no commercial vendor archive purchased
        has_genuine_prod_data = False
        overall_status = "WAITING_FOR_VENDOR_DATA" if not has_genuine_prod_data else "CERTIFICATION_COMPLETE"

        # 7. Write 9 Canonical JSON Artifacts in data/phase14/
        # Artifact 1: phase14_dataset_certification.json
        with open(os.path.join(data_dir, "phase14_dataset_certification.json"), "w", encoding="utf-8") as f:
            json.dump({
                "certification_timestamp": datetime.now(timezone.utc).isoformat(),
                "phase_14_status": overall_status,
                "total_datasets_evaluated": len(cert_results),
                "total_certified": sum(1 for c in cert_results if c.is_certified),
                "certifications": [c.to_dict() for c in cert_results],
            }, f, indent=2)

        # Artifact 2: phase14_dataset_versions.json
        with open(os.path.join(data_dir, "phase14_dataset_versions.json"), "w", encoding="utf-8") as f:
            json.dump(version_registry.to_dict(), f, indent=2)

        # Artifact 3: phase14_validation_results.json
        with open(os.path.join(data_dir, "phase14_validation_results.json"), "w", encoding="utf-8") as f:
            json.dump({
                "validation_run_timestamp": datetime.now(timezone.utc).isoformat(),
                "results": [
                    {
                        "dataset_id": c.dataset_id,
                        "stages_passed": c.stages_passed,
                        "stages_failed": c.stages_failed,
                        "failure_codes": c.failure_codes,
                        "rejection_reasons": c.rejection_reasons,
                    }
                    for c in cert_results
                ],
            }, f, indent=2)

        # Artifact 4: phase14_quality_metrics.json
        with open(os.path.join(data_dir, "phase14_quality_metrics.json"), "w", encoding="utf-8") as f:
            json.dump({
                "scorecard_policy": "DIAGNOSTIC_ONLY",
                "scorecards": scorecards,
            }, f, indent=2)

        # Artifact 5: phase14_options_certification.json
        with open(os.path.join(data_dir, "phase14_options_certification.json"), "w", encoding="utf-8") as f:
            json.dump({
                "options_certification_results": [
                    {
                        "dataset_id": c.dataset_id,
                        "metrics": c.options_metrics.to_dict() if c.options_metrics else None,
                    }
                    for c in cert_results if c.options_metrics is not None
                ],
            }, f, indent=2)

        # Artifact 6: phase14_readiness.json
        with open(os.path.join(data_dir, "phase14_readiness.json"), "w", encoding="utf-8") as f:
            json.dump(readiness_report.to_dict(), f, indent=2)

        # Artifact 7: phase14_provenance.json
        with open(os.path.join(data_dir, "phase14_provenance.json"), "w", encoding="utf-8") as f:
            json.dump({
                "provenance_records": [
                    {
                        "dataset_id": c.dataset_id,
                        "version_id": c.version_id,
                        "vendor": c.vendor,
                        "source_file": c.certification_run_id,
                        "provenance_status": c.provenance_status,
                    }
                    for c in cert_results
                ],
            }, f, indent=2)

        # Artifact 8: phase14_license_status.json
        with open(os.path.join(data_dir, "phase14_license_status.json"), "w", encoding="utf-8") as f:
            json.dump({
                "license_records": [
                    {
                        "dataset_id": c.dataset_id,
                        "vendor": c.vendor,
                        "license_status": c.license_status,
                        "research_permission": (c.license_status in ["LICENSE_VERIFIED", "COMMERCIAL_RESEARCH"]),
                    }
                    for c in cert_results
                ],
            }, f, indent=2)

        # Artifact 9: phase14_certification_state.json
        with open(os.path.join(data_dir, "phase14_certification_state.json"), "w", encoding="utf-8") as f:
            json.dump(sm.to_dict(), f, indent=2)

        # 8. Generate 8 Markdown Reports
        Phase14ReportGenerator.generate_all(
            workspace_root=workspace_root,
            cert_results=cert_results,
            readiness_report=readiness_report,
            scorecards=scorecards,
            baseline_result=baseline_res,
            overall_status=overall_status,
        )

        SafetyPolicy.assert_safety_invariants(context="Phase14Orchestrator.run:end")

        return {
            "status": "COMPLETE",
            "phase_14_status": overall_status,
            "readiness": readiness_report.to_dict(),
            "baseline_verification": baseline_res.to_dict(),
        }


if __name__ == "__main__":
    out = Phase14Orchestrator.run()
    print(json.dumps(out, indent=2))
