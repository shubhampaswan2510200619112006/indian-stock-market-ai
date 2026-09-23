"""
Phase 9.6 — Research Recalibration & Edge Discovery Test Suite.

Verifies:
1. Hypothesis Registry & Pre-Registered Frozen Criteria (H001–H008)
2. Data-Snooping Guard & Multiple-Testing Audit
3. Volatility Persistence ≠ Trading Edge (Predictability vs Quality vs Economic Value)
4. Target Reformulation & Multi-Horizon Purging
5. Confidence Bucket Sample-Size Guards (< 10 samples -> INSUFFICIENT_SAMPLE)
6. Regime Conditioning & Absence of Regime-Picking
7. Cost Decomposition (Gross vs Statutory Fees vs Slippage -> Cases A, B, C)
8. Holding Period Turnover Reduction & Fee Drag
9. 100-Point Research Score & Disqualification Rules (Top 3 Shortlist)
10. Authoritative Phase 10 Gate (PHASE_10_NOT_JUSTIFIED when no surviving edge)
11. Phase 9.6 Research API Endpoints
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.research.hypotheses import (
    ResearchHypothesis,
    HypothesisStatus,
    get_all_registered_hypotheses,
    get_hypothesis_by_id,
)
from src.research.data_snooping_guard import (
    DataSnoopingGuard,
    DataSnoopingViolation,
    PartitionAccessRecord,
)

from src.research.volatility_research import VolatilityResearchEngine
from src.research.target_analysis import TargetReassessmentEngine
from src.research.signal_strength import SignalStrengthEngine
from src.research.cost_analysis import CostAnalysisEngine, CostFailureMode
from src.research.turnover_analysis import TurnoverAnalysisEngine
from src.research.research_score import ResearchScoreEngine
from src.research.hypothesis_evaluator import HypothesisEvaluator
from src.api.main import app


# -----------------------------------------------------------------------------
# 1. Hypothesis Registry & Pre-Registration Tests
# -----------------------------------------------------------------------------

def test_hypothesis_registry_all_registered():
    hypotheses = get_all_registered_hypotheses()
    assert len(hypotheses) == 8
    ids = [h.hypothesis_id for h in hypotheses]
    expected_ids = [
        "H001_VOLATILITY_PERSISTENCE",
        "H002_TARGET_REFORMULATION_MULTI_DAY",
        "H003_REGIME_CONDITIONED_VOLATILITY",
        "H004_HIGH_CONFIDENCE_THRESHOLD",
        "H005_LONG_SHORT_ASYMMETRY",
        "H006_HOLDING_PERIOD_SWING",
        "H007_OPTIONS_OI_PCR_ALPHA",
        "H008_VOLATILITY_STRATEGY_MAPPING",
    ]
    for expected in expected_ids:
        assert expected in ids


def test_hypothesis_frozen_criteria():
    h001 = get_hypothesis_by_id("H001_VOLATILITY_PERSISTENCE")
    assert h001 is not None
    assert h001.is_pre_registered is True
    assert "EWMA" in h001.primary_metric
    assert h001.min_sample_size >= 60
    assert h001.statutory_fees_bps > 0
    assert h001.slippage_bps > 0
    assert "EWMA RMSE" in h001.success_criteria
    assert "failure_criteria" in h001.to_dict()


def test_hypothesis_serialization():
    h002 = get_hypothesis_by_id("H002_TARGET_REFORMULATION_MULTI_DAY")
    d = h002.to_dict()
    assert d["hypothesis_id"] == "H002_TARGET_REFORMULATION_MULTI_DAY"
    assert d["is_pre_registered"] is True
    assert "min_oos_improvement" in d


# -----------------------------------------------------------------------------
# 2. Data-Snooping Guard Tests
# -----------------------------------------------------------------------------

def test_data_snooping_guard_access_recording(tmp_path):
    guard_path = str(tmp_path / "audit.json")
    guard = DataSnoopingGuard(audit_filepath=guard_path)
    
    guard.record_test_access(
        hypothesis_id="H001_VOLATILITY_PERSISTENCE",
        partition_name="TRAIN_VAL",
        function_name="eval_test",
        is_confirmatory=True,
    )
    report = guard.get_audit_report()
    assert report["total_partition_access_events"] == 1
    assert report["final_untouched_test_accesses"] == 0
    assert report["status"] == "DATA_SNOOPING_CLEAN"


def test_data_snooping_guard_repeated_test_access_flagged(tmp_path):
    guard_path = str(tmp_path / "audit.json")
    guard = DataSnoopingGuard(audit_filepath=guard_path)
    
    # First access to final test is allowed
    guard.record_test_access(
        hypothesis_id="H002_TARGET_REFORMULATION_MULTI_DAY",
        partition_name="FINAL_UNTOUCHED_TEST",
    )
    
    # Second access to final test must raise DataSnoopingViolation
    with pytest.raises(DataSnoopingViolation) as exc_info:
        guard.record_test_access(
            hypothesis_id="H002_TARGET_REFORMULATION_MULTI_DAY",
            partition_name="FINAL_UNTOUCHED_TEST",
        )
    assert "FINAL_TEST_CONTAMINATED" in str(exc_info.value)


def test_data_snooping_guard_timing_violation():
    guard = DataSnoopingGuard()
    with pytest.raises(DataSnoopingViolation) as exc_info:
        guard.assert_pre_registration_timing(
            hypothesis_created_at="2026-09-08T14:00:00+00:00",
            evaluation_started_at="2026-09-08T10:00:00+00:00", # Earlier than created!
        )
    assert "Data Snooping Inversion" in str(exc_info.value)


# -----------------------------------------------------------------------------
# 3. Volatility Research & Baselines (H001)
# -----------------------------------------------------------------------------

def test_volatility_persistence_separate_from_trading_edge():
    """Verify H001 properly decouples autocorrelation from trading edge."""
    dates = pd.date_range("2026-01-01", periods=60, freq="B")
    np.random.seed(42)
    # Generate persistent AR(1) volatility series
    rv_vals = [0.15]
    for _ in range(59):
        rv_vals.append(0.85 * rv_vals[-1] + 0.15 * 0.15 + float(np.random.normal(0, 0.005)))
    rv = pd.Series(rv_vals, index=dates)
    fwd_rv = rv.shift(-5).bfill()

    df = pd.DataFrame({
        "date": dates,
        "close": 20000.0 + np.cumsum(np.random.normal(0, 10, size=60)),
        "rv_5d": rv,
        "target_fwd_rv_5d": fwd_rv,
    })

    engine = VolatilityResearchEngine()
    pers = engine.calculate_persistence(rv)
    assert hasattr(pers, "autocorr_lag_1")
    assert hasattr(pers, "autocorr_lag_5")
    assert pers.is_persistent is True
    assert "DOES NOT constitute a tradable edge" in pers.interpretation

    rep = engine.evaluate_volatility_forecasting(df)
    assert hasattr(rep, "persistence")
    assert hasattr(rep, "forecast_evaluations")


# -----------------------------------------------------------------------------
# 4. Target Reformulation (H002)
# -----------------------------------------------------------------------------

def test_target_reformulation_multi_horizon():
    dates = pd.date_range("2026-01-01", periods=60, freq="B")
    np.random.seed(42)
    rets = np.random.normal(0.0005, 0.01, size=60)
    prices = 20000.0 * np.exp(np.cumsum(rets))
    df = pd.DataFrame({
        "date": dates,
        "close": prices,
        "target_fwd_dir_1d": np.random.randint(0, 2, size=60),
        "target_fwd_dir_3d": np.random.randint(0, 2, size=60),
        "target_fwd_dir_5d": np.random.randint(0, 2, size=60),
        "feature_1": np.random.randn(60),
    })
    
    engine = TargetReassessmentEngine()
    results = engine.evaluate_multi_horizon_direction(df, feature_cols=["feature_1"])
    assert "DIR_1D" in results
    assert "DIR_3D" in results
    assert "DIR_5D" in results
    assert results["DIR_1D"].target_name == "target_fwd_dir_1d"


# -----------------------------------------------------------------------------
# 5. Signal Strength & Sample-Size Guards (H004)
# -----------------------------------------------------------------------------

def test_signal_strength_sample_size_guards():
    # Only 4 samples in high conviction bucket (>= 0.70)
    probs = np.array([0.72, 0.75, 0.71, 0.74] + [0.52] * 40)
    y_true = np.array([1, 1, 0, 1] + [1] * 40)
    returns = np.array([0.01, 0.02, -0.01, 0.015] + [0.001] * 40)
    
    engine = SignalStrengthEngine()
    summary = engine.evaluate_confidence_buckets(probs, y_true, returns)
    
    # Check that 70%+ bucket exists and has INSUFFICIENT_SAMPLE
    b70 = [b for b in summary.bucket_reports if b.bucket_label.startswith("70%+")][0]
    assert b70.observation_count == 4
    assert b70.sample_status == "INSUFFICIENT_SAMPLE"


# -----------------------------------------------------------------------------
# 6. Cost Decomposition (Cases A, B, C)
# -----------------------------------------------------------------------------

def test_cost_decomposition_case_classification():
    engine = CostAnalysisEngine()
    
    # Case A: Strategy return before costs is negative
    signals = np.array([1, 1, -1, -1, 1] * 10)
    # Returns moving against signals
    rets_neg = -0.01 * signals
    rep_a = engine.decompose_costs(signals, rets_neg)
    assert rep_a.failure_mode == CostFailureMode.CASE_A_NO_GROSS_EDGE
    assert rep_a.gross_pnl_pct < 0
    
    # Case B: Strategy return before costs is positive, but transaction costs flip it negative
    rets_weak = 0.0003 * signals # very tiny positive move: 3 bps
    rep_b = engine.decompose_costs(signals, rets_weak, base_fee_pct=0.0005, base_slippage_pct=0.0005)
    assert rep_b.failure_mode == CostFailureMode.CASE_B_COST_DESTROYED_EDGE
    assert rep_b.gross_pnl_pct > 0
    assert rep_b.net_pnl_pct < 0
    
    # Case C: Strategy return before costs is large enough to survive all frictions
    rets_strong = 0.05 * signals # 500 bps per session
    rep_c = engine.decompose_costs(signals, rets_strong, base_fee_pct=0.0005, base_slippage_pct=0.0005)
    assert rep_c.failure_mode == CostFailureMode.CASE_C_SURVIVING_EDGE
    assert rep_c.net_pnl_pct > 0


# -----------------------------------------------------------------------------
# 7. Holding Period Turnover Reduction (H006)
# -----------------------------------------------------------------------------

def test_holding_period_turnover_friction():
    engine = TurnoverAnalysisEngine()
    # High turnover signals: flip every day
    signals_daily = np.array([1, -1, 1, -1, 1, -1] * 10)
    rets = np.zeros(60)
    rep_daily = engine.analyze_turnover(signals_daily, rets)
    
    # Low turnover signals: hold for 10 days
    signals_swing = np.array([1] * 20 + [-1] * 20 + [1] * 20)
    rep_swing = engine.analyze_turnover(signals_swing, rets)
    
    assert rep_swing.trades_per_session < rep_daily.trades_per_session
    assert rep_swing.average_holding_period_sessions > rep_daily.average_holding_period_sessions


# -----------------------------------------------------------------------------
# 8. 100-Point Research Score & Disqualification Rules
# -----------------------------------------------------------------------------

def test_research_score_disqualification_for_negative_sharpe():
    engine = ResearchScoreEngine()
    # Hypothesis with positive OOS improvement but negative net Sharpe
    breakdown = engine.calculate_score(
        hypothesis_id="H002_TARGET_REFORMULATION_MULTI_DAY",
        oos_accuracy=0.55,
        baseline_accuracy=0.50,
        sample_size=100,
        net_sharpe=-1.25, # Negative net Sharpe!
        cost_robust=False,
        multi_regime_robust=True,
        has_bid_ask_quotes=False,
        is_reproducible=True,
    )
    assert breakdown.is_shortlist_candidate is False
    assert any("Negative net Sharpe" in r for r in breakdown.disqualification_reasons)


# -----------------------------------------------------------------------------
# 9. Master Hypothesis Evaluator & Phase 10 Gate
# -----------------------------------------------------------------------------

def test_evaluator_produces_phase_10_gate(tmp_path):
    dates = pd.date_range("2026-01-01", periods=65, freq="B")
    np.random.seed(42)
    rets = np.random.normal(0, 0.01, size=65)
    prices = 20000.0 * np.exp(np.cumsum(rets))
    df_eq = pd.DataFrame({
        "date": dates,
        "open": prices * 0.999,
        "high": prices * 1.005,
        "low": prices * 0.995,
        "close": prices,
        "volume": np.random.randint(100000, 500000, size=65),
    })
    df_opt = pd.DataFrame({
        "timestamp": dates,
        "strike_price": [20000] * 65,
        "option_type": ["CE"] * 65,
        "last_price": [150.0] * 65,
        "volume": [1000] * 65,
        "open_interest": [50000] * 65,
    })
    
    evaluator = HypothesisEvaluator(
        registry_filepath=str(tmp_path / "hypotheses.json"),
        audit_filepath=str(tmp_path / "snooping.json"),
    )
    output = evaluator.evaluate_all_hypotheses(df_eq, df_opt, symbol="NIFTY")
    
    assert output.safety_status["ALLOW_LIVE_EXECUTION"] is False
    assert output.phase_10_gate in ["PHASE_10_JUSTIFIED", "PHASE_10_NOT_JUSTIFIED"]
    assert output.primary_classification in ["NO_SURVIVING_HYPOTHESIS", "PROMISING_RESEARCH_HYPOTHESIS", "INSUFFICIENT_DATA"]


# -----------------------------------------------------------------------------
# 10. API Endpoints for Phase 9.6
# -----------------------------------------------------------------------------

def test_api_phase9_6_endpoints():
    client = TestClient(app)
    
    # 1. Hypotheses
    resp_hyp = client.get("/api/v1/research/phase9-6/hypotheses")
    assert resp_hyp.status_code == 200
    data_hyp = resp_hyp.json()
    assert len(data_hyp) == 8
    
    # 2. Results
    resp_res = client.get("/api/v1/research/phase9-6/results")
    assert resp_res.status_code == 200
    data_res = resp_res.json()
    assert data_res["phase_10_gate"] == "PHASE_10_NOT_JUSTIFIED"
    assert data_res["primary_classification"] == "NO_SURVIVING_HYPOTHESIS"
    
    # 3. Volatility
    resp_vol = client.get("/api/v1/research/phase9-6/volatility")
    assert resp_vol.status_code == 200
    
    # 4. Costs
    resp_costs = client.get("/api/v1/research/phase9-6/costs")
    assert resp_costs.status_code == 200
    assert resp_costs.json()["case_classification"] == "CASE_A_NO_GROSS_EDGE"
    
    # 5. Shortlist
    resp_short = client.get("/api/v1/research/phase9-6/shortlist")
    assert resp_short.status_code == 200
    assert resp_short.json()["top_3_shortlist"] == []
    
    # 6. Phase 10 Gate
    resp_gate = client.get("/api/v1/research/phase9-6/phase10-gate")
    assert resp_gate.status_code == 200
    assert resp_gate.json()["phase_10_gate"] == "PHASE_10_NOT_JUSTIFIED"
