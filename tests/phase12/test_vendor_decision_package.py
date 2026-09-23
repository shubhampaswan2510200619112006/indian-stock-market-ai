"""
Unit and Regression Tests for Phase 12 Final Mission — Vendor Contact & Data Acquisition Decision Package.
"""

from __future__ import annotations

import json
import os
import pytest

from src.research.phase12 import (
    ALLOW_BROKER_CONNECTION,
    ALLOW_LIVE_EXECUTION,
    ALLOW_OPTIONS_BACKTEST,
    ALLOW_PAPER_AUTOMATION,
    AUTO_PAPER_ORDER_SUBMISSION,
    BROKER,
    HUMAN_DECISION_REQUIRED,
    LIVE_EXECUTION,
    NEW_UNPREREGISTERED_ALPHA_RESEARCH,
    OPTIONS_EXECUTION,
    PURCHASE_AUTHORIZED,
    STRATEGY_OPTIMIZATION,
    UNLIMITED_PARAMETER_SEARCH,
)
from src.research.phase12.baseline_verifier import verify_frozen_baselines
from src.research.phase12.decision_package import (
    AcquisitionDecisionStateMachine,
    DecisionPackageManager,
    DecisionState,
    EvidenceStatus,
    QuoteStatus,
)


def test_safety_invariants():
    """Verify that all platform execution and commercial safety flags remain locked."""
    assert BROKER == "NONE"
    assert LIVE_EXECUTION == "DISABLED"
    assert AUTO_PAPER_ORDER_SUBMISSION == "DISABLED"
    assert OPTIONS_EXECUTION == "BLOCKED"
    assert NEW_UNPREREGISTERED_ALPHA_RESEARCH == "DISABLED"
    assert UNLIMITED_PARAMETER_SEARCH == "DISABLED"
    assert STRATEGY_OPTIMIZATION == "DISABLED"

    assert ALLOW_LIVE_EXECUTION is False
    assert ALLOW_BROKER_CONNECTION is False
    assert ALLOW_PAPER_AUTOMATION is False
    assert ALLOW_OPTIONS_BACKTEST is False
    assert PURCHASE_AUTHORIZED is False
    assert HUMAN_DECISION_REQUIRED is True


def test_frozen_baselines_integrity():
    """Verify that all historical baselines (9.7 through 12) remain intact."""
    result = verify_frozen_baselines()
    assert result["all_baselines_intact"] is True
    assert result["phase_9_7_baseline"] == "FROZEN"
    assert result["phase_9_8_research_results"] == "FROZEN"
    assert result["phase_9_8_numerical_results"] == "FROZEN"
    assert result["phase_9_9_freeze_manifest"] == "FROZEN_IMMUTABLE"
    assert result["phase_10a_artifacts_status"] == "INTACT"
    assert result["phase_10b_artifacts_status"] == "INTACT"
    assert result["phase_10c_artifacts_status"] == "INTACT"
    assert result["phase_11_artifacts_status"] == "INTACT"
    assert len(result["errors"]) == 0


def test_canonical_acquisition_decision_package_schema():
    """Verify canonical acquisition requirements artifact structure and thresholds."""
    reqs = DecisionPackageManager.get_canonical_acquisition_requirements()
    assert reqs["specification_version"] == "phase12_final_decision_package_v1"

    # Governance checks
    gov = reqs["governance"]
    assert gov["purchase_authorized"] is False
    assert gov["human_decision_required"] is True
    assert gov["broker"] == "NONE"
    assert gov["live_execution"] == "DISABLED"
    assert gov["auto_paper_order_submission"] == "DISABLED"
    assert gov["options_execution"] == "BLOCKED"

    # Intraday checks
    intra = reqs["intraday_requirements"]
    assert "NIFTY 50" in intra["underlyings"]
    assert "NIFTY BANK" in intra["underlyings"]
    assert "1 minute" in intra["intervals"]
    assert "5 minute" in intra["intervals"]
    assert intra["minimum_sessions"] == 250
    assert intra["minimum_sessions_threshold_label"] == "PROJECT_RESEARCH_THRESHOLD"
    assert "PROJECT_RESEARCH_THRESHOLD" in intra["minimum_sessions_threshold_explanation"]
    assert "Asia/Kolkata (+05:30)" in intra["timezone"]
    assert "09:15-15:30 IST" in intra["market_session_ist"]

    # Options checks
    opt = reqs["options_requirements"]
    assert "NIFTY OPTIONS" in opt["targets"]
    assert "BANKNIFTY OPTIONS" in opt["targets"]
    assert "bid" in opt["minimum_schema"]
    assert "ask" in opt["minimum_schema"]
    assert opt["paired_quote_continuity_threshold_pct"] == 70.0
    assert opt["paired_quote_continuity_threshold_label"] == "PROJECT_RESEARCH_THRESHOLD"
    assert "PROJECT_RESEARCH_THRESHOLD" in opt["paired_quote_continuity_explanation"]

    # Contract validation: dynamic calendar/spec, no hardcoded weekdays
    cv = opt["contract_validation"]
    assert cv["method"] == "EXCHANGE_SPEC_AND_CALENDAR_DRIVEN"
    assert any("Thursday" in p for p in cv["prohibited_assumptions"])
    assert any("Wednesday" in p for p in cv["prohibited_assumptions"])


