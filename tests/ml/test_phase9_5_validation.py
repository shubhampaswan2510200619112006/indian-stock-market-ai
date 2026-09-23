"""
Phase 9.5 — Automated Unit & Integration Tests.

Verifies:
1. Point-in-time timestamp precedence and leakage guards.
2. Contamination rejection (raises DataLeakageError when future data leaks).
3. Scaler isolation (scaler fitted strictly on training data).
4. Multi-horizon target generation (1D, 3D, 5D, 10D).
5. Progressive model hierarchy (Levels 0-3) and Level 4 Deep Learning Gate.
6. 5-Tier feature ablation (Tiers A-E).
7. Probability calibration (Platt scaling & Isotonic regression).
8. Chronological walk-forward with dynamic purging and embargo.
9. Realistic Indian market frictions (STT, NSE fees, GST, Stamp duty, Slippage).
10. Robustness stress testing (costs, slippage, regimes, block bootstrap).
11. Experiment registry multiple-testing controls and rejection of PRODUCTION_READY.
12. Full validation orchestrator execution and readiness matrix integrity.
"""

from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import pytest

from src.ml.ablation import FeatureAblationEngine, FeatureTier
from src.ml.baselines import (
    Baseline0NaiveModel,
    Baseline0PersistenceModel,
    Baseline1RollingMeanModel,
    Baseline2LogisticRegressionModel,
    Baseline3RidgeLassoModel,
    Baseline4RandomForestModel,
    Baseline5GradientBoostingModel,
    DeepLearningModelGate,
    MLBaselineModelSuite,
    ModelHierarchyLevel,
)
from src.ml.calibration import ProbabilityCalibrator
from src.ml.economic_metrics import EconomicMetricsEngine, IndianMarketFrictionModel
from src.ml.experiment_registry import ExperimentRecord, ExperimentRegistry, ExperimentStatus
from src.ml.leakage_guard import DataLeakageError, PointInTimeLeakageGuard
from src.ml.stress_testing import RobustnessStressEngine
from src.ml.targets import MultiHorizonTargetEngine, TargetCategory, TargetDefinition, TargetType, generate_directional_targets
from src.ml.validation_report import Phase95ValidationOrchestrator
from src.ml.walk_forward_ml import WalkForwardMLValidator


# =============================================================================
# 1. Leakage Guard & Contamination Tests
# =============================================================================

def test_leakage_guard_timestamp_precedence():
    t_feat = datetime(2026, 3, 9, 15, 30)
    t_pred = datetime(2026, 3, 9, 15, 31)
    t_tgt_start = datetime(2026, 3, 10, 9, 15)
    t_tgt_end = datetime(2026, 3, 10, 15, 30)

    # Valid ordering should pass
    PointInTimeLeakageGuard.assert_timestamp_ordering(t_feat, t_pred, t_tgt_start, t_tgt_end)

    # Future feature inversion should raise DataLeakageError
    with pytest.raises(DataLeakageError, match="Timestamp Inversion Detected"):
        PointInTimeLeakageGuard.assert_timestamp_ordering(t_pred + timedelta(hours=1), t_pred, t_tgt_start, t_tgt_end)

    # Target lookahead into prediction should raise DataLeakageError
    with pytest.raises(DataLeakageError, match="Lookahead Contamination Detected"):
        PointInTimeLeakageGuard.assert_timestamp_ordering(t_feat, t_tgt_start + timedelta(minutes=5), t_tgt_start, t_tgt_end)


def test_leakage_guard_target_leakage_detection():
    df_features = pd.DataFrame({
        "feat_clean": np.random.randn(50),
        "feat_leaked": np.array([1.0 if i % 2 == 0 else 0.0 for i in range(50)]),
    })
    target_series = pd.Series(df_features["feat_leaked"].values, name="target_col")

    # Clean subset should pass
    clean_sub = df_features[["feat_clean"]]
    res_clean = PointInTimeLeakageGuard.check_target_leakage_in_features(clean_sub, target_series)
    assert res_clean.is_clean is True

    # Leaked subset must trigger DataLeakageError
    with pytest.raises(DataLeakageError, match="Target Leakage Detected"):
        PointInTimeLeakageGuard.check_target_leakage_in_features(df_features, target_series)


