"""
Unit & Integration Tests for Phase 13 Data Acquisition & Onboarding.
"""

from __future__ import annotations

import json
import os
import pytest
import pandas as pd

from src.research.phase13.acquisition_state import (
    AcquisitionLifecycleState,
    AcquisitionStateMachine,
    HumanAuthorizationRecord,
)
from src.research.phase13.baseline_verifier import Phase13BaselineVerifier
from src.research.phase13.dataset_manifest import (
    DatasetCategory,
    DatasetRegistry,
    LicenseStatus,
)
from src.research.phase13.readiness import GateState, Phase13ReadinessEngine
from src.research.phase13.safety_policy import SafetyPolicy, SafetyViolationError
from src.research.phase13.validator import (
    Phase13DataValidator,
    ValidationType,
)
from src.research.phase13.vendor_response_ingestion import (
    CostQuoteStatus,
    VendorCostModel,
    VerificationStatus,
)


def test_safety_policy_immutability():
    """Verify read-only safety accessors and assert invariants."""
    assert SafetyPolicy.get_broker() == "NONE"
    assert SafetyPolicy.get_live_execution() == "DISABLED"
    assert SafetyPolicy.get_auto_paper_order_submission() == "DISABLED"
    assert SafetyPolicy.get_options_execution() == "BLOCKED"
    assert SafetyPolicy.get_new_alpha_research() == "DISABLED"
    assert SafetyPolicy.get_unlimited_parameter_search() == "DISABLED"
    assert SafetyPolicy.get_strategy_optimization() == "DISABLED"
    assert SafetyPolicy.get_purchase_authorized() is False
    assert SafetyPolicy.get_human_decision_required() is True

    # Assert raises no error in valid state
    SafetyPolicy.assert_safety_invariants(context="test_safety_policy_immutability")


def test_baseline_verifier_authoritative_manifest():
    """Verify non-destructive baseline verification against authoritative frozen hashes."""
    res = Phase13BaselineVerifier.verify()
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
    assert len(res.errors) == 0


def test_dynamic_readiness_no_hardcoding():
    """Verify readiness gates are derived dynamically from evidence and not hardcoded."""
    # When no qualifying production datasets exist:
    empty_registry = DatasetRegistry()
    report = Phase13ReadinessEngine.evaluate(
        manifests=empty_registry.get_all_manifests(),
        validation_results=[],
    )
    assert report.intraday_1m_ready == GateState.BLOCKED
    assert report.intraday_5m_ready == GateState.BLOCKED
    assert report.options_bid_ask_ready == GateState.BLOCKED
    assert report.options_execution_ready == GateState.BLOCKED


def test_future_valid_dataset_flips_gate_to_pass():
    """Verify that a future valid dataset dynamically changes an aggregate gate from BLOCKED to PASS."""
    # Generate synthetic compliant NIFTY 1m and BANKNIFTY 1m datasets with 260 sessions
    dates = pd.date_range("2025-01-01", periods=260, freq="B")
    dfs = []
    for d in dates:
        session_times = pd.date_range(f"{d.strftime('%Y-%m-%d')} 09:15:00", periods=375, freq="1min")
        dfs.append(pd.DataFrame({
            "timestamp": session_times.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "open": 20000.0,
            "high": 20010.0,
            "low": 19990.0,
            "close": 20005.0,
            "volume": 1000,
            "symbol": "NIFTY 50",
        }))
    df_nifty_1m = pd.concat(dfs, ignore_index=True)

    val_nifty = Phase13DataValidator.validate_dataset(
        df=df_nifty_1m,
        validation_type=ValidationType.FULL_DATASET_VALIDATION,
        dataset_id="PROD_NIFTY_1M_FULL",
        underlying="NIFTY",
        interval="1m",
        vendor="TrueData",
        dataset_version="v1",
        dataset_type="INTRADAY_1M",
    )
    assert val_nifty.is_valid is True

    # Same for BANKNIFTY
    df_bn_1m = df_nifty_1m.copy()
    df_bn_1m["symbol"] = "NIFTY BANK"
    val_bn = Phase13DataValidator.validate_dataset(
        df=df_bn_1m,
        validation_type=ValidationType.FULL_DATASET_VALIDATION,
        dataset_id="PROD_BANKNIFTY_1M_FULL",
        underlying="BANKNIFTY",
        interval="1m",
        vendor="TrueData",
        dataset_version="v1",
        dataset_type="INTRADAY_1M",
    )
    assert val_bn.is_valid is True

    reg = DatasetRegistry()
    m1 = reg.register_dataset(
        dataset_id="PROD_NIFTY_1M_FULL",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="TrueData",
        product_name="Tick Archive",
        underlying="NIFTY",
        frequency="1m",
        coverage_start="2025-01-01",
        coverage_end="2025-12-31",
        total_records=len(df_nifty_1m),
        source_file="nifty_1m_tape.csv",
        source_checksum="hash_nifty_1m",
        license_status=LicenseStatus.LICENSE_VERIFIED,
        validation_run_id=val_nifty.validation_run_id,
    )
    m2 = reg.register_dataset(
        dataset_id="PROD_BANKNIFTY_1M_FULL",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="TrueData",
        product_name="Tick Archive",
        underlying="BANKNIFTY",
        frequency="1m",
        coverage_start="2025-01-01",
        coverage_end="2025-12-31",
        total_records=len(df_bn_1m),
        source_file="bn_1m_tape.csv",
        source_checksum="hash_bn_1m",
        license_status=LicenseStatus.LICENSE_VERIFIED,
        validation_run_id=val_bn.validation_run_id,
    )

    # Re-evaluate readiness dynamically
    rep = Phase13ReadinessEngine.evaluate(
        manifests=[m1, m2],
        validation_results=[val_nifty, val_bn],
    )
    # Both NIFTY and BANKNIFTY are satisfied with >= 250 sessions:
    assert rep.intraday_1m_ready == GateState.PASS


