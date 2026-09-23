"""
Phase 14 Certification Architecture and Governance Tests.
"""

import json
import os
import pytest
import pandas as pd

from src.research.phase14.safety_policy import SafetyPolicy, SafetyViolationError
from src.research.phase14.baseline_verifier import Phase14BaselineVerifier
from src.research.phase14.certification_state import CertificationState, CertificationStateMachine, IllegalStateTransitionError
from src.research.phase14.fixture_quarantine import FixtureQuarantineManager
from src.research.phase14.versioning import DatasetVersionRegistry
from src.research.phase14.certifier import Phase14DataCertifier, StaleQuoteStatus
from src.research.phase14.scorecard import Phase14QualityScorecard
from src.research.phase14.readiness_engine import Phase14ReadinessEngine, GateState


def test_safety_policy_immutability():
    """Verify read-only safety accessors enforce exact safety constants."""
    assert SafetyPolicy.get_broker() == "NONE"
    assert SafetyPolicy.get_live_execution() == "DISABLED"
    assert SafetyPolicy.get_auto_paper_order_submission() == "DISABLED"
    assert SafetyPolicy.get_options_execution() == "BLOCKED"
    assert SafetyPolicy.get_new_alpha_research() == "DISABLED"
    assert SafetyPolicy.get_automated_vendor_contact() == "DISABLED"
    assert SafetyPolicy.get_automated_data_purchase() == "DISABLED"
    assert SafetyPolicy.get_purchase_authorized() is False
    assert SafetyPolicy.get_human_decision_required() is True
    assert SafetyPolicy.get_phase_15_unlocked() is False

    # Assert raises no error in valid state
    SafetyPolicy.assert_safety_invariants("test")


def test_baseline_verifier_all_phases_intact():
    """Verify non-destructive baseline verification across Phases 9.7 through 13."""
    res = Phase14BaselineVerifier.verify()
    assert res.all_baselines_intact is True
    assert res.status_decision == "ALL_BASELINES_INTACT"
    assert res.phase_9_7_baseline == "FROZEN"
    assert res.phase_9_8_research_results == "FROZEN"
    assert res.phase_9_9_freeze_manifest == "FROZEN_IMMUTABLE"
    assert res.phase_10a_artifacts_status == "INTACT"
    assert res.phase_10b_artifacts_status == "INTACT"
    assert res.phase_10c_artifacts_status == "INTACT"
    assert res.phase_11_artifacts_status == "INTACT"
    assert res.phase_12_artifacts_status == "INTACT"
    assert res.phase_13_artifacts_status == "INTACT"
    assert len(res.errors) == 0


def test_fixture_quarantine_manager():
    """Verify quarantine manager detects mock/fixture indicators across fields and paths."""
    # Direct indicator in ID
    is_q, reason = FixtureQuarantineManager.check_quarantine(
        dataset_id="MOCK_TAPE_1M", source_file="tape.csv"
    )
    assert is_q is True
    assert "CONTAMINATION_VIOLATION" in reason

    # Indicator in source file
    is_q, reason = FixtureQuarantineManager.check_quarantine(
        dataset_id="PROD_TAPE_1M", source_file="data/test_csv/tape.csv"
    )
    assert is_q is True

    # Indicator in metadata
    is_q, reason = FixtureQuarantineManager.check_quarantine(
        dataset_id="CLEAN_TAPE", source_file="data/tape.csv", metadata={"is_synthetic": True}
    )
    assert is_q is True
    assert "EXPLICIT_FIXTURE_FLAG" in reason

    # Clean production dataset
    is_q, reason = FixtureQuarantineManager.check_quarantine(
        dataset_id="GENUINE_NIFTY_TAPE", source_file="data/production/nifty.csv"
    )
    assert is_q is False
    assert reason is None


def test_versioning_engine_content_hashes():
    """Verify versioning engine assigns content hashes, detects replacements, and prevents silent overwrite."""
    reg = DatasetVersionRegistry()
    v1 = reg.register_version(
        dataset_id="ARCHIVE_1M",
        sha256="hash_v1",
        source="file_v1.csv",
        vendor="VendorA",
    )
    assert v1.version_id == "v1"

    # Registering same hash returns v1 without duplicate
    v1_dup = reg.register_version(
        dataset_id="ARCHIVE_1M",
        sha256="hash_v1",
        source="file_v1.csv",
        vendor="VendorA",
    )
    assert v1_dup.version_id == "v1"

    # Registering updated content hash produces v2 with v1 as parent
    v2 = reg.register_version(
        dataset_id="ARCHIVE_1M",
        sha256="hash_v2",
        source="file_v2.csv",
        vendor="VendorA",
    )
    assert v2.version_id == "v2"
    assert v2.parent_version == "v1"