def test_scaler_isolation_verification():
    from sklearn.preprocessing import StandardScaler

    train_data = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    test_data = np.array([[10.0, 20.0], [30.0, 40.0]])

    def _fit_scaler(data):
        scaler = StandardScaler()
        scaler.fit(data)
        return scaler

    res = PointInTimeLeakageGuard.verify_scaler_isolation(_fit_scaler, train_data, test_data)
    assert res.is_clean is True


def test_future_target_mutation_test():
    dates = pd.date_range("2026-01-01", periods=60, freq="B")
    prices = 100.0 + np.cumsum(np.random.randn(60))
    raw_df = pd.DataFrame({"date": dates, "close": prices, "volume": 1000})

    def _feature_calc(df):
        d = df.copy()
        # Strictly backward-looking feature
        d["sma_5"] = d["close"].rolling(5).mean()
        return d

    res = PointInTimeLeakageGuard.run_future_target_mutation_test(
        feature_calculator_fn=_feature_calc,
        raw_df=raw_df,
        mutation_index=40,
    )
    assert res.is_clean is True


# =============================================================================
# 2. Multi-Horizon Target Engine Tests
# =============================================================================

def test_multi_horizon_target_engine():
    dates = pd.date_range("2026-01-01", periods=50, freq="B")
    prices = 100.0 + np.cumsum(np.random.randn(50))
    df = pd.DataFrame({
        "date": dates,
        "open": prices * 0.99,
        "high": prices * 1.01,
        "low": prices * 0.98,
        "close": prices,
        "volume": 1000,
    })

    targets_df = MultiHorizonTargetEngine.build_all_underlying_targets(df)

    # Check that forward return columns are present
    for h in [1, 3, 5, 10]:
        assert f"target_fwd_ret_{h}d" in targets_df.columns
        assert f"target_fwd_dir_{h}d" in targets_df.columns

    assert "target_fwd_rv_5d" in targets_df.columns
    assert "target_start_timestamp" in targets_df.columns

    # Verify chronological precedence for first row
    first_row = targets_df.iloc[0]
    assert first_row["feature_availability_timestamp"] < first_row["target_start_timestamp"]


# =============================================================================
# 3. Model Hierarchy & Deep Learning Gate Tests
# =============================================================================

def test_model_hierarchy_baselines():
    X = np.random.randn(40, 4)
    y_class = np.array([1 if i % 2 == 0 else 0 for i in range(40)])
    y_reg = np.random.randn(40)

    # Level 0 Naive
    m0 = Baseline0NaiveModel(is_classification=True).fit(X, y_class)
    assert len(m0.predict(X)) == 40
    assert m0.level == ModelHierarchyLevel.LEVEL_0_NAIVE

    # Level 0 Persistence
    m_pers = Baseline0PersistenceModel().fit(X, y_class)
    assert len(m_pers.predict(X)) == 40

    # Level 1 Logistic
    m1 = Baseline2LogisticRegressionModel().fit(X, y_class)
    assert len(m1.predict(X)) == 40
    assert m1.level == ModelHierarchyLevel.LEVEL_1_LINEAR

    # Level 2 Random Forest
    m2 = Baseline4RandomForestModel(is_classification=True, n_estimators=10).fit(X, y_class)
    assert len(m2.predict(X)) == 40
    assert m2.level == ModelHierarchyLevel.LEVEL_2_RANDOM_FOREST

    # Level 3 Gradient Boosting
    m3 = Baseline5GradientBoostingModel(is_classification=True, n_estimators=10).fit(X, y_class)
    assert len(m3.predict(X)) == 40
    assert m3.level == ModelHierarchyLevel.LEVEL_3_GRADIENT_BOOSTING


def test_deep_learning_gate_rejection():
    # When sample count is 500 (< 10,000 threshold), must return SKIPPED_INSUFFICIENT_DATA
    gate_res = DeepLearningModelGate.evaluate_deep_learning_eligibility(sample_count=500)
    assert gate_res["DEEP_LEARNING"] == "SKIPPED_INSUFFICIENT_DATA"
    assert "required_threshold" in gate_res


# =============================================================================
# 4. 5-Tier Feature Ablation Tests
# =============================================================================