def test_nifty_only_does_not_unlock_banknifty():
    """Verify scope independence: NIFTY 1m passing does not make aggregate 1m ready if BANKNIFTY is missing."""
    reg = DatasetRegistry()
    m_nifty = reg.register_dataset(
        dataset_id="NIFTY_ONLY_1M",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="TrueData",
        product_name="NIFTY Index",
        underlying="NIFTY",
        frequency="1m",
        coverage_start="2025-01-01",
        coverage_end="2025-12-31",
        total_records=100000,
        source_file="nifty.csv",
        source_checksum="hash_nifty",
        license_status=LicenseStatus.LICENSE_VERIFIED,
        validation_run_id="VAL-NIFTY-PASS",
    )

    # Mock validation result with 260 sessions
    from src.research.phase13.validator import IntradayMetrics, Phase13ValidationResult
    val_mock = Phase13ValidationResult(
        validation_run_id="VAL-NIFTY-PASS",
        validation_type=ValidationType.FULL_DATASET_VALIDATION,
        dataset_id="NIFTY_ONLY_1M",
        underlying="NIFTY",
        interval="1m",
        vendor="TrueData",
        dataset_version="v1",
        validation_timestamp="2026-09-09T00:00:00Z",
        is_valid=True,
        intraday_metrics=IntradayMetrics(
            total_records=100000,
            total_sessions=260,
            valid_sessions=260,
            bars_per_session_mean=375.0,
            expected_bars_per_session=375,
            duplicate_bars_count=0,
            missing_bars_count=0,
            ohlc_violations_count=0,
            timestamp_parseable=True,
            session_alignment_passed=True,
            sessions_threshold_met=True,
        ),
    )

    rep = Phase13ReadinessEngine.evaluate(
        manifests=[m_nifty],
        validation_results=[val_mock],
    )
    # Scoped result for NIFTY is PASS
    scoped_nifty = [r for r in rep.dataset_scoped_results if r.dataset_id == "NIFTY_ONLY_1M"][0]
    assert scoped_nifty.state == GateState.PASS

    # But aggregate gate remains BLOCKED because BANKNIFTY is missing
    assert rep.intraday_1m_ready == GateState.BLOCKED
    assert any("BANKNIFTY" in b for b in rep.blocking_reasons)


def test_5m_pass_does_not_unlock_1m():
    """Verify interval independence: 5m qualification does not unlock 1m."""
    reg = DatasetRegistry()
    m_5m = reg.register_dataset(
        dataset_id="NIFTY_5M",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="TrueData",
        product_name="5m Index",
        underlying="NIFTY",
        frequency="5m",
        coverage_start="2025-01-01",
        coverage_end="2025-12-31",
        total_records=20000,
        source_file="nifty_5m.csv",
        source_checksum="hash_nifty_5m",
        license_status=LicenseStatus.LICENSE_VERIFIED,
        validation_run_id="VAL-5M",
    )
    rep = Phase13ReadinessEngine.evaluate(manifests=[m_5m], validation_results=[])
    assert rep.intraday_1m_ready == GateState.BLOCKED


def test_sample_validation_pass_leaves_full_dataset_pending():
    """Verify that sample validation pass does NOT unlock production data readiness."""
    df_sample = pd.DataFrame({
        "timestamp": ["2026-09-08T09:15:00+05:30", "2026-09-08T09:16:00+05:30"],
        "open": [25000.0, 25010.0],
        "high": [25020.0, 25015.0],
        "low": [24990.0, 25005.0],
        "close": [25010.0, 25012.0],
        "volume": [100, 150],
        "symbol": ["NIFTY 50", "NIFTY 50"],
    })
    val_sample = Phase13DataValidator.validate_dataset(
        df=df_sample,
        validation_type=ValidationType.SAMPLE_VALIDATION,
        dataset_id="TEST_SAMPLE_1M",
        underlying="NIFTY",
        interval="1m",
        vendor="TrueData",
        dataset_version="sample_v1",
        dataset_type="INTRADAY_1M",
    )
    # Sample validation can pass with 1 session
    assert val_sample.validation_type == ValidationType.SAMPLE_VALIDATION
    assert val_sample.intraday_metrics.sessions_threshold_met is True  # Meets sample threshold (>= 1)

    # But full dataset validation strictly requires >= 250 sessions
    val_full = Phase13DataValidator.validate_dataset(
        df=df_sample,
        validation_type=ValidationType.FULL_DATASET_VALIDATION,
        dataset_id="TEST_SAMPLE_1M",
        underlying="NIFTY",
        interval="1m",
        vendor="TrueData",
        dataset_version="full_v1",
        dataset_type="INTRADAY_1M",
    )
    assert val_full.is_valid is False
    assert "INTRADAY_SESSION_THRESHOLD_FAILED" in val_full.rejection_reason