def test_canonical_session_bar_count_derivation():
    """Verify expected bars per session are derived dynamically from calendar/session definition."""
    # 09:15 to 15:30 = 375 minutes
    assert Phase14DataCertifier.derive_expected_bars_per_session("1m") == 375
    assert Phase14DataCertifier.derive_expected_bars_per_session("5m") == 75
    assert Phase14DataCertifier.derive_expected_bars_per_session("15m") == 25
    assert Phase14DataCertifier.derive_expected_bars_per_session("eod") == 1


def test_stale_quote_default_not_assessed():
    """Verify stale quote rule is not arbitrarily invented."""
    df_opt = pd.DataFrame({
        "timestamp": ["2026-09-08 09:15:00", "2026-09-08 09:15:01"],
        "bid": [100.0, 100.0],
        "ask": [102.0, 102.0],
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df_opt,
        dataset_id="OPT_STALE_TEST",
        version_id="v1",
        underlying="NIFTY",
        interval="tick",
        vendor="TestVendor",
        source_file="opt.csv",
        dataset_type="OPTIONS_QUOTES",
    )
    assert cert.options_metrics.stale_quote_status == StaleQuoteStatus.NOT_ASSESSED


def test_quality_scorecard_is_diagnostic_only():
    """Verify that high quality scores can NEVER override failed hard certification gates."""
    # Dataset with 10 sessions (fails >= 250 threshold)
    dates = pd.date_range("2025-01-01", periods=10, freq="B")
    dfs = []
    for d in dates:
        st = pd.date_range(f"{d.strftime('%Y-%m-%d')} 09:15:00", periods=75, freq="5min")
        dfs.append(pd.DataFrame({
            "timestamp": st.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "open": 20000.0, "high": 20010.0, "low": 19990.0, "close": 20005.0,
            "volume": 1000,
        }))
    df = pd.concat(dfs, ignore_index=True)

    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="SHORT_DATASET",
        version_id="v1",
        underlying="NIFTY",
        interval="5m",
        vendor="VendorX",
        source_file="short.csv",
        dataset_type="INTRADAY_5M",
        license_status="LICENSE_VERIFIED",
    )
    scorecard = Phase14QualityScorecard.evaluate(cert)

    assert scorecard.scorecard_policy == "DIAGNOSTIC_ONLY"
    assert scorecard.hard_gates_intact is False
    assert scorecard.certification_eligible_by_gates is False
    assert any("INSUFFICIENT_SESSIONS" in b for b in scorecard.blocking_reasons)


def test_all_phase14_artifacts_exist_and_conform():
    """Verify all 9 JSON artifacts and 8 Markdown reports exist in data/phase14 and reports/phase14."""
    data_artifacts = [
        "data/phase14/phase14_dataset_certification.json",
        "data/phase14/phase14_dataset_versions.json",
        "data/phase14/phase14_validation_results.json",
        "data/phase14/phase14_quality_metrics.json",
        "data/phase14/phase14_options_certification.json",
        "data/phase14/phase14_readiness.json",
        "data/phase14/phase14_provenance.json",
        "data/phase14/phase14_license_status.json",
        "data/phase14/phase14_certification_state.json",
    ]
    for p in data_artifacts:
        assert os.path.exists(p), f"Missing data artifact: {p}"
        assert os.path.getsize(p) > 0, f"Empty data artifact: {p}"

    report_artifacts = [
        "reports/phase14/PHASE14_FINAL_REPORT.md",
        "reports/phase14/FULL_DATASET_CERTIFICATION_REPORT.md",
        "reports/phase14/INTRADAY_CERTIFICATION_REPORT.md",
        "reports/phase14/OPTIONS_CERTIFICATION_REPORT.md",
        "reports/phase14/DATA_QUALITY_REPORT.md",
        "reports/phase14/PROVENANCE_AND_LICENSE_REPORT.md",
        "reports/phase14/RESEARCH_READINESS_REPORT.md",
        "reports/phase14/DATASET_FAILURE_DIAGNOSTICS.md",
    ]
    for r in report_artifacts:
        assert os.path.exists(r), f"Missing report artifact: {r}"
        assert os.path.getsize(r) > 0, f"Empty report artifact: {r}"