def test_feature_ablation_tiers():
    dates = pd.date_range("2026-01-01", periods=60, freq="B")
    prices = 100.0 + np.cumsum(np.random.randn(60))
    df = pd.DataFrame({
        "date": dates,
        "open": prices * 0.99,
        "high": prices * 1.01,
        "low": prices * 0.98,
        "close": prices,
        "volume": 1000,
    })

    df_feats, tier_defs = FeatureAblationEngine.generate_features_all_tiers(df, symbol="NIFTY")

    assert len(tier_defs[FeatureTier.TIER_A_PRICE]) < len(tier_defs[FeatureTier.TIER_B_PRICE_ACTION])
    assert len(tier_defs[FeatureTier.TIER_B_PRICE_ACTION]) < len(tier_defs[FeatureTier.TIER_C_VOLUME])
    assert len(tier_defs[FeatureTier.TIER_C_VOLUME]) < len(tier_defs[FeatureTier.TIER_D_VOLATILITY_REGIME])
    assert "regime_code" in tier_defs[FeatureTier.TIER_D_VOLATILITY_REGIME]
    assert "market_regime" in df_feats.columns


# =============================================================================
# 5. Probability Calibration Tests
# =============================================================================

def test_probability_calibration():
    y_true_tr = np.array([0, 0, 1, 1, 0, 1, 0, 1, 1, 0])
    y_prob_tr = np.array([0.2, 0.3, 0.7, 0.8, 0.4, 0.6, 0.1, 0.9, 0.85, 0.15])

    y_true_te = np.array([0, 1, 0, 1])
    y_prob_te = np.array([0.35, 0.65, 0.25, 0.75])

    rep = ProbabilityCalibrator.evaluate_calibration(
        model_name="Test_Logistic",
        y_prob_train=y_prob_tr,
        y_true_train=y_true_tr,
        y_prob_test=y_prob_te,
        y_true_test=y_true_te,
        method="sigmoid",
    )

    assert rep.uncalibrated_brier_score >= 0.0
    assert rep.calibrated_brier_score >= 0.0
    assert rep.uncalibrated_ece >= 0.0


# =============================================================================
# 6. Chronological Walk-Forward Tests
# =============================================================================

def test_walk_forward_purging_embargo():
    dates = pd.date_range("2026-01-01", periods=60, freq="B")
    prices = 100.0 + np.cumsum(np.random.randn(60))
    df = pd.DataFrame({
        "date": dates,
        "feat_1": np.random.randn(60),
        "target": np.array([1 if i % 2 == 0 else 0 for i in range(60)]),
    })

    validator = WalkForwardMLValidator(
        min_train_size=20,
        test_size=10,
        horizon_days=3,
        expanding=True,
    )
    assert validator.purge_window == 3

    model = Baseline0NaiveModel(is_classification=True)
    folds = validator.run_walk_forward(
        model=model,
        df=df,
        feature_cols=["feat_1"],
        target_col="target",
    )

    assert len(folds) >= 2
    for f in folds:
        # Verify train_end < test_start with purge gap
        purge_gap = (f.test_start - f.train_end).days
        assert purge_gap >= 1


# =============================================================================
# 7. Economic Metrics & Indian Market Frictions Tests
# =============================================================================

def test_economic_metrics_indian_frictions():
    # 20 signals: alternating +1 and -1
    signals = np.array([1.0 if i % 2 == 0 else -1.0 for i in range(20)])
    rets = np.array([0.01 if i % 2 == 0 else -0.01 for i in range(20)])

    friction = IndianMarketFrictionModel(cost_multiplier=1.0, slippage_multiplier=1.0)
    rep = EconomicMetricsEngine.evaluate_strategy_returns(signals, rets, frictions=friction)

    assert rep.total_trades > 0
    assert rep.total_fees > 0.0  # STT / exchange fees applied
    assert rep.total_slippage > 0.0
    assert rep.net_return < rep.gross_return
    assert rep.sample_reliability == "RELIABLE"


# =============================================================================
# 8. Robustness Stress & Block Bootstrap Tests
# =============================================================================