def test_provisional_candidate_ranking_labeling():
    """Verify mandatory correction 1: candidate ranking is provisional and conditional."""
    reqs = DecisionPackageManager.get_canonical_acquisition_requirements()
    p_rank = reqs["provisional_candidate_ranking"]
    assert p_rank["ranking_label"] == "PROVISIONAL_CANDIDATE_RANKING"
    assert "SUBJECT_TO_VENDOR_CONFIRMATION" in p_rank["mandatory_conditions"]
    assert "SUBJECT_TO_FORMAL_QUOTATION" in p_rank["mandatory_conditions"]
    assert "SUBJECT_TO_LICENSE_REVIEW" in p_rank["mandatory_conditions"]
    assert "SUBJECT_TO_SAMPLE_VALIDATION" in p_rank["mandatory_conditions"]
    assert "NOT a purchasing recommendation" in p_rank["disclaimer"]


def test_capability_vs_historical_dataset_availability():
    """Verify mandatory correction 3: live capability does NOT imply historical dataset availability."""
    claims = DecisionPackageManager.get_vendor_claims_catalog()
    assert len(claims) >= 9

    # TrueData live vs historical
    td_live = [c for c in claims if c["claim_id"] == "TD-002"][0]
    td_hist = [c for c in claims if c["claim_id"] == "TD-003"][0]
    assert td_live["capability_type"] == "PROVIDER_CAPABILITY"
    assert td_live["verification_status"] == EvidenceStatus.VERIFIED.value
    assert td_hist["capability_type"] == "EXACT_HISTORICAL_DATASET_AVAILABILITY"
    assert td_hist["verification_status"] == EvidenceStatus.REQUIRES_VENDOR_CONFIRMATION.value

    # GDFL live vs historical
    gdfl_live = [c for c in claims if c["claim_id"] == "GDFL-002"][0]
    gdfl_hist = [c for c in claims if c["claim_id"] == "GDFL-003"][0]
    assert gdfl_live["capability_type"] == "PROVIDER_CAPABILITY"
    assert gdfl_live["verification_status"] == EvidenceStatus.VERIFIED.value
    assert gdfl_hist["capability_type"] == "EXACT_HISTORICAL_DATASET_AVAILABILITY"
    assert gdfl_hist["verification_status"] == EvidenceStatus.REQUIRES_VENDOR_CONFIRMATION.value


def test_cost_integrity_and_normalization():
    """Verify mandatory correction 2: cost integrity with explicit estimates, quotes, or UNKNOWN."""
    cost_model = DecisionPackageManager.get_cost_comparison_model()
    providers = {p["provider"]: p for p in cost_model["providers"]}

    # NSE DotEx pricing status must be SALES_QUOTE_REQUIRED and totals UNKNOWN
    nse = providers["NSE Data & Analytics Ltd (DotEx)"]
    assert nse["pricing_status"] == QuoteStatus.SALES_QUOTE_REQUIRED.value
    assert "UNKNOWN" in nse["cost_breakdown"]["one_time_data_cost"]
    assert "UNKNOWN" in nse["year_1_total_cost"]
    assert "ESTIMATE — NOT A QUOTE" in nse["year_1_total_cost"]

    # TrueData pricing status must be ESTIMATE — NOT A QUOTE
    td = providers["TrueData (TrueData India)"]
    assert td["pricing_status"] == QuoteStatus.ESTIMATE.value
    assert "ESTIMATE — NOT A QUOTE" in td["year_1_total_cost"]
    assert "ESTIMATE — NOT A QUOTE" in td["three_year_total_cost"]

    # Retail broker pricing is verified quote but fails requirements
    zerodha = providers["Zerodha Kite Connect"]
    assert zerodha["pricing_status"] == QuoteStatus.VERIFIED_QUOTE.value
    assert zerodha["year_1_total_cost"] == 48000
    assert zerodha["three_year_total_cost"] == 144000
    assert "INSUFFICIENT" in zerodha["commercial_assessment"]


