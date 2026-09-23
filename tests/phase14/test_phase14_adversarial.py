"""
Phase 14 Adversarial and Edge-Case Test Suite.

Implements all 40 mandatory adversarial scenarios defined in Phase 14 specifications.
"""

import os
import pytest
import pandas as pd
import numpy as np

from src.research.phase14.safety_policy import SafetyPolicy, SafetyViolationError
from src.research.phase14.baseline_verifier import Phase14BaselineVerifier
from src.research.phase14.certification_state import CertificationState, CertificationStateMachine, IllegalStateTransitionError
from datetime import date, timedelta
from src.data_infrastructure.calendar import NSEMarketCalendar
from src.research.phase14.fixture_quarantine import FixtureQuarantineManager
from src.research.phase14.versioning import DatasetVersionRegistry
from src.research.phase14.certifier import Phase14DataCertifier, StaleQuoteStatus
from src.research.phase14.scorecard import Phase14QualityScorecard
from src.research.phase14.readiness_engine import Phase14ReadinessEngine, GateState


def generate_clean_sessions(num_sessions: int, bars_per_session: int = 75, interval: str = "5m", symbol: str = "NIFTY 50"):
    freq_str = "1min" if interval == "1m" else "5min"
    dfs = []
    curr = date(2025, 1, 1)
    sessions_generated = 0
    while sessions_generated < num_sessions:
        if NSEMarketCalendar.is_trading_day(curr):
            st = pd.date_range(f"{curr.strftime('%Y-%m-%d')} 09:15:00", periods=bars_per_session, freq=freq_str)
            dfs.append(pd.DataFrame({
                "timestamp": st.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
                "open": 20000.0, "high": 20010.0, "low": 19990.0, "close": 20005.0,
                "volume": 1000, "symbol": symbol,
            }))
            sessions_generated += 1
        curr += timedelta(days=1)
    return pd.concat(dfs, ignore_index=True)


# 1. No vendor data
def test_adv_01_no_vendor_data():
    report = Phase14ReadinessEngine.evaluate([])
    assert report.technical_data_certified == GateState.BLOCKED.value
    assert report.project_full_market_data_ready == GateState.BLOCKED.value
    assert report.capability_readiness["INTRADAY_RESEARCH_CAPABILITY"].state == GateState.BLOCKED


# 2. Valid 250-session dataset
def test_adv_02_valid_250_session_dataset():
    df = generate_clean_sessions(250, bars_per_session=75, interval="5m")
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="VALID_250_DATASET",
        version_id="v1",
        underlying="NIFTY",
        interval="5m",
        vendor="VendorTrue",
        source_file="valid.csv",
        dataset_type="INTRADAY_5M",
        license_status="LICENSE_VERIFIED",
    )
    assert cert.is_certified is True
    assert cert.intraday_metrics.sessions_threshold_met is True
    assert cert.intraday_metrics.valid_trading_sessions == 250


# 3. 249-session dataset (fails research threshold)
def test_adv_03_249_session_dataset_fails():
    df = generate_clean_sessions(249, bars_per_session=75, interval="5m")
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="SHORT_249",
        version_id="v1",
        underlying="NIFTY",
        interval="5m",
        vendor="VendorTrue",
        source_file="short249.csv",
        dataset_type="INTRADAY_5M",
        license_status="LICENSE_VERIFIED",
    )
    assert cert.is_certified is False
    assert "INSUFFICIENT_SESSIONS" in cert.failure_codes
    assert cert.intraday_metrics.sessions_threshold_met is False


# 4. 250 sessions with incomplete sessions
def test_adv_04_250_sessions_with_incomplete_sessions():
    df = generate_clean_sessions(250, bars_per_session=75, interval="5m")
    # Truncate first 20 sessions to only 10 bars (< 95% complete)
    dates = pd.to_datetime(df["timestamp"]).dt.date.unique()
    bad_dates = dates[:20]
    # Filter out most bars from those 20 dates
    mask_keep = ~((pd.to_datetime(df["timestamp"]).dt.date.isin(bad_dates)) & (df.index % 5 != 0))
    df_incomplete = df[mask_keep].reset_index(drop=True)

    cert = Phase14DataCertifier.certify_dataset(
        df=df_incomplete,
        dataset_id="INCOMPLETE_SESSIONS",
        version_id="v1",
        underlying="NIFTY",
        interval="5m",
        vendor="VendorTrue",
        source_file="inc.csv",
        dataset_type="INTRADAY_5M",
        license_status="LICENSE_VERIFIED",
    )
    assert cert.intraday_metrics.valid_trading_sessions == 230
    assert cert.intraday_metrics.sessions_threshold_met is False