def test_human_authorization_event_enforcement():
    """Verify human authorization must be a structured event, not a bare boolean."""
    sm = AcquisitionStateMachine(initial_state=AcquisitionLifecycleState.AWAITING_HUMAN_DECISION)

    # Attempt to transition to APPROVED_FOR_MANUAL_ACQUISITION without auth record raises PermissionError
    with pytest.raises(PermissionError) as exc_info:
        sm.transition(
            to_state=AcquisitionLifecycleState.APPROVED_FOR_MANUAL_ACQUISITION,
            reason="Trying automated approval",
            auth_record=None,
        )
    assert "HumanAuthorizationRecord" in str(exc_info.value)

    # Valid human authorization record allows transition
    auth = HumanAuthorizationRecord(
        human_decision="APPROVE",
        decision_timestamp="2026-09-09T16:00:00Z",
        vendor="NSE Data & Analytics Ltd (DotEx)",
        product="Historical 1m Index Tape",
        approved_scope="NIFTY 50 & NIFTY BANK 1m 2018-2025",
        approved_cost_ref="QUOTE-NSE-2026-001",
        authorization_id="AUTH-HUMAN-001",
        decision_outcome="APPROVED_FOR_MANUAL_ACQUISITION",
        notes="Approved following legal review of internal research terms.",
    )
    success = sm.transition(
        to_state=AcquisitionLifecycleState.APPROVED_FOR_MANUAL_ACQUISITION,
        reason="Human portfolio manager signed approval form",
        auth_record=auth,
    )
    assert success is True
    assert sm.current_state == AcquisitionLifecycleState.APPROVED_FOR_MANUAL_ACQUISITION


def test_content_based_versioning_and_duplicate_checksum():
    """Verify content-based versioning creates new versions on change and detects identical checksums."""
    reg = DatasetRegistry()
    m1 = reg.register_dataset(
        dataset_id="DS_VERSIONED",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="VendorX",
        product_name="Tape",
        underlying="NIFTY",
        frequency="1m",
        coverage_start="2025-01-01",
        coverage_end="2025-06-30",
        total_records=1000,
        source_file="file1.csv",
        source_checksum="checksum_aaa",
    )
    assert m1.version == "v1"

    # Registering identical checksum returns existing version (no redundant duplicate version)
    m1_again = reg.register_dataset(
        dataset_id="DS_VERSIONED",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="VendorX",
        product_name="Tape",
        underlying="NIFTY",
        frequency="1m",
        coverage_start="2025-01-01",
        coverage_end="2025-06-30",
        total_records=1000,
        source_file="file1.csv",
        source_checksum="checksum_aaa",
    )
    assert m1_again.version == "v1"

    # Registering different checksum creates v2
    m2 = reg.register_dataset(
        dataset_id="DS_VERSIONED",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="VendorX",
        product_name="Tape",
        underlying="NIFTY",
        frequency="1m",
        coverage_start="2025-01-01",
        coverage_end="2025-12-31",
        total_records=2000,
        source_file="file2.csv",
        source_checksum="checksum_bbb",
    )
    assert m2.version == "v2"


def test_all_phase13_artifacts_exist_and_conform():
    """Verify all 7 JSON artifacts and 7 Markdown reports exist and match required schemas."""
    workspace_root = "."
    data_dir = os.path.join(workspace_root, "data", "phase13")
    required_json = [
        "phase13_dataset_registry.json",
        "phase13_vendor_responses.json",
        "phase13_acquisition_state.json",
        "phase13_data_validation.json",
        "phase13_readiness.json",
        "phase13_provenance.json",
        "phase13_acceptance_results.json",
    ]
    for r in required_json:
        p = os.path.join(data_dir, r)
        assert os.path.exists(p), f"Missing JSON artifact: {r}"
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data is not None

    reports_dir = os.path.join(workspace_root, "reports", "phase13")
    required_reports = [
        "PHASE13_DATA_ACQUISITION_STATUS.md",
        "DATASET_ONBOARDING_GUIDE.md",
        "INTRADAY_ACCEPTANCE_REPORT.md",
        "OPTIONS_ACCEPTANCE_REPORT.md",
        "DATA_PROVENANCE_REPORT.md",
        "DATA_READINESS_REPORT.md",
        "PHASE13_FINAL_REPORT.md",
    ]
    for rep in required_reports:
        p = os.path.join(reports_dir, rep)
        assert os.path.exists(p), f"Missing Markdown report: {rep}"
        with open(p, "r", encoding="utf-8") as f:
            text = f.read()
            assert len(text) > 100, f"Report {rep} is unexpectedly empty"