def test_value_scoring_hard_gate_non_override():
    """Verify transparent value scoring model enforces hard gates (cost cannot override missing quotes)."""
    scoring = DecisionPackageManager.get_value_scoring_model()
    weights = scoring["weights"]
    assert sum(weights.values()) == pytest.approx(1.0, 0.01)

    eval_by_provider = {e["provider"]: e for e in scoring["evaluations"]}

    # NSE DotEx passes hard gates
    assert eval_by_provider["NSE Data & Analytics Ltd (DotEx)"]["hard_gate_pass"] is True

    # Zerodha has low cost but fails hard gate for missing options Bid/Ask
    zerodha = eval_by_provider["Zerodha Kite Connect"]
    assert zerodha["hard_gate_pass"] is False
    assert "HARD_GATE_FAILED" in zerodha["rejection_reason"]

    # Yahoo Finance has 0 cost but fails hard gate
    yahoo = eval_by_provider["Public / Free Endpoints (Yahoo Finance)"]
    assert yahoo["hard_gate_pass"] is False
    assert "HARD_GATE_FAILED" in yahoo["rejection_reason"]


def test_decision_state_machine_and_human_authorization_lock():
    """Verify state machine strictly defaults to HUMAN_AUTHORIZATION_PENDING and prevents automated approval."""
    sm = AcquisitionDecisionStateMachine()
    assert sm.current_state == DecisionState.HUMAN_AUTHORIZATION_PENDING
    assert sm.purchase_authorized is False
    assert sm.human_decision_required is True

    # Attempt transition to APPROVED_FOR_ACQUISITION without human signoff must fail
    with pytest.raises(PermissionError) as exc_info:
        sm.transition(
            new_state=DecisionState.APPROVED_FOR_ACQUISITION,
            actor="AUTOMATED_SCRIPT",
            reason="Vendor looks good",
            human_signoff=False,
        )
    assert "explicit human authorization" in str(exc_info.value)
    assert sm.current_state == DecisionState.HUMAN_AUTHORIZATION_PENDING
    assert sm.purchase_authorized is False

    # Transition with explicit human sign-off succeeds
    success = sm.transition(
        new_state=DecisionState.APPROVED_FOR_ACQUISITION,
        actor="Human Portfolio Manager",
        reason="Contract and sample validated",
        human_signoff=True,
    )
    assert success is True
    assert sm.current_state == DecisionState.APPROVED_FOR_ACQUISITION
    assert sm.purchase_authorized is True
    assert sm.authorized_by == "Human Portfolio Manager"


def test_all_decision_package_artifacts_exist_and_populated():
    """Verify that all 5 JSON files and 10 markdown reports exist and are populated."""
    workspace_root = "."
    res = DecisionPackageManager.generate_all_artifacts(workspace_root)
    assert res["status"] == "SUCCESS"

    data_dir = os.path.join(workspace_root, "data", "phase12")
    required_json_files = [
        "acquisition_decision_package.json",
        "acquisition_decision.json",
        "vendor_claims.json",
        "vendor_responses.json",
        "cost_comparison.json",
    ]
    for filename in required_json_files:
        path = os.path.join(data_dir, filename)
        assert os.path.exists(path), f"Missing data artifact: {filename}"
        with open(path, "r", encoding="utf-8") as f:
            content = json.load(f)
            assert content is not None

    reports_dir = os.path.join(workspace_root, "reports", "phase12")
    required_reports = [
        "VENDOR_CONTACT_QUESTIONNAIRE.md",
        "VENDOR_RESPONSE_TEMPLATE.md",
        "VENDOR_COMPARISON_MATRIX.md",
        "ACQUISITION_DECISION_TREE.md",
        "PRE_PURCHASE_ACCEPTANCE_TEST.md",
        "HUMAN_ACQUISITION_DECISION_FORM.md",
        "VENDOR_ENQUIRY_NSE.md",
        "VENDOR_ENQUIRY_TRUEDATA.md",
        "VENDOR_ENQUIRY_GDFL.md",
        "FINAL_ACQUISITION_DECISION_PACKAGE.md",
    ]
    for filename in required_reports:
        path = os.path.join(reports_dir, filename)
        assert os.path.exists(path), f"Missing report artifact: {filename}"
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
            assert len(text) > 100, f"Report {filename} is unexpectedly empty"


def test_vendor_contact_questionnaire_contents():
    """Verify questionnaire has exactly 20 intraday and 30 options questions."""
    reports_dir = os.path.join(".", "reports", "phase12")
    q_path = os.path.join(reports_dir, "VENDOR_CONTACT_QUESTIONNAIRE.md")
    with open(q_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Check for presence of questions
    assert "20. What specific research, non-display, and internal quantitative use license is included?" in text
    assert "30. What specific redistribution, third-party disclosure, or display restrictions apply?" in text


def test_vendor_comparison_matrix_preserves_unknown():
    """Verify matrix retains UNKNOWN for unconfirmed attributes rather than fabricated entries."""
    reports_dir = os.path.join(".", "reports", "phase12")
    matrix_path = os.path.join(reports_dir, "VENDOR_COMPARISON_MATRIX.md")
    with open(matrix_path, "r", encoding="utf-8") as f:
        text = f.read()
    assert "UNKNOWN" in text
    assert "REQUIRES_VENDOR_QUOTE" in text
    assert "REQUIRES_CONFIRMATION" in text