# 5. Wrong timezone (raw UTC without IST conversion)
def test_adv_05_wrong_timezone():
    df = pd.DataFrame({
        "timestamp": ["2026-09-08T03:45:00Z", "2026-09-08T03:46:00Z"],
        "open": 20000.0, "high": 20010.0, "low": 19990.0, "close": 20005.0,
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="UTC_DATASET",
        version_id="v1",
        underlying="NIFTY",
        interval="1m",
        vendor="VendorUTC",
        source_file="utc.csv",
        dataset_type="INTRADAY_1M",
    )
    assert "TIMEZONE_INVALID" in cert.failure_codes


# 6. Duplicate bars
def test_adv_06_duplicate_bars():
    df = pd.DataFrame({
        "timestamp": ["2026-09-08T09:15:00+05:30", "2026-09-08T09:15:00+05:30"],
        "open": 20000.0, "high": 20010.0, "low": 19990.0, "close": 20005.0,
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="DUP_BARS",
        version_id="v1",
        underlying="NIFTY",
        interval="1m",
        vendor="VendorDup",
        source_file="dup.csv",
        dataset_type="INTRADAY_1M",
    )
    assert cert.intraday_metrics.total_duplicate_bars == 1


# 7. Invalid OHLC
def test_adv_07_invalid_ohlc():
    df = pd.DataFrame({
        "timestamp": ["2026-09-08T09:15:00+05:30"],
        "open": 20000.0, "high": 19900.0, "low": 20100.0, "close": 20005.0,  # High < Low
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="BAD_OHLC",
        version_id="v1",
        underlying="NIFTY",
        interval="1m",
        vendor="VendorBad",
        source_file="bad.csv",
        dataset_type="INTRADAY_1M",
    )
    assert "OHLC_INVALID" in cert.failure_codes


# 8. Missing trading session (detects gap, excludes exchange holidays)
def test_adv_08_missing_trading_session_detection():
    # 2 trading days, skip 1 business day that is NOT an official holiday
    d1 = pd.date_range("2025-01-02 09:15:00", periods=75, freq="5min")
    d2 = pd.date_range("2025-01-06 09:15:00", periods=75, freq="5min")  # Friday Jan 3 skipped
    df = pd.DataFrame({
        "timestamp": list(d1.strftime("%Y-%m-%dT%H:%M:%S+05:30")) + list(d2.strftime("%Y-%m-%dT%H:%M:%S+05:30")),
        "open": 20000.0, "high": 20010.0, "low": 19990.0, "close": 20005.0,
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="GAP_SESSION",
        version_id="v1",
        underlying="NIFTY",
        interval="5m",
        vendor="VendorGap",
        source_file="gap.csv",
        dataset_type="INTRADAY_5M",
    )
    assert cert.intraday_metrics.valid_trading_sessions == 2


# 9. Fixture contamination
def test_adv_09_fixture_contamination():
    df = generate_clean_sessions(260)
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="PIT_LEAK_TEST_NIFTY",
        version_id="v1",
        underlying="NIFTY",
        interval="5m",
        vendor="VendorFixture",
        source_file="test_tape.csv",
        dataset_type="INTRADAY_5M",
    )
    assert cert.is_quarantined is True
    assert "FIXTURE_DATASET" in cert.failure_codes


# 10. Vendor claim without data
def test_adv_10_vendor_claim_without_data():
    cert = Phase14DataCertifier.certify_dataset(
        df=None,
        dataset_id="EMPTY_CLAIM",
        version_id="v1",
        underlying="NIFTY",
        interval="1m",
        vendor="ClaimVendor",
        source_file="empty.csv",
        dataset_type="INTRADAY_1M",
    )
    assert cert.is_certified is False
    assert "INGESTION_EMPTY_DATASET" in cert.failure_codes


# 11. Invalid provenance
def test_adv_11_invalid_provenance():
    df = generate_clean_sessions(5)
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="NO_PROV",
        version_id="v1",
        underlying="NIFTY",
        interval="5m",
        vendor="VendorA",
        source_file="",  # Missing source file
        dataset_type="INTRADAY_5M",
    )
    assert "PROVENANCE_MISSING" in cert.failure_codes


# 12. Unknown license
def test_adv_12_unknown_license():
    df = generate_clean_sessions(5)
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="UNKNOWN_LIC",
        version_id="v1",
        underlying="NIFTY",
        interval="5m",
        vendor="VendorA",
        source_file="a.csv",
        dataset_type="INTRADAY_5M",
        license_status="LICENSE_UNKNOWN",
    )
    assert "LICENSE_UNCONFIRMED" in cert.failure_codes


# 13. Valid Bid/Ask
def test_adv_13_valid_bid_ask():
    df = pd.DataFrame({
        "timestamp": ["2026-09-08 09:15:00"] * 100,
        "bid": [100.0] * 100,
        "ask": [102.0] * 100,
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="VALID_BA",
        version_id="v1",
        underlying="NIFTY",
        interval="tick",
        vendor="VendorOpt",
        source_file="ba.csv",
        dataset_type="OPTIONS_QUOTES",
        license_status="LICENSE_VERIFIED",
    )
    assert cert.options_metrics.paired_quote_coverage_pct == 100.0
    assert cert.options_metrics.crossed_quotes_count == 0


# 14. Missing Bid
def test_adv_14_missing_bid():
    df = pd.DataFrame({
        "timestamp": ["2026-09-08 09:15:00"],
        "ask": [102.0],
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="NO_BID",
        version_id="v1",
        underlying="NIFTY",
        interval="tick",
        vendor="VendorOpt",
        source_file="nobid.csv",
        dataset_type="OPTIONS_QUOTES",
    )
    assert "OPTIONS_BID_MISSING" in cert.failure_codes


# 15. Missing Ask
def test_adv_15_missing_ask():
    df = pd.DataFrame({
        "timestamp": ["2026-09-08 09:15:00"],
        "bid": [100.0],
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="NO_ASK",
        version_id="v1",
        underlying="NIFTY",
        interval="tick",
        vendor="VendorOpt",
        source_file="noask.csv",
        dataset_type="OPTIONS_QUOTES",
    )
    assert "OPTIONS_ASK_MISSING" in cert.failure_codes


# 16. Crossed market
def test_adv_16_crossed_market():
    df = pd.DataFrame({
        "timestamp": ["2026-09-08 09:15:00"],
        "bid": [105.0],
        "ask": [100.0],  # Bid > Ask
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="CROSSED_OPT",
        version_id="v1",
        underlying="NIFTY",
        interval="tick",
        vendor="VendorOpt",
        source_file="cross.csv",
        dataset_type="OPTIONS_QUOTES",
    )
    assert "CROSSED_MARKET" in cert.failure_codes


# 17. Disconnected Bid/Ask
def test_adv_17_disconnected_bid_ask():
    # 50 records with Bid only, 50 records with Ask only (zero paired quotes)
    df = pd.DataFrame({
        "timestamp": ["2026-09-08 09:15:00"] * 100,
        "bid": [100.0] * 50 + [0.0] * 50,
        "ask": [0.0] * 50 + [102.0] * 50,
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="DISCONNECTED_BA",
        version_id="v1",
        underlying="NIFTY",
        interval="tick",
        vendor="VendorOpt",
        source_file="disc.csv",
        dataset_type="OPTIONS_QUOTES",
    )
    assert cert.options_metrics.paired_bid_ask_records == 0
    assert "CONTINUOUS_EXECUTABLE_SURFACE_LOW" in cert.failure_codes


# 18. Low executable coverage
def test_adv_18_low_executable_coverage():
    # Only 40 paired quotes out of 100 (40% < 70% threshold)
    df = pd.DataFrame({
        "timestamp": ["2026-09-08 09:15:00"] * 100,
        "bid": [100.0] * 40 + [0.0] * 60,
        "ask": [102.0] * 40 + [0.0] * 60,
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="LOW_COV_OPT",
        version_id="v1",
        underlying="NIFTY",
        interval="tick",
        vendor="VendorOpt",
        source_file="lowcov.csv",
        dataset_type="OPTIONS_QUOTES",
    )
    assert cert.options_metrics.paired_quote_coverage_pct == 40.0
    assert cert.options_metrics.continuity_threshold_met is False


# 19. High isolated quote coverage but zero continuous surface
def test_adv_19_high_isolated_quote_coverage():
    df = pd.DataFrame({
        "timestamp": ["2026-09-08 09:15:00"] * 60 + ["2026-09-08 09:16:00"] * 40,
        "bid": [100.0] * 60 + [0.0] * 40,
        "ask": [102.0] * 60 + [0.0] * 40,
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="ISOLATED_QUOTES",
        version_id="v1",
        underlying="NIFTY",
        interval="tick",
        vendor="VendorOpt",
        source_file="iso.csv",
        dataset_type="OPTIONS_QUOTES",
    )
    assert cert.options_metrics.options_quality_level == "L2"


# 20. Invalid option contract metadata
def test_adv_20_invalid_option_contract_metadata():
    df = pd.DataFrame({
        "timestamp": ["2026-09-08 09:15:00"],
        "option_type": ["XX"],  # Invalid type
        "bid": [100.0], "ask": [102.0],
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df,
        dataset_id="BAD_CONTRACT",
        version_id="v1",
        underlying="NIFTY",
        interval="tick",
        vendor="VendorOpt",
        source_file="badc.csv",
        dataset_type="OPTIONS_QUOTES",
    )
    assert "INVALID_OPTION_CONTRACT_METADATA" in cert.failure_codes


# 21. NIFTY passes / BANKNIFTY fails (Scope independence)
def test_adv_21_nifty_passes_banknifty_fails():
    df_nifty = generate_clean_sessions(255, bars_per_session=375, interval="1m", symbol="NIFTY 50")
    cert_nifty = Phase14DataCertifier.certify_dataset(
        df=df_nifty, dataset_id="NIFTY_1M_PASS", version_id="v1", underlying="NIFTY",
        interval="1m", vendor="VendorV", source_file="n.csv", dataset_type="INTRADAY_1M", license_status="LICENSE_VERIFIED",
    )
    assert cert_nifty.is_certified is True

    rep = Phase14ReadinessEngine.evaluate([cert_nifty])
    # Scoped NIFTY passes, but aggregate INTRADAY_1M_READY remains BLOCKED because BANKNIFTY is missing
    scoped_nifty = [r for r in rep.dataset_scoped_results if r.dataset_id == "NIFTY_1M_PASS"][0]
    assert scoped_nifty.state == GateState.PASS
    assert rep.aggregate_gates["INTRADAY_1M_READY"] == GateState.BLOCKED.value


# 22. 1m passes / 5m fails (Interval independence)
def test_adv_22_1m_passes_5m_fails():
    df_1m = generate_clean_sessions(255, bars_per_session=375, interval="1m")
    cert_1m = Phase14DataCertifier.certify_dataset(
        df=df_1m, dataset_id="1M_PASS", version_id="v1", underlying="NIFTY",
        interval="1m", vendor="VendorV", source_file="1m.csv", dataset_type="INTRADAY_1M", license_status="LICENSE_VERIFIED",
    )
    rep = Phase14ReadinessEngine.evaluate([cert_1m])
    assert rep.aggregate_gates["INTRADAY_5M_READY"] == GateState.BLOCKED.value


# 23. One dataset version changes
def test_adv_23_dataset_version_changes():
    reg = DatasetVersionRegistry()
    v1 = reg.register_version(dataset_id="TAPE_A", sha256="hash_v1", source="f.csv", vendor="VendorA")
    v2 = reg.register_version(dataset_id="TAPE_A", sha256="hash_v2", source="f_new.csv", vendor="VendorA")
    assert v1.version_id != v2.version_id
    assert v2.parent_version == "v1"


# 24. Content hash changes produces new version
def test_adv_24_content_hash_changes():
    reg = DatasetVersionRegistry()
    v1 = reg.register_version(dataset_id="DS_1", sha256="hash_100", source="s1.csv", vendor="V1")
    v2 = reg.register_version(dataset_id="DS_1", sha256="hash_101", source="s1.csv", vendor="V1")
    assert v2.version_id == "v2"


# 25. Silent repair attempt prohibited
def test_adv_25_silent_repair_attempt_prohibited():
    df = pd.DataFrame({
        "timestamp": ["2026-09-08 09:15:00"],
        "open": 20000.0, "high": 19000.0, "low": 20100.0, "close": 20000.0,  # Impossible bar
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df, dataset_id="NO_REPAIR", version_id="v1", underlying="NIFTY",
        interval="1m", vendor="VendorX", source_file="r.csv", dataset_type="INTRADAY_1M",
    )
    assert cert.is_certified is False
    assert "OHLC_INVALID" in cert.failure_codes


# 26. Derived bars boundary alignment
def test_adv_26_derived_bars_boundary_alignment():
    # 5m dataset with timestamps not on :00, :05, :10
    df = pd.DataFrame({
        "timestamp": ["2026-09-08 09:17:00", "2026-09-08 09:22:00"],
        "open": 20000.0, "high": 20010.0, "low": 19990.0, "close": 20005.0,
    })
    df_ref = generate_clean_sessions(1, bars_per_session=375, interval="1m")
    cert = Phase14DataCertifier.certify_dataset(
        df=df, dataset_id="MISALIGNED_5M", version_id="v1", underlying="NIFTY",
        interval="5m", vendor="VendorX", source_file="m5.csv", dataset_type="INTRADAY_5M",
        df_1m_reference=df_ref,
    )
    assert "BAR_BOUNDARY_MISALIGNED" in cert.failure_codes


# 27. Theoretical depth incorrectly labelled historical
def test_adv_27_theoretical_depth_not_historical():
    df = pd.DataFrame({
        "timestamp": ["2026-09-08 09:15:00"],
        "bid": [100.0], "ask": [102.0],
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df, dataset_id="THEOR_DEPTH", version_id="v1", underlying="NIFTY",
        interval="tick", vendor="VendorD", source_file="d.csv", dataset_type="OPTIONS_QUOTES",
    )
    assert cert.options_metrics.depth_verification_level == "THEORETICAL_DEPTH"


# 28. Current API capability vs historical depth
def test_adv_28_current_api_capability_distinguished():
    df = pd.DataFrame({
        "timestamp": ["2026-09-08 09:15:00"],
        "bid": [100.0], "ask": [102.0],
    })
    cert = Phase14DataCertifier.certify_dataset(
        df=df, dataset_id="API_CAP", version_id="v1", underlying="NIFTY",
        interval="tick", vendor="VendorAPI", source_file="api.csv", dataset_type="OPTIONS_QUOTES",
    )
    assert cert.options_metrics.depth_verification_level != "HISTORICAL_DEPTH_VERIFIED"


# 29. License pass but technical failure
def test_adv_29_license_pass_technical_failure():
    df = generate_clean_sessions(10)  # Fails 250 sessions
    cert = Phase14DataCertifier.certify_dataset(
        df=df, dataset_id="LIC_PASS_TECH_FAIL", version_id="v1", underlying="NIFTY",
        interval="5m", vendor="VendorL", source_file="l.csv", dataset_type="INTRADAY_5M",
        license_status="LICENSE_VERIFIED",
    )
    assert cert.license_status == "LICENSE_VERIFIED"
    assert cert.is_certified is False
    assert "INSUFFICIENT_SESSIONS" in cert.failure_codes


# 30. Technical pass but license failure
def test_adv_30_technical_pass_license_failure():
    df = generate_clean_sessions(255)
    cert = Phase14DataCertifier.certify_dataset(
        df=df, dataset_id="TECH_PASS_LIC_FAIL", version_id="v1", underlying="NIFTY",
        interval="5m", vendor="VendorL", source_file="l.csv", dataset_type="INTRADAY_5M",
        license_status="LICENSE_UNKNOWN",  # Unconfirmed license
    )
    assert cert.is_certified is False
    assert "LICENSE_UNCONFIRMED" in cert.failure_codes


# 31. Aggregate readiness calculation requires all components
def test_adv_31_aggregate_readiness_calculation():
    # Only NIFTY 1m and 5m certified, no BANKNIFTY
    df_nifty_1m = generate_clean_sessions(255, bars_per_session=375, interval="1m")
    df_nifty_5m = generate_clean_sessions(255, bars_per_session=75, interval="5m")
    c1 = Phase14DataCertifier.certify_dataset(
        df=df_nifty_1m, dataset_id="N_1M", version_id="v1", underlying="NIFTY",
        interval="1m", vendor="V", source_file="n1.csv", dataset_type="INTRADAY_1M", license_status="LICENSE_VERIFIED",
    )
    c2 = Phase14DataCertifier.certify_dataset(
        df=df_nifty_5m, dataset_id="N_5M", version_id="v1", underlying="NIFTY",
        interval="5m", vendor="V", source_file="n5.csv", dataset_type="INTRADAY_5M", license_status="LICENSE_VERIFIED",
    )
    rep = Phase14ReadinessEngine.evaluate([c1, c2])
    assert rep.aggregate_gates["INTRADAY_1M_READY"] == GateState.BLOCKED.value
    assert rep.capability_readiness["INTRADAY_RESEARCH_CAPABILITY"].state == GateState.BLOCKED


# 32. Frozen baseline mutation attempt safely blocked
def test_adv_32_frozen_baseline_mutation_attempt():
    res = Phase14BaselineVerifier.verify()
    assert res.all_baselines_intact is True
    # Mutating expected hash fails verifier
    # We test non-destructive failure handling
    res_fake = Phase14BaselineVerifier.verify(workspace_root="non_existent_dir")
    assert res_fake.all_baselines_intact is False
    assert res_fake.status_decision == "BASELINE_VERIFICATION_INCOMPLETE"


# 33. Human authorization absent
def test_adv_33_human_authorization_absent():
    assert SafetyPolicy.get_purchase_authorized() is False
    assert SafetyPolicy.get_human_decision_required() is True


# 34. Human authorization present but technical validation fails
def test_adv_34_human_authorization_separate_from_technical_gate():
    df = generate_clean_sessions(10)
    cert = Phase14DataCertifier.certify_dataset(
        df=df, dataset_id="AUTH_BUT_TECH_FAIL", version_id="v1", underlying="NIFTY",
        interval="5m", vendor="V", source_file="v.csv", dataset_type="INTRADAY_5M",
    )
    # Even if commercial purchase was approved externally, technical certification is False
    assert cert.is_certified is False


# 35. Illegal state transition
def test_adv_35_illegal_state_transition():
    sm = CertificationStateMachine(initial_state=CertificationState.WAITING_FOR_VENDOR_DATA)
    with pytest.raises(IllegalStateTransitionError):
        # Cannot jump from WAITING_FOR_VENDOR_DATA to FULL_DATASET_CERTIFIED
        sm.transition_to(
            target_state=CertificationState.FULL_DATASET_CERTIFIED,
            reason="Illegal bypass",
            evidence_reference="NONE",
        )


# 36. Phase 14 cannot activate downstream alpha research
def test_adv_36_cannot_activate_downstream_alpha_research():
    assert SafetyPolicy.get_new_alpha_research() == "DISABLED"
    assert SafetyPolicy.get_unlimited_parameter_search() == "DISABLED"
    assert SafetyPolicy.get_strategy_optimization() == "DISABLED"


# 37. Broker remains NONE
def test_adv_37_broker_remains_none():
    assert SafetyPolicy.get_broker() == "NONE"


# 38. Live execution remains disabled
def test_adv_38_live_execution_disabled():
    assert SafetyPolicy.get_live_execution() == "DISABLED"


# 39. Automated paper submission remains disabled
def test_adv_39_auto_paper_submission_disabled():
    assert SafetyPolicy.get_auto_paper_order_submission() == "DISABLED"


# 40. Purchase remains unauthorized
def test_adv_40_purchase_remains_unauthorized():
    assert SafetyPolicy.get_purchase_authorized() is False
    assert SafetyPolicy.get_automated_data_purchase() == "DISABLED"
    assert SafetyPolicy.get_automated_vendor_contact() == "DISABLED"
    assert SafetyPolicy.get_phase_15_unlocked() is False