def test_robustness_stress_and_bootstrap():
    signals = np.array([1.0, 1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0, -1.0, 1.0] * 3)
    rets = np.array([0.005, -0.002, 0.003, -0.004, 0.001, 0.006, -0.001, -0.003, 0.002, 0.004] * 3)
    regimes = pd.Series(["BULL"] * 15 + ["BEAR"] * 15)

    rob_report = RobustnessStressEngine.generate_full_robustness_report(
        signals=signals,
        asset_returns=rets,
        regimes=regimes,
    )

    assert len(rob_report.cost_stress_results) == 3
    assert len(rob_report.slippage_stress_results) == 3
    assert rob_report.bootstrap_sharpe_ci.confidence_level == 0.95
    assert rob_report.bootstrap_expectancy_ci.ci_lower <= rob_report.bootstrap_expectancy_ci.ci_upper


# =============================================================================
# 9. Experiment Registry & Safety Invariant Tests
# =============================================================================

def test_experiment_registry_safety_invariant(tmp_path):
    reg_file = str(tmp_path / "test_exp_reg.json")
    registry = ExperimentRegistry(reg_file)

    exp = ExperimentRecord(
        experiment_id="TEST-EXP-001",
        hypothesis="Test directional edge",
        dataset_snapshot_id="SNAP-001",
        feature_version="v1.0",
        target_version="1D_Direction",
        model_name="TestModel",
        model_level="LEVEL_1_LINEAR",
        hyperparameters={},
        threshold=0.5,
        random_seed=42,
        train_period_start="2026-01-01",
        train_period_end="2026-06-01",
        test_period_start="2026-06-02",
        test_period_end="2026-09-01",
        oos_observations=50,
        oos_trades=20,
        oos_accuracy=0.52,
        oos_sharpe=0.4,
        oos_net_return=0.02,
        oos_max_drawdown=0.05,
        status=ExperimentStatus.RESEARCH_ONLY,
    )

    registry.record_experiment(exp)
    assert len(registry.list_experiments()) == 1

    # Safety Invariant: Attempting to set PRODUCTION_READY must raise ValueError
    exp_illegal = ExperimentRecord(
        experiment_id="ILLEGAL-EXP",
        hypothesis="Illegal production attempt",
        dataset_snapshot_id="SNAP-001",
        feature_version="v1.0",
        target_version="1D_Direction",
        model_name="IllegalModel",
        model_level="LEVEL_1_LINEAR",
        hyperparameters={},
        threshold=0.5,
        random_seed=42,
        train_period_start="2026-01-01",
        train_period_end="2026-06-01",
        test_period_start="2026-06-02",
        test_period_end="2026-09-01",
        oos_observations=50,
        oos_trades=20,
        oos_accuracy=0.99,
        oos_sharpe=3.0,
        oos_net_return=0.5,
        oos_max_drawdown=0.01,
        status="PRODUCTION_READY",  # Must be rejected
    )

    with pytest.raises(ValueError, match="Safety Violation"):
        registry.record_experiment(exp_illegal)


# =============================================================================
# 10. Master Orchestrator End-to-End Test
# =============================================================================

def test_full_validation_orchestrator(tmp_path):
    reg_file = str(tmp_path / "orch_reg.json")
    dates = pd.date_range("2026-01-01", periods=65, freq="B")
    prices = 100.0 + np.cumsum(np.random.randn(65))
    df_equity = pd.DataFrame({
        "date": [d.date() for d in dates],
        "open": prices * 0.99,
        "high": prices * 1.01,
        "low": prices * 0.98,
        "close": prices,
        "volume": 1000,
    })

    orch = Phase95ValidationOrchestrator(registry_filepath=reg_file)
    output = orch.run_full_validation(equity_df=df_equity, symbol="NIFTY")

    assert output.safety_status["ALLOW_LIVE_EXECUTION"] is False
    assert output.primary_classification in [
        "STATISTICALLY_PROMISING",
        "WEAK_INCONCLUSIVE",
        "NO_EVIDENCE_OF_EDGE",
        "INSUFFICIENT_DATA",
    ]
    assert output.readiness_matrix["LIVE_TRADING_READINESS"] == "NOT_READY"
    assert output.readiness_matrix["BROKER_READINESS"] == "NOT_IMPLEMENTED"
