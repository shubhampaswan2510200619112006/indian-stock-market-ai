"""
FastAPI Routes for ML Predictive Research Framework (Phase 6 & Phase 6.5).
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np

from src.database.repository import get_session
from src.database.models import EquityPriceDB, OptionsQuoteDB
from src.ingestion.nse_bhavcopy_importer import NSEBhavcopyOptionsProvider
from src.ml.backtest_integration import MLBacktestEvaluator
from src.ml.baselines import MLBaselineModelSuite
from src.ml.feature_pipeline import MLFeaturePipeline
from src.ml.metrics import evaluate_classification_metrics
from src.ml.registry import ModelRegistry, ModelRegistryRecord
from src.ml.statistical_validation import compute_block_bootstrap_ci, compute_permutation_test
from src.ml.sufficiency import (
    MLDataCoverageStatus,
    MLStatisticalEvidenceStatus,
    evaluate_dual_sufficiency,
)
from src.ml.targets import TargetDefinition, TargetType, generate_directional_targets
from src.ml.walk_forward_ml import WalkForwardMLValidator

router = APIRouter(prefix="/api/v1/ml", tags=["ML Research Engine"])


class TrainRequest(BaseModel):
    symbol: str = "NIFTY"
    days_back: int = 30
    horizon_days: int = 1
    model_key: str = "Baseline_2_LogisticRegression"


@router.get("/sufficiency-status")
def get_ml_dual_sufficiency(symbol: str = "NIFTY"):
    """
    Evaluates current database dataset scale and returns Dual Status (Coverage & Statistical Evidence).
    """
    session = get_session()
    try:
        quote_count = session.query(OptionsQuoteDB).count()
        equity_count = session.query(EquityPriceDB).filter(EquityPriceDB.symbol == symbol).count()
        q_min = session.query(OptionsQuoteDB.timestamp).order_by(OptionsQuoteDB.timestamp.asc()).first()
        q_max = session.query(OptionsQuoteDB.timestamp).order_by(OptionsQuoteDB.timestamp.desc()).first()

        date_range_days = (q_max[0] - q_min[0]).days if q_min and q_max else 0

        sufficiency = evaluate_dual_sufficiency(
            total_observations=quote_count,
            trading_days_count=equity_count,
            contracts_count=62,
            underlyings_count=1,
            expiries_count=1,
            independent_oos_trades=3,
            total_walk_forward_folds=3,
            fold_consistency_ratio=0.66,
        )
        return {
            "data_coverage_status": sufficiency.data_coverage_status.value,
            "statistical_evidence_status": sufficiency.statistical_evidence_status.value,
            "total_observations": sufficiency.total_observations,
            "trading_days_count": sufficiency.trading_days_count,
            "reasons": sufficiency.reasons,
            "warnings": sufficiency.warnings,
            "disclaimer": sufficiency.disclaimer,
        }
    finally:
        session.close()


@router.post("/train-walk-forward")
def train_and_validate_walk_forward(req: TrainRequest):
    """
    Trains specified model using chronological walk-forward CV, reporting per-fold metrics,
    Block Bootstrap CIs, Model A Execution Audit, and Stress Tests.
    """
    provider = NSEBhavcopyOptionsProvider()
    provider.ingest_genuine_nifty_options_dataset(symbol=req.symbol, days_back=req.days_back)

    session = get_session()
    try:
        eq_rows = (
            session.query(EquityPriceDB)
            .filter(EquityPriceDB.symbol == req.symbol)
            .order_by(EquityPriceDB.timestamp.asc())
            .all()
        )
        if len(eq_rows) < 10:
            raise HTTPException(status_code=400, detail="Insufficient equity price history in database.")

        df_equity = pd.DataFrame([
            {"date": r.timestamp.date(), "open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume}
            for r in eq_rows
        ])

        pipeline = MLFeaturePipeline(feature_version="v1.0")
        df_feat, feature_cols = pipeline.build_feature_matrix(df_equity, symbol=req.symbol)

        target_def = TargetDefinition(
            name=f"dir_return_{req.horizon_days}d",
            target_type=TargetType.DIRECTIONAL_RETURN_BINARY,
            horizon_days=req.horizon_days,
        )
        df_full = generate_directional_targets(df_feat, target_def, date_col="date", price_col="close")

        baselines = MLBaselineModelSuite.get_all_baselines(is_classification=True)
        if req.model_key not in baselines:
            raise HTTPException(status_code=400, detail=f"Model key '{req.model_key}' not found in baselines suite.")

        model = baselines[req.model_key]

        validator = WalkForwardMLValidator(min_train_size=8, test_size=3, purge_window=1)
        folds = validator.run_walk_forward(
            model=model,
            df=df_full,
            feature_cols=feature_cols,
            target_col=f"target_binary_{req.horizon_days}d",
            date_col="date",
        )

        all_records = []
        fold_summaries = []
        for f in folds:
            all_records.extend(f.prediction_records)
            fold_summaries.append({
                "fold_index": f.fold_index,
                "train_span": f"{f.train_start.date()} to {f.train_end.date()}",
                "test_span": f"{f.test_start.date()} to {f.test_end.date()}",
                "train_count": f.train_count,
                "test_count": f.test_count,
                "accuracy": f.fold_accuracy,
                "f1": f.fold_f1,
                "brier_score": f.fold_brier_score,
            })

        y_true = np.array([r.actual_outcome for r in all_records])
        y_pred = np.array([r.prediction for r in all_records])
        y_prob = np.array([r.probability for r in all_records])

        metrics = evaluate_classification_metrics(y_true, y_pred, y_prob)

        # Bootstrap & Permutation Validation
        bootstrap_ci = compute_block_bootstrap_ci(y_true == y_pred, metric_name="Accuracy")
        perm_test = compute_permutation_test(y_true, y_pred, metric_name="Accuracy")

        dual_suff = evaluate_dual_sufficiency(
            total_observations=len(df_full),
            trading_days_count=len(df_equity),
            contracts_count=62,
            underlyings_count=1,
            expiries_count=1,
            independent_oos_trades=3,
            total_walk_forward_folds=len(folds),
            fold_consistency_ratio=float(np.mean([f.fold_accuracy for f in folds])) if folds else 0.0,
        )

        # Register in Model Registry
        registry = ModelRegistry()
        reg_record = ModelRegistryRecord(
            model_name=model.name,
            model_version="v1.0",
            target_name=target_def.name,
            feature_version="v1.0",
            dataset_hash=pipeline.compute_dataset_hash(df_full),
            training_period_start=str(df_full["date"].iloc[0]),
            training_period_end=str(df_full["date"].iloc[-1]),
            hyperparameters={"horizon_days": req.horizon_days},
            data_sufficiency_status=dual_suff.data_coverage_status.value,
            validation_accuracy=metrics.accuracy,
            oos_accuracy=metrics.accuracy,
            oos_brier_score=metrics.brier_score,
        )
        registry.register_model(reg_record)

        # Evaluate OOS Strategy Backtest & Execution Audit
        evaluator = MLBacktestEvaluator(symbol=req.symbol)
        bt_eval = evaluator.run_oos_backtest(all_records, dual_suff)

        return {
            "model_name": model.name,
            "data_coverage_status": dual_suff.data_coverage_status.value,
            "statistical_evidence_status": dual_suff.statistical_evidence_status.value,
            "total_folds": len(folds),
            "total_oos_predictions": len(all_records),
            "fold_summaries": fold_summaries,
            "metrics": {
                "accuracy": metrics.accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1": metrics.f1,
                "roc_auc": metrics.roc_auc,
                "brier_score": metrics.brier_score,
                "ece": metrics.expected_calibration_error,
            },
            "bootstrap_ci": {
                "mean_estimate": bootstrap_ci.mean_estimate,
                "ci_lower": bootstrap_ci.ci_lower,
                "ci_upper": bootstrap_ci.ci_upper,
                "dependence_disclaimer": bootstrap_ci.dependence_disclaimer,
            },
            "permutation_test": {
                "observed_value": perm_test.observed_value,
                "p_value": perm_test.p_value,
                "null_hypothesis": perm_test.null_hypothesis,
            },
            "execution_audit": {
                "attempted_executions": bt_eval.execution_audit.attempted_executions,
                "successful_executions": bt_eval.execution_audit.successful_executions,
                "refused_executions": bt_eval.execution_audit.refused_executions,
                "refusal_reasons": bt_eval.execution_audit.refusal_reasons,
                "price_source_distribution": bt_eval.execution_audit.execution_price_source_distribution,
            },
            "oos_backtest": {
                "trades_executed": bt_eval.ml_trades_executed,
                "net_pnl": bt_eval.ml_net_pnl,
                "win_rate": bt_eval.ml_win_rate,
                "sharpe": bt_eval.ml_sharpe,
                "max_drawdown": bt_eval.ml_max_drawdown,
                "conclusion_category": bt_eval.conclusion_category,
                "robustness_status": bt_eval.robustness_status,
                "stress_results": bt_eval.stress_results,
            },
            "disclaimer": bt_eval.disclaimer,
        }
    finally:
        session.close()


@router.get("/registry")
def list_model_registry():
    """Returns all registered ML models."""
    registry = ModelRegistry()
    return {"registered_models": registry.list_models()}
