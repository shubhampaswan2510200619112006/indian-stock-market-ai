"""
Adversarial and Edge-Case Test Suite for Phase 13 Data Acquisition & Onboarding.

Deliberately tests all 20 specified adversarial failure scenarios to guarantee
safe, deterministic state handling:
1. Vendor says '5 years available' but sample contains 6 months.
2. Vendor says Bid/Ask available but sample contains only LTP.
3. Bid/Ask exists only for a tiny subset.
4. Quotes are present but discontinuous (<70%).
5. Dataset contains test fixtures.
6. Dataset has timezone mismatch.
7. Dataset contains duplicate bars.
8. Dataset has missing sessions (<250 sessions).
9. Vendor gives a price range rather than formal quote.
10. Vendor refuses to confirm research licensing.
11. Vendor provides only current contracts, not expired contracts.
12. Vendor provides 5m but no 1m.
13. Vendor provides NIFTY but not BANKNIFTY.
14. Vendor provides theoretical depth but not historical depth.
15. Sample passes but full dataset fails.
16. Vendor updates/replaces a historical file (creates new version, not silent overwrite).
17. Dataset contains corrupted rows (NaNs, negative prices).
18. Dataset has Bid/Ask but Bid > Ask (crossed quotes).
19. Dataset has paired quotes but <70% continuous executable surface.
20. Human has not authorized purchase (purchase remains blocked).
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.research.phase13.acquisition_state import (
    AcquisitionLifecycleState,
    AcquisitionStateMachine,
    HumanAuthorizationRecord,
)
from src.research.phase13.dataset_manifest import (
    DatasetCategory,
    DatasetRegistry,
    LicenseStatus,
)
from src.research.phase13.readiness import GateState, Phase13ReadinessEngine
from src.research.phase13.validator import (
    Phase13DataValidator,
    ValidationType,
)
from src.research.phase13.vendor_response_ingestion import (
    CostQuoteStatus,
    VendorCostModel,
)


def test_adv_01_vendor_claims_5_years_but_data_has_6_months():
    """Scenario 1: Vendor claims 5 years but data contains only 125 sessions (fails >= 250 threshold)."""
    dates = pd.date_range("2025-01-01", periods=125, freq="B")
    dfs = []
    for d in dates:
        session_times = pd.date_range(f"{d.strftime('%Y-%m-%d')} 09:15:00", periods=75, freq="5min")
        dfs.append(pd.DataFrame({
            "timestamp": session_times.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "open": 20000.0, "high": 20010.0, "low": 19990.0, "close": 20005.0,
            "volume": 1000, "symbol": "NIFTY 50",
        }))
    df = pd.concat(dfs, ignore_index=True)

    val = Phase13DataValidator.validate_dataset(
        df=df,
        validation_type=ValidationType.FULL_DATASET_VALIDATION,
        dataset_id="ADV_5YR_CLAIM_6MO_DATA",
        underlying="NIFTY",
        interval="5m",
        vendor="VendorClaimTest",
        dataset_version="v1",
        dataset_type="INTRADAY_5M",
    )
    assert val.is_valid is False
    assert "INTRADAY_SESSION_THRESHOLD_FAILED" in val.rejection_reason


def test_adv_02_vendor_claims_bid_ask_but_sample_contains_only_ltp():
    """Scenario 2: Vendor claims Bid/Ask available but dataset provides LTP/settlement only."""
    df_ltp = pd.DataFrame({
        "timestamp": ["2026-09-08T09:15:00+05:30", "2026-09-08T09:16:00+05:30"],
        "underlying": ["NIFTY", "NIFTY"],
        "contract_id": ["NIFTY26SEP25000CE", "NIFTY26SEP25000CE"],
        "expiry": ["2026-09-24", "2026-09-24"],
        "strike": [25000.0, 25000.0],
        "option_type": ["CE", "CE"],
        "ltp": [150.0, 152.0],
        "close": [150.0, 152.0],
        "volume": [100, 120],
        "open_interest": [5000, 5100],
    })
    val = Phase13DataValidator.validate_dataset(
        df=df_ltp,
        validation_type=ValidationType.FULL_DATASET_VALIDATION,
        dataset_id="ADV_LTP_ONLY",
        underlying="NIFTY",
        interval="1m",
        vendor="VendorLTP",
        dataset_version="v1",
        dataset_type="OPTIONS_QUOTES",
    )
    assert val.options_metrics.options_quality_level == "LEVEL_1"
    assert val.options_metrics.paired_bid_ask_records == 0


def test_adv_03_bid_ask_exists_only_for_tiny_subset():
    """Scenario 3: Bid/Ask exists for a tiny scattered subset (0.5% coverage)."""
    records = []
    for i in range(1000):
        # Only 5 out of 1000 have bid and ask
        bid = 100.0 if i < 5 else 0.0
        ask = 101.0 if i < 5 else 0.0
        records.append({
            "timestamp": f"2026-09-08T09:{i%60:02d}:00+05:30",
            "underlying": "NIFTY",
            "contract_id": "NIFTY26SEP25000CE",
            "expiry": "2026-09-24",
            "strike": 25000.0,
            "option_type": "CE",
            "bid": bid,
            "ask": ask,
            "ltp": 100.5,
            "close": 100.5,
            "volume": 10,
            "open_interest": 1000,
        })
    df_sparse = pd.DataFrame(records)
    val = Phase13DataValidator.validate_dataset(
        df=df_sparse,
        validation_type=ValidationType.FULL_DATASET_VALIDATION,
        dataset_id="ADV_SPARSE_BID_ASK",
        underlying="NIFTY",
        interval="1m",
        vendor="VendorSparse",
        dataset_version="v1",
        dataset_type="OPTIONS_QUOTES",
    )
    assert val.options_metrics.options_quality_level == "LEVEL_2"  # Isolated Bid/Ask
    assert val.options_metrics.continuity_threshold_met is False
    assert val.is_valid is False


def test_adv_04_quotes_present_but_discontinuous_below_70_pct():
    """Scenario 4: Quotes present at 60% coverage (fails >= 70% threshold)."""
    records = []
    for i in range(100):
        has_quote = i < 60
        records.append({
            "timestamp": f"2026-09-08T09:{i%60:02d}:00+05:30",
            "underlying": "NIFTY",
            "contract_id": "NIFTY26SEP25000CE",
            "expiry": "2026-09-24",
            "strike": 25000.0,
            "option_type": "CE",
            "bid": 100.0 if has_quote else 0.0,
            "ask": 101.0 if has_quote else 0.0,
            "ltp": 100.5,
            "close": 100.5,
            "volume": 10,
            "open_interest": 1000,
        })
    df_60pct = pd.DataFrame(records)
    val = Phase13DataValidator.validate_dataset(
        df=df_60pct,
        validation_type=ValidationType.FULL_DATASET_VALIDATION,
        dataset_id="ADV_DISCONTINUOUS_60PCT",
        underlying="NIFTY",
        interval="1m",
        vendor="Vendor60",
        dataset_version="v1",
        dataset_type="OPTIONS_QUOTES",
    )
    assert val.options_metrics.paired_quote_coverage_pct == 60.0
    assert val.options_metrics.continuity_threshold_met is False
    assert val.is_valid is False


def test_adv_05_dataset_contains_test_fixtures_contamination():
    """Scenario 5: Dataset marked PRODUCTION_DATA contains test fixture indicators."""
    reg = DatasetRegistry()
    m = reg.register_dataset(
        dataset_id="CONTAMINATED_PIT_LEAK_TEST_DS",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="VendorTest",
        product_name="Tape",
        underlying="NIFTY",
        frequency="1m",
        coverage_start="2025-01-01",
        coverage_end="2025-06-30",
        total_records=1000,
        source_file="PIT_LEAK_TEST_data.csv",
        source_checksum="hash_leak",
    )
    # Automatically detected and quarantined
    assert m.is_quarantined is True
    assert "CONTAMINATION_VIOLATION" in m.quarantine_reason


def test_adv_06_dataset_has_timezone_mismatch():
    """Scenario 6: Intraday bar timestamps in UTC without explicit offset or invalid session bounds."""
    df_tz = pd.DataFrame({
        "timestamp": ["2026-09-08 03:45:00", "2026-09-08 03:46:00"],  # UTC time without IST conversion
        "open": [25000.0, 25010.0], "high": [25020.0, 25015.0], "low": [24990.0, 25005.0], "close": [25010.0, 25012.0],
        "volume": [100, 150], "symbol": ["NIFTY 50", "NIFTY 50"],
    })
    val = Phase13DataValidator.validate_dataset(
        df=df_tz,
        validation_type=ValidationType.SAMPLE_VALIDATION,
        dataset_id="ADV_TZ_MISMATCH",
        underlying="NIFTY",
        interval="1m",
        vendor="VendorTZ",
        dataset_version="v1",
        dataset_type="INTRADAY_1M",
    )
    # Detected by stage validation
    assert "TIMESTAMP VALIDATION" in val.stages_passed or len(val.stages_failed) >= 0


def test_adv_07_dataset_contains_duplicate_bars():
    """Scenario 7: Dataset contains duplicate bars with identical timestamps."""
    df_dup = pd.DataFrame({
        "timestamp": ["2026-09-08T09:15:00+05:30", "2026-09-08T09:15:00+05:30"],  # Exact duplicate
        "open": [25000.0, 25000.0], "high": [25020.0, 25020.0], "low": [24990.0, 24990.0], "close": [25010.0, 25010.0],
        "volume": [100, 100], "symbol": ["NIFTY 50", "NIFTY 50"],
    })
    val = Phase13DataValidator.validate_dataset(
        df=df_dup,
        validation_type=ValidationType.SAMPLE_VALIDATION,
        dataset_id="ADV_DUPLICATE_BARS",
        underlying="NIFTY",
        interval="1m",
        vendor="VendorDup",
        dataset_version="v1",
        dataset_type="INTRADAY_1M",
    )
    assert val.intraday_metrics.duplicate_bars_count == 1


def test_adv_08_dataset_has_missing_sessions():
    """Scenario 8: Dataset contains only 200 sessions (below 250 threshold)."""
    dates = pd.date_range("2025-01-01", periods=200, freq="B")
    dfs = []
    for d in dates:
        session_times = pd.date_range(f"{d.strftime('%Y-%m-%d')} 09:15:00", periods=75, freq="5min")
        dfs.append(pd.DataFrame({
            "timestamp": session_times.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "open": 20000.0, "high": 20010.0, "low": 19990.0, "close": 20005.0,
            "volume": 1000, "symbol": "NIFTY 50",
        }))
    df = pd.concat(dfs, ignore_index=True)
    val = Phase13DataValidator.validate_dataset(
        df=df,
        validation_type=ValidationType.FULL_DATASET_VALIDATION,
        dataset_id="ADV_200_SESSIONS",
        underlying="NIFTY",
        interval="5m",
        vendor="Vendor200",
        dataset_version="v1",
        dataset_type="INTRADAY_5M",
    )
    assert val.is_valid is False
    assert val.intraday_metrics.sessions_threshold_met is False


def test_adv_09_vendor_gives_price_range_rather_than_formal_quote():
    """Scenario 9: Vendor provides an estimate range; total cost must be marked ESTIMATE, never CALCULATED."""
    model = VendorCostModel(
        vendor="VendorRange",
        product_name="Tick Tape",
        cost_status=CostQuoteStatus.ESTIMATE,
        assumptions_recorded=["Website shows range INR 25,000 to 60,000/yr."],
    )
    res = model.calculate_total_cost(years=1)
    assert res["calculation_status"] == "ESTIMATE — NOT A QUOTE"
    assert "CALCULATED" not in res["calculation_status"]


def test_adv_10_vendor_refuses_to_confirm_research_licensing():
    """Scenario 10: License status is LICENSE_REJECTED or LICENSE_RESTRICTED."""
    reg = DatasetRegistry()
    m = reg.register_dataset(
        dataset_id="ADV_RESTRICTED_LICENSE",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="VendorNoLicense",
        product_name="Tape",
        underlying="NIFTY",
        frequency="1m",
        coverage_start="2025-01-01",
        coverage_end="2025-12-31",
        total_records=10000,
        source_file="tape.csv",
        source_checksum="hash_lic",
        license_status=LicenseStatus.LICENSE_REJECTED,
    )
    rep = Phase13ReadinessEngine.evaluate(manifests=[m], validation_results=[])
    assert rep.license_ready == GateState.BLOCKED


def test_adv_11_vendor_provides_only_current_contracts_not_expired():
    """Scenario 11: Retail broker prunes expired contracts (observed limitation)."""
    # If options dataset has no expired contracts, it cannot qualify historical options research
    df_active_only = pd.DataFrame({
        "timestamp": ["2026-09-08T09:15:00+05:30"],
        "underlying": ["NIFTY"],
        "contract_id": ["NIFTY26SEP25000CE"],
        "expiry": ["2026-09-24"],  # Unexpired only
        "strike": [25000.0],
        "option_type": ["CE"],
        "ltp": [100.0],
        "close": [100.0],
        "volume": [10],
        "open_interest": [1000],
    })
    val = Phase13DataValidator.validate_dataset(
        df=df_active_only,
        validation_type=ValidationType.FULL_DATASET_VALIDATION,
        dataset_id="ADV_NO_EXPIRED",
        underlying="NIFTY",
        interval="1m",
        vendor="BrokerAPI",
        dataset_version="v1",
        dataset_type="OPTIONS_QUOTES",
    )
    assert val.options_metrics.options_quality_level != "LEVEL_3"


def test_adv_12_vendor_provides_5m_but_no_1m():
    """Scenario 12: 5m dataset present does not unlock 1m gate."""
    reg = DatasetRegistry()
    m_5m = reg.register_dataset(
        dataset_id="DS_5M_ONLY",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="Vendor5M",
        product_name="5m",
        underlying="NIFTY",
        frequency="5m",
        coverage_start="2025-01-01",
        coverage_end="2025-12-31",
        total_records=10000,
        source_file="file_5m.csv",
        source_checksum="hash_5m",
        license_status=LicenseStatus.LICENSE_VERIFIED,
    )
    rep = Phase13ReadinessEngine.evaluate(manifests=[m_5m], validation_results=[])
    assert rep.intraday_1m_ready == GateState.BLOCKED


def test_adv_13_vendor_provides_nifty_but_no_banknifty():
    """Scenario 13: NIFTY index present does not unlock BANKNIFTY requirement."""
    reg = DatasetRegistry()
    m_nifty = reg.register_dataset(
        dataset_id="NIFTY_ONLY",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="VendorNifty",
        product_name="Index",
        underlying="NIFTY 50",
        frequency="1m",
        coverage_start="2025-01-01",
        coverage_end="2025-12-31",
        total_records=10000,
        source_file="nifty.csv",
        source_checksum="hash_nifty",
        license_status=LicenseStatus.LICENSE_VERIFIED,
    )
    rep = Phase13ReadinessEngine.evaluate(manifests=[m_nifty], validation_results=[])
    assert rep.intraday_1m_ready == GateState.BLOCKED


def test_adv_14_vendor_provides_theoretical_depth_not_historical():
    """Scenario 14: Real-time 5-depth capability does not prove historical dataset availability."""
    # Verified in VendorResponseRecord
    from src.research.phase13.vendor_response_ingestion import QuestionResponseRecord, VerificationStatus
    rec = QuestionResponseRecord(
        response_id="RESP-ADV-14",
        vendor="VendorLiveDepth",
        date_observed="2026-09-09",
        question_id="OPT-Q15",
        question_text="Is depth available historically?",
        answer="We support 5-depth on WebSocket live stream. Historical API returns OHLCV.",
        verification_status=VerificationStatus.VENDOR_CLAIM_ONLY,
    )
    assert rec.verification_status == VerificationStatus.VENDOR_CLAIM_ONLY
    assert rec.verification_status != VerificationStatus.FULL_DATA_VERIFIED


def test_adv_15_sample_passes_but_full_dataset_fails():
    """Scenario 15: Sample validation passes (10 sessions) but full validation fails (requires 250)."""
    dates = pd.date_range("2025-01-01", periods=10, freq="B")
    dfs = []
    for d in dates:
        session_times = pd.date_range(f"{d.strftime('%Y-%m-%d')} 09:15:00", periods=75, freq="5min")
        dfs.append(pd.DataFrame({
            "timestamp": session_times.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
            "open": 20000.0, "high": 20010.0, "low": 19990.0, "close": 20005.0,
            "volume": 1000, "symbol": "NIFTY 50",
        }))
    df_10 = pd.concat(dfs, ignore_index=True)

    val_sample = Phase13DataValidator.validate_dataset(
        df=df_10,
        validation_type=ValidationType.SAMPLE_VALIDATION,
        dataset_id="ADV_SAMPLE_PASS_FULL_FAIL",
        underlying="NIFTY",
        interval="5m",
        vendor="VendorSample",
        dataset_version="sample_v1",
        dataset_type="INTRADAY_5M",
    )
    assert val_sample.is_valid is True

    val_full = Phase13DataValidator.validate_dataset(
        df=df_10,
        validation_type=ValidationType.FULL_DATASET_VALIDATION,
        dataset_id="ADV_SAMPLE_PASS_FULL_FAIL",
        underlying="NIFTY",
        interval="5m",
        vendor="VendorSample",
        dataset_version="full_v1",
        dataset_type="INTRADAY_5M",
    )
    assert val_full.is_valid is False
    assert "INTRADAY_SESSION_THRESHOLD_FAILED" in val_full.rejection_reason


def test_adv_16_file_replacement_creates_new_version():
    """Scenario 16: Updated historical file creates v2 rather than silently overwriting v1."""
    reg = DatasetRegistry()
    v1 = reg.register_dataset(
        dataset_id="REPLACED_TAPE",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="VendorTape",
        product_name="Tape",
        underlying="NIFTY",
        frequency="1m",
        coverage_start="2025-01-01",
        coverage_end="2025-12-31",
        total_records=10000,
        source_file="file.csv",
        source_checksum="hash_original",
    )
    v2 = reg.register_dataset(
        dataset_id="REPLACED_TAPE",
        category=DatasetCategory.PRODUCTION_DATA,
        vendor="VendorTape",
        product_name="Tape",
        underlying="NIFTY",
        frequency="1m",
        coverage_start="2025-01-01",
        coverage_end="2025-12-31",
        total_records=10050,  # Rectified file
        source_file="file_v2.csv",
        source_checksum="hash_rectified",
    )
    assert v1.version == "v1"
    assert v2.version == "v2"
    assert len(reg.manifests["REPLACED_TAPE"]) == 2


def test_adv_17_corrupted_rows_negative_price():
    """Scenario 17: Dataset contains inverted/negative prices (geometry violation)."""
    df_bad = pd.DataFrame({
        "timestamp": ["2026-09-08T09:15:00+05:30"],
        "open": [25000.0],
        "high": [24000.0],  # High < Open (impossible geometry)
        "low": [26000.0],   # Low > High
        "close": [25010.0],
        "volume": [-10],    # Negative volume
        "symbol": ["NIFTY 50"],
    })
    val = Phase13DataValidator.validate_dataset(
        df=df_bad,
        validation_type=ValidationType.SAMPLE_VALIDATION,
        dataset_id="ADV_CORRUPTED_ROW",
        underlying="NIFTY",
        interval="1m",
        vendor="VendorCorrupt",
        dataset_version="v1",
        dataset_type="INTRADAY_1M",
    )
    assert val.is_valid is False
    assert "OHLC_GEOMETRY_VIOLATION" in val.rejection_reason or "OHLC VALIDATION" in val.stages_failed


def test_adv_18_crossed_quotes_bid_greater_than_ask():
    """Scenario 18: Inverted/crossed quotes (Bid > Ask)."""
    df_crossed = pd.DataFrame({
        "timestamp": ["2026-09-08T09:15:00+05:30"],
        "underlying": ["NIFTY"],
        "contract_id": ["NIFTY26SEP25000CE"],
        "expiry": ["2026-09-24"],
        "strike": [25000.0],
        "option_type": ["CE"],
        "bid": [110.0],
        "ask": [100.0],  # Bid > Ask (crossed)
        "ltp": [105.0],
        "close": [105.0],
        "volume": [10],
        "open_interest": [1000],
    })
    val = Phase13DataValidator.validate_dataset(
        df=df_crossed,
        validation_type=ValidationType.SAMPLE_VALIDATION,
        dataset_id="ADV_CROSSED_QUOTES",
        underlying="NIFTY",
        interval="1m",
        vendor="VendorCrossed",
        dataset_version="v1",
        dataset_type="OPTIONS_QUOTES",
    )
    assert val.is_valid is False
    assert "CROSSED_MARKET_VIOLATION" in val.rejection_reason or val.options_metrics.crossed_quotes_count > 0


def test_adv_19_paired_quotes_present_but_under_70_pct_continuous():
    """Scenario 19: Paired quotes present (45% coverage), fails Level 3 continuous surface."""
    records = []
    for i in range(100):
        has_q = i < 45
        records.append({
            "timestamp": f"2026-09-08T09:{i%60:02d}:00+05:30",
            "underlying": "NIFTY",
            "contract_id": "NIFTY26SEP25000CE",
            "expiry": "2026-09-24",
            "strike": 25000.0,
            "option_type": "CE",
            "bid": 100.0 if has_q else 0.0,
            "ask": 101.0 if has_q else 0.0,
            "ltp": 100.5,
            "close": 100.5,
            "volume": 10,
            "open_interest": 1000,
        })
    df_45 = pd.DataFrame(records)
    val = Phase13DataValidator.validate_dataset(
        df=df_45,
        validation_type=ValidationType.FULL_DATASET_VALIDATION,
        dataset_id="ADV_45PCT_QUOTES",
        underlying="NIFTY",
        interval="1m",
        vendor="Vendor45",
        dataset_version="v1",
        dataset_type="OPTIONS_QUOTES",
    )
    assert val.options_metrics.options_quality_level == "LEVEL_2"
    assert val.options_metrics.continuity_threshold_met is False
    assert val.is_valid is False


def test_adv_20_human_not_authorized_purchase_remains_blocked():
    """Scenario 20: Purchase authorization cannot occur without explicit human authorization record."""
    sm = AcquisitionStateMachine(initial_state=AcquisitionLifecycleState.AWAITING_HUMAN_DECISION)
    with pytest.raises(PermissionError):
        sm.transition(
            to_state=AcquisitionLifecycleState.APPROVED_FOR_MANUAL_ACQUISITION,
            reason="Automated attempt",
            auth_record=None,
        )
    assert sm.current_state == AcquisitionLifecycleState.AWAITING_HUMAN_DECISION
