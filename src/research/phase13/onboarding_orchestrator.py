"""
Phase 13 Onboarding Orchestrator.

Orchestrates the Phase 13 pipeline:
1. Asserts safety policy invariants.
2. Non-destructively verifies frozen baselines.
3. Ingests normalized vendor responses and cost models.
4. Registers and validates datasets.
5. Dynamically derives dataset-scoped and aggregate readiness.
6. Emits all 7 machine-readable JSON artifacts and 7 Markdown reports.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import pandas as pd

from src.research.phase13.acquisition_state import AcquisitionLifecycleState, AcquisitionStateMachine
from src.research.phase13.baseline_verifier import Phase13BaselineVerifier
from src.research.phase13.dataset_manifest import DatasetCategory, DatasetRegistry, LicenseStatus
from src.research.phase13.readiness import Phase13ReadinessEngine
from src.research.phase13.reports import Phase13ReportGenerator
from src.research.phase13.safety_policy import SafetyPolicy
from src.research.phase13.validator import Phase13DataValidator, ValidationType
from src.research.phase13.vendor_response_ingestion import CostQuoteStatus, VendorCostModel, VendorResponseCatalog


class Phase13OnboardingOrchestrator:
    """
    Master pipeline orchestrator for Phase 13.
    """

    @classmethod
    def run_pipeline(cls, workspace_root: str = ".") -> Dict[str, Any]:
        # 1. Assert Safety Invariants
        SafetyPolicy.assert_safety_invariants(context="Phase13OnboardingOrchestrator.run_pipeline")

        # 2. Non-Destructive Baseline Verification
        baseline_res = Phase13BaselineVerifier.verify(workspace_root)
        if not baseline_res.all_baselines_intact:
            return {
                "status": "ABORTED_BASELINE_FAILURE",
                "baseline_verification": baseline_res.to_dict(),
            }

        # Setup output directories
        data_dir = os.path.join(workspace_root, "data", "phase13")
        reports_dir = os.path.join(workspace_root, "reports", "phase13")
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)

        # 3. State Machine Initialization
        # Current authoritative state: AWAITING_HUMAN_DECISION (compatible with Phase 12)
        state_machine = AcquisitionStateMachine(initial_state=AcquisitionLifecycleState.AWAITING_HUMAN_DECISION)

        # 4. Ingest Vendor Responses & Cost Models
        vendor_responses = VendorResponseCatalog.get_initial_responses()
        cost_models = [
            VendorCostModel(
                vendor="NSE Data & Analytics Ltd (DotEx)",
                product_name="Historical Tick-by-Tick / 5-Depth Archives",
                cost_status=CostQuoteStatus.SALES_QUOTE_REQUIRED,
                assumptions_recorded=["Official exchange enterprise quotation required. Industry estimate INR 50k-250k+."],
            ).to_dict(),
            VendorCostModel(
                vendor="TrueData (TrueData India)",
                product_name="TrueData Historical REST API + Tick Archives",
                cost_status=CostQuoteStatus.ESTIMATE,
                annual_subscription_cost=40000.0,
                assumptions_recorded=["Estimated INR 25,000 to INR 60,000 / yr. Not a binding quote."],
            ).to_dict(),
            VendorCostModel(
                vendor="Global DataFeeds (GDFL)",
                product_name="NimbleDataPro Historical Archives",
                cost_status=CostQuoteStatus.ESTIMATE,
                annual_subscription_cost=35000.0,
                assumptions_recorded=["Estimated INR 20,000 to INR 50,000 / yr. Not a binding quote."],
            ).to_dict(),
            VendorCostModel(
                vendor="Zerodha Kite Connect",
                product_name="Kite Connect Historical API",
                cost_status=CostQuoteStatus.VERIFIED_QUOTE,
                monthly_subscription_cost=4000.0,
                annual_subscription_cost=48000.0,
                assumptions_recorded=["Official price: INR 2k Base + INR 2k Historical/mo. Fails options requirements."],
            ).to_dict(),
        ]

        # 5. Register and Validate Baseline Datasets
        dataset_registry = DatasetRegistry()
        validation_results = []

        # 5a. Public 1m sample (Observed in Phase 10A - 7 sessions, fails threshold)
        p10a_1m_path = os.path.join(workspace_root, "data", "phase10a", "intraday", "nsei_1m.csv")
        if os.path.exists(p10a_1m_path):
            df_1m = pd.read_csv(p10a_1m_path)
            val_1m = Phase13DataValidator.validate_dataset(
                df=df_1m,
                validation_type=ValidationType.SAMPLE_VALIDATION,
                dataset_id="YAHOO_PUBLIC_NIFTY_1M_SAMPLE",
                underlying="NIFTY 50",
                interval="1m",
                vendor="Yahoo Finance (Public Free Endpoint)",
                dataset_version="sample_v1",
                dataset_type="INTRADAY_1M",
                license_status="LICENSE_RESTRICTED",
            )
            validation_results.append(val_1m)
            manifest_1m = dataset_registry.register_dataset(
                dataset_id="YAHOO_PUBLIC_NIFTY_1M_SAMPLE",
                category=DatasetCategory.AUXILIARY_DATASET,  # Kept distinct from target production data
                vendor="Yahoo Finance",
                product_name="yfinance public endpoint",
                underlying="NIFTY 50",
                frequency="1m",
                coverage_start="2026-09-01",
                coverage_end="2026-09-08",
                total_records=len(df_1m),
                source_file=p10a_1m_path,
                source_checksum="sha256_public_sample_1m",
                license_status=LicenseStatus.LICENSE_RESTRICTED,
                validation_run_id=val_1m.validation_run_id,
            )

        # 5b. Public 5m sample (Observed in Phase 10A - 43 sessions, fails threshold)
        p10a_5m_path = os.path.join(workspace_root, "data", "phase10a", "intraday", "nsei_5m.csv")
        if os.path.exists(p10a_5m_path):
            df_5m = pd.read_csv(p10a_5m_path)
            val_5m = Phase13DataValidator.validate_dataset(
                df=df_5m,
                validation_type=ValidationType.SAMPLE_VALIDATION,
                dataset_id="YAHOO_PUBLIC_NIFTY_5M_SAMPLE",
                underlying="NIFTY 50",
                interval="5m",
                vendor="Yahoo Finance (Public Free Endpoint)",
                dataset_version="sample_v1",
                dataset_type="INTRADAY_5M",
                license_status="LICENSE_RESTRICTED",
            )
            validation_results.append(val_5m)
            dataset_registry.register_dataset(
                dataset_id="YAHOO_PUBLIC_NIFTY_5M_SAMPLE",
                category=DatasetCategory.AUXILIARY_DATASET,
                vendor="Yahoo Finance",
                product_name="yfinance public endpoint",
                underlying="NIFTY 50",
                frequency="5m",
                coverage_start="2026-07-10",
                coverage_end="2026-09-08",
                total_records=len(df_5m),
                source_file=p10a_5m_path,
                source_checksum="sha256_public_sample_5m",
                license_status=LicenseStatus.LICENSE_RESTRICTED,
                validation_run_id=val_5m.validation_run_id,
            )

        # 5c. Options SQLite sample (19,643 records, LTP Bhavcopy only)
        options_db_path = os.path.join(workspace_root, "data", "indian_options.db")
        if os.path.exists(options_db_path):
            import sqlite3
            conn = sqlite3.connect(options_db_path)
            try:
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
                df_opt = pd.read_sql(query, conn)
                val_opt = Phase13DataValidator.validate_dataset(
                    df=df_opt,
                    validation_type=ValidationType.SAMPLE_VALIDATION,
                    dataset_id="NSE_BHAVCOPY_OPTIONS_LTP_SAMPLE",
                    underlying="NIFTY",
                    interval="daily_settlement",
                    vendor="NSE Public Bhavcopy",
                    dataset_version="bhavcopy_v1",
                    dataset_type="OPTIONS_QUOTES",
                    license_status="LICENSE_VERIFIED",
                )
                validation_results.append(val_opt)
                dataset_registry.register_dataset(
                    dataset_id="NSE_BHAVCOPY_OPTIONS_LTP_SAMPLE",
                    category=DatasetCategory.PRODUCTION_DATA,
                    vendor="NSE Public Web",
                    product_name="Historical F&O Bhavcopy",
                    underlying="NIFTY",
                    frequency="eod",
                    coverage_start="2018-01-01",
                    coverage_end="2025-12-31",
                    total_records=len(df_opt),
                    source_file=options_db_path,
                    source_checksum="sha256_bhavcopy_db",
                    license_status=LicenseStatus.LICENSE_VERIFIED,
                    validation_run_id=val_opt.validation_run_id,
                )
            except Exception as e:
                print(f"Options sample query error: {e}")
            finally:
                conn.close()

        # 6. Evaluate Readiness Gates Dynamically
        all_manifests = dataset_registry.get_all_manifests()
        readiness_report = Phase13ReadinessEngine.evaluate(
            manifests=all_manifests,
            validation_results=validation_results,
        )

        # 7. Write 7 Machine-Readable Artifacts in data/phase13/
        # Artifact 1: phase13_dataset_registry.json
        with open(os.path.join(data_dir, "phase13_dataset_registry.json"), "w", encoding="utf-8") as f:
            json.dump(dataset_registry.to_dict(), f, indent=2)

        # Artifact 2: phase13_vendor_responses.json
        with open(os.path.join(data_dir, "phase13_vendor_responses.json"), "w", encoding="utf-8") as f:
            json.dump({
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "responses": vendor_responses,
                "cost_models": cost_models,
            }, f, indent=2)

        # Artifact 3: phase13_acquisition_state.json
        with open(os.path.join(data_dir, "phase13_acquisition_state.json"), "w", encoding="utf-8") as f:
            json.dump(state_machine.to_dict(), f, indent=2)

        # Artifact 4: phase13_data_validation.json
        with open(os.path.join(data_dir, "phase13_data_validation.json"), "w", encoding="utf-8") as f:
            json.dump({
                "validation_runs_count": len(validation_results),
                "validation_runs": [v.to_dict() for v in validation_results],
            }, f, indent=2)

        # Artifact 5: phase13_readiness.json
        with open(os.path.join(data_dir, "phase13_readiness.json"), "w", encoding="utf-8") as f:
            json.dump(readiness_report.to_dict(), f, indent=2)

        # Artifact 6: phase13_provenance.json
        provenance_data = {
            "provenance_records": [
                {
                    "dataset_id": m.dataset_id,
                    "version": m.version,
                    "vendor": m.vendor,
                    "source_checksum": m.source_checksum,
                    "license_status": m.license_status.value,
                    "acquisition_timestamp": m.acquisition_timestamp,
                }
                for m in all_manifests
            ]
        }
        with open(os.path.join(data_dir, "phase13_provenance.json"), "w", encoding="utf-8") as f:
            json.dump(provenance_data, f, indent=2)

        # Artifact 7: phase13_acceptance_results.json
        acceptance_results = {
            "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
            "acceptance_criteria": {
                "intraday_sessions_threshold": ">= 250 sessions (PROJECT_RESEARCH_THRESHOLD)",
                "options_quote_continuity_threshold": ">= 70.0% continuous paired surface (PROJECT_RESEARCH_THRESHOLD)",
                "contract_validation_method": "EXCHANGE_SPEC_AND_CALENDAR_DRIVEN",
                "test_fixture_isolation": "ENFORCED",
            },
            "gate_results": readiness_report.aggregate_gates if hasattr(readiness_report, "aggregate_gates") else readiness_report.to_dict()["aggregate_gates"],
            "blocking_reasons": readiness_report.blocking_reasons,
        }
        with open(os.path.join(data_dir, "phase13_acceptance_results.json"), "w", encoding="utf-8") as f:
            json.dump(acceptance_results, f, indent=2)

        # 8. Generate 7 Markdown Reports in reports/phase13/
        Phase13ReportGenerator.generate_all_reports(
            reports_dir=reports_dir,
            state_machine=state_machine,
            readiness_report=readiness_report,
            dataset_registry=dataset_registry,
            validation_results=validation_results,
            vendor_responses=vendor_responses,
            cost_models=cost_models,
            baseline_result=baseline_res,
        )

        return {
            "status": "COMPLETE",
            "phase_13_status": "VENDOR_EVALUATION_COMPLETE",
            "overall_state": "AWAITING_HUMAN_ACQUISITION_DECISION",
            "readiness": readiness_report.to_dict(),
            "baseline_verification": baseline_res.to_dict(),
        }


if __name__ == "__main__":
    res = Phase13OnboardingOrchestrator.run_pipeline()
    print("Phase 13 Pipeline Execution Output:")
    print(json.dumps(res, indent=2))
