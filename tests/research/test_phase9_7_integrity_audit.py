"""
Phase 9.7 — Research Integrity Audit, Data Expansion & Phase 10 Gate Test Suite.

Verifies:
1. Baseline Checksum Integrity (Phase 9.5 and Phase 9.6 baseline preservation)
2. Timing & Point-in-Time Audit (Backward return detection & invalidation)
3. Timing Method Comparison (Original INVALIDATED, Forward C2C VALID, Next-Day O2O VALID)
4. Trade Cost & Cash Accounting Double-Entry Reconciliation (Exact matching)
5. Information Leakage Audit across Pipeline Components
6. Data Expansion Target (>= 250 sessions) decoupled from Statistical Sufficiency
7. Strict Separation of NIFTY and BANKNIFTY (No instrument pooling / cherry-picking)
8. Options Quote Audit & 0.0% Bid/Ask Execution Gate Enforcement (BLOCKED)
9. H008 LTP-Only Prohibition (Must not be declared positive from LTP quotes)
10. Block Bootstrap Effective Sample Size & Confidence Intervals
11. Phase 10 Gate Survival Evaluation (Conservative PHASE_10_NOT_JUSTIFIED enforcement)
12. Zero New Hypotheses Constraint (Audit & Revalidation Only)
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.database.connection import get_session
from src.database.models import EquityPriceDB
from src.research.bid_ask_investigation import OptionsBidAskAuditEngine
from src.research.historical_expansion import HistoricalDataExpansionEngine
from src.research.hypotheses import get_all_registered_hypotheses
from src.research.integrity_audit import ResearchIntegrityAuditor
from src.research.phase10_gate import Phase10Decision, Phase10GateEngine
from src.research.revalidation import LockedHypothesisRevalidationEngine


# -----------------------------------------------------------------------------
# 1. Baseline Checksum Integrity Tests
# -----------------------------------------------------------------------------

def test_baseline_checksum_integrity():
    audit = ResearchIntegrityAuditor.audit_baseline_integrity()
    assert audit.phase95_validation_hash != ""
    assert audit.phase96_validation_hash != ""
    assert audit.phase95_hash_matches_baseline is True
    assert audit.phase96_hash_matches_baseline is True


# -----------------------------------------------------------------------------
# 2. Timing & Point-in-Time Audit Tests
# -----------------------------------------------------------------------------

def test_timing_audit_backward_return_detection():
    timing_audit = ResearchIntegrityAuditor.audit_timing_and_point_in_time()
    assert timing_audit.timing_error_detected is True
    assert timing_audit.status_classification == "MATERIAL_TIMING_ERROR_REPAIRED"
    assert "INVALIDATED_FOR_INFERENCE" in timing_audit.original_result_status
    assert "VALID" in timing_audit.authoritative_result_status
    assert "backward" in timing_audit.description.lower()
    assert timing_audit.affected_component != ""


def test_timing_comparison_methods():
    session = get_session()
    rows = session.query(EquityPriceDB).filter(EquityPriceDB.symbol == "NIFTY").order_by(EquityPriceDB.date.asc()).limit(120).all()
    session.close()

    df_nifty = pd.DataFrame([
        {"date": r.date, "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume}
        for r in rows
    ])
    comparisons = LockedHypothesisRevalidationEngine.compare_timing_methods(df_nifty, symbol="NIFTY")
    assert len(comparisons) == 3

    statuses = [c.status for c in comparisons]
    methods = [c.timing_method for c in comparisons]

    assert any("INVALIDATED" in s for s in statuses)
    assert any("VALID" in s for s in statuses)
    assert any("Phase 9.5" in m for m in methods)
    assert any("Forward Close-to-Close" in m for m in methods)
    assert any("Next-Day Open-to-Open" in m for m in methods)

    for c in comparisons:
        assert isinstance(c.gross_return_pct, float)
        assert isinstance(c.net_return_pct, float)
        assert isinstance(c.sharpe_ratio, float)
        assert isinstance(c.max_drawdown_pct, float)


# -----------------------------------------------------------------------------
# 3. Trade Cost & Double-Entry Cash Accounting Reconciliation
# -----------------------------------------------------------------------------

def test_trade_cost_reconciliation():
    signals = np.array([1, 1, -1, 0, 1, -1, 0, 1, 1, -1] * 5)
    returns = np.random.normal(0.0005, 0.01, size=len(signals))

    cost_audit = ResearchIntegrityAuditor.audit_trade_costs(signals, returns)
    assert cost_audit.total_trades_audited > 0
    assert cost_audit.reconciliation_verified is True
    assert cost_audit.sum_trades_equals_portfolio is True
    assert cost_audit.unit_consistency_verified is True
    assert len(cost_audit.sample_audited_trades) > 0

    # Net PnL must equal Gross PnL - All Frictions
    expected_net = cost_audit.gross_pnl_pct - cost_audit.total_fees_pct - cost_audit.total_slippage_pct
    assert np.isclose(cost_audit.net_pnl_pct, expected_net, atol=1e-5)


def test_backtest_cash_accounting_reconciliation():
    accounting = ResearchIntegrityAuditor.audit_backtest_accounting(initial_cash=1_000_000.0)
    assert accounting.cash_reconciliation_exact is True
    assert accounting.audit_verdict == "ACCOUNTING_PASS"
    assert accounting.duplicate_fills_found == 0
    assert accounting.impossible_fills_found == 0
    assert accounting.negative_cash_events == 0


# -----------------------------------------------------------------------------
# 4. Pipeline Information Leakage Audit Tests
# -----------------------------------------------------------------------------

def test_leakage_audit_across_components():
    leak_audit = ResearchIntegrityAuditor.audit_leakage_across_components()
    assert leak_audit.target_leakage_detected is False
    assert leak_audit.scaler_leakage_detected is False
    assert leak_audit.rolling_window_lookahead_detected is False
    assert leak_audit.future_labels_leakage_detected is False
    assert leak_audit.audit_verdict == "CLEAN_AFTER_TIMING_REPAIR"


# -----------------------------------------------------------------------------
# 5. Data Expansion & Decoupling from Statistical Sufficiency
# -----------------------------------------------------------------------------

def test_data_expansion_coverage_and_sufficiency_separation():
    expanded = HistoricalDataExpansionEngine.get_both_expanded_datasets()
    nifty_df, nifty_cov = expanded["NIFTY"]
    banknifty_df, banknifty_cov = expanded["BANKNIFTY"]

    assert nifty_cov.total_sessions >= 250
    assert banknifty_cov.total_sessions >= 250

    # Mandatory Mandate 1: DATA_COVERAGE_STATUS decoupled from STATISTICAL_SUFFICIENCY_STATUS
    assert nifty_cov.data_coverage_status == "DATA_EXPANDED_SUFFICIENT_COVERAGE"
    assert "NO AUTOMATIC SUFFICIENCY" in nifty_cov.statistical_sufficiency_status
    assert banknifty_cov.data_coverage_status == "DATA_EXPANDED_SUFFICIENT_COVERAGE"


def test_nifty_and_banknifty_separate_analysis():
    reval_path = Path("data/phase9_7_revalidation.json")
    assert reval_path.exists()

    with open(reval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nifty_hyps = data["hypotheses_expanded_dataset_nifty"]
    banknifty_hyps = data["hypotheses_expanded_dataset_banknifty"]

    assert len(nifty_hyps) == 8
    assert len(banknifty_hyps) == 8

    for rn in nifty_hyps:
        assert rn["instrument"] == "NIFTY"
    for rbn in banknifty_hyps:
        assert rbn["instrument"] == "BANKNIFTY"


# -----------------------------------------------------------------------------
# 6. Options Quote Audit & 0.0% Bid/Ask Execution Gate Tests
# -----------------------------------------------------------------------------

def test_options_bid_ask_quote_audit():
    bid_ask_rep = OptionsBidAskAuditEngine.audit_database_quotes()
    assert bid_ask_rep.total_options_quotes > 0
    assert bid_ask_rep.paired_bid_ask_pct == 0.0
    assert bid_ask_rep.execution_backtest_gate == "BLOCKED"
    assert bid_ask_rep.paper_execution_gate == "BLOCKED"


def test_h008_ltp_only_cannot_be_declared_positive():
    reval_path = Path("data/phase9_7_revalidation.json")
    assert reval_path.exists()

    with open(reval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    h008 = [r for r in data["hypotheses_expanded_dataset_nifty"] if r["hypothesis_id"] == "H008_VOLATILITY_STRATEGY_MAPPING"][0]

    # Mandate 8: Cannot be declared positive / SURVIVES from LTP-only results
    assert h008["corrected_status"] in ["INCONCLUSIVE", "INCONCLUSIVE (EXECUTION_DATA_BLOCKED)", "REJECTED"]
    assert h008["success_criteria_met"] is False


# -----------------------------------------------------------------------------
# 7. Block Bootstrap Reporting
# -----------------------------------------------------------------------------

def test_block_bootstrap_audit_reporting():
    sample_rets = np.random.normal(0.0002, 0.01, size=120)
    boot = LockedHypothesisRevalidationEngine.calculate_block_bootstrap(
        sample_rets,
        block_length=3,
        iterations=500,
        random_seed=42,
    )

    assert boot.resampling_method == "STATIONARY_BLOCK_BOOTSTRAP"
    assert boot.block_length_sessions == 3
    assert boot.bootstrap_iterations == 500
    assert boot.random_seed == 42
    assert boot.original_sample_size == 120
    assert boot.effective_sample_size == 40
    assert boot.ci_lower_95 <= boot.observed_value <= boot.ci_upper_95


# -----------------------------------------------------------------------------
# 8. Phase 10 Gate Survival & Conservative Enforcement
# -----------------------------------------------------------------------------

def test_phase10_gate_all_pass_required():
    gate_rep_failed = Phase10GateEngine.evaluate_gates(
        has_methodology_errors=False,
        has_unresolved_leakage=False,
        oos_validated=True,
        gross_edge_bps=-10.0,
        net_edge_bps=-15.0,
        is_cost_robust=False,
        is_regime_robust=False,
        trade_count=100,
        is_reproducible=True,
        paired_bid_ask_pct=0.0,
        surviving_hypothesis=None,
    )

    assert gate_rep_failed.authoritative_decision == Phase10Decision.PHASE_10_NOT_JUSTIFIED
    assert (gate_rep_failed.failed_gate_count + gate_rep_failed.blocked_gate_count) >= 3
    failed_gate_names = [g.gate_name for g in gate_rep_failed.gates if g.status.value in ["FAIL", "BLOCKED"]]
    assert any("Gross Edge" in name for name in failed_gate_names)
    assert any("Net Edge" in name for name in failed_gate_names)


def test_phase10_gate_zero_new_hypotheses_constraint():
    hypotheses = get_all_registered_hypotheses()
    # Mandate 12: Multiple testing - NEW_HYPOTHESES = 0
    assert len(hypotheses) == 8
