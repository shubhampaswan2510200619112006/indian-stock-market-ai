"""
Phase 9.5 — Research & Statistical Validation API Routes.

Exposes endpoints for:
- Datasets & Snapshots
- Experiment Registry & Multiple-Testing Audit
- Progressive Model Hierarchy (Levels 0-4)
- 5-Tier Feature Ablation
- Chronological Walk-Forward
- Robustness & Stress Testing
- Market Regimes Breakdown
- Block Bootstrap 95% Confidence Intervals
- Final Research Classification & Readiness Matrix
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
import numpy as np
import pandas as pd

from src.database.repository import get_session
from src.database.models import EquityPriceDB, OptionsContractDB, OptionsQuoteDB
from src.ml.ablation import FeatureAblationEngine, FeatureTier
from src.ml.baselines import MLBaselineModelSuite
from src.ml.experiment_registry import ExperimentRegistry
from src.ml.validation_report import Phase95ValidationOrchestrator

router = APIRouter(prefix="/api/v1/research", tags=["Phase 9.5 Statistical Research"])


def _load_validation_data(symbol: str = "NIFTY") -> Tuple[pd.DataFrame, pd.DataFrame]:
    session = get_session()
    try:
        eq_rows = (
            session.query(EquityPriceDB)
            .filter(EquityPriceDB.symbol == symbol)
            .order_by(EquityPriceDB.date.asc())
            .all()
        )
        opt_rows = (
            session.query(OptionsQuoteDB, OptionsContractDB)
            .join(OptionsContractDB, OptionsQuoteDB.contract_id == OptionsContractDB.id)
            .order_by(OptionsQuoteDB.timestamp.asc())
            .all()
        )

        df_eq = pd.DataFrame([
            {
                "date": r.date,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in eq_rows
        ])

        df_opt = pd.DataFrame([
            {
                "timestamp": q.timestamp,
                "strike_price": c.strike_price,
                "option_type": c.option_type,
                "last_price": q.last_price,
                "volume": q.volume,
                "open_interest": q.open_interest,
            }
            for q, c in opt_rows
        ]) if opt_rows else pd.DataFrame()

        return df_eq, df_opt
    finally:
        session.close()


@router.get("/datasets")
def get_research_datasets(symbol: str = "NIFTY"):
    df_eq, df_opt = _load_validation_data(symbol)
    return {
        "symbol": symbol,
        "trading_sessions": len(df_eq),
        "option_observations": len(df_opt),
        "bid_ask_coverage_pct": 0.0,
        "options_execution_status": "INSUFFICIENT_DATA",
        "equity_direction_status": "SUFFICIENT" if len(df_eq) >= 60 else "INSUFFICIENT",
    }


@router.get("/experiments")
def get_experiment_registry():
    registry = ExperimentRegistry()
    return {
        "experiments": registry.list_experiments(),
        "multiple_testing_audit": registry.audit_multiple_testing().__dict__,
    }


@router.get("/models")
def get_model_hierarchy():
    models = MLBaselineModelSuite.get_all_baselines(is_classification=True)
    return {
        "model_hierarchy": [
            {"name": m.name, "level": m.level.value} for m in models.values()
        ],
        "level_4_deep_learning_status": "SKIPPED_INSUFFICIENT_DATA",
    }


@router.get("/walk-forward")
def get_walk_forward_evaluation(symbol: str = "NIFTY"):
    df_eq, df_opt = _load_validation_data(symbol)
    if len(df_eq) < 30:
        raise HTTPException(status_code=400, detail="Insufficient equity data.")
    orch = Phase95ValidationOrchestrator()
    rep = orch.run_full_validation(df_eq, df_opt, symbol=symbol)
    return rep.walk_forward_summary


@router.get("/ablation")
def get_feature_ablation(symbol: str = "NIFTY"):
    df_eq, df_opt = _load_validation_data(symbol)
    if len(df_eq) < 30:
        raise HTTPException(status_code=400, detail="Insufficient data for ablation.")
    orch = Phase95ValidationOrchestrator()
    rep = orch.run_full_validation(df_eq, df_opt, symbol=symbol)
    return rep.ablation_results


@router.get("/strategies")
def get_strategy_evaluation(symbol: str = "NIFTY"):
    df_eq, df_opt = _load_validation_data(symbol)
    orch = Phase95ValidationOrchestrator()
    rep = orch.run_full_validation(df_eq, df_opt, symbol=symbol)
    return {
        "strategy_validation": rep.strategy_validation,
        "ml_incremental_value": rep.ml_incremental_value,
    }


@router.get("/robustness")
def get_robustness_stress(symbol: str = "NIFTY"):
    df_eq, df_opt = _load_validation_data(symbol)
    orch = Phase95ValidationOrchestrator()
    rep = orch.run_full_validation(df_eq, df_opt, symbol=symbol)
    return rep.robustness_summary


@router.get("/regimes")
def get_regime_breakdown(symbol: str = "NIFTY"):
    df_eq, df_opt = _load_validation_data(symbol)
    orch = Phase95ValidationOrchestrator()
    rep = orch.run_full_validation(df_eq, df_opt, symbol=symbol)
    return {
        "regime_breakdowns": rep.robustness_summary.get("regime_breakdowns", []),
        "dominant_regime_dependence": rep.robustness_summary.get("dominant_regime_dependence", "UNKNOWN"),
    }


@router.get("/bootstrap")
def get_bootstrap_confidence_intervals(symbol: str = "NIFTY"):
    df_eq, df_opt = _load_validation_data(symbol)
    orch = Phase95ValidationOrchestrator()
    rep = orch.run_full_validation(df_eq, df_opt, symbol=symbol)
    return rep.bootstrap_results


@router.get("/readiness")
def get_final_readiness(symbol: str = "NIFTY"):
    df_eq, df_opt = _load_validation_data(symbol)
    orch = Phase95ValidationOrchestrator()
    rep = orch.run_full_validation(df_eq, df_opt, symbol=symbol)
    return {
        "primary_classification": rep.primary_classification,
        "primary_classification_reason": rep.primary_classification_reason,
        "readiness_matrix": rep.readiness_matrix,
        "safety_status": rep.safety_status,
    }


# ============================================================================
# PHASE 9.6 — RESEARCH RECALIBRATION & EDGE DISCOVERY ENDPOINTS
# ============================================================================

@router.get("/phase9-6/hypotheses")
def get_phase9_6_hypotheses():
    """List all 8 pre-registered research hypotheses and their frozen criteria."""
    import json
    from pathlib import Path
    p = Path("data/research_hypothesis_registry.json")
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    from src.research.hypotheses import get_all_registered_hypotheses
    return [h.to_dict() for h in get_all_registered_hypotheses()]


@router.get("/phase9-6/results")
def get_phase9_6_results():
    """Return the complete Phase 9.6 research recalibration results."""
    import json
    from pathlib import Path
    p = Path("data/phase9_6_research_validation.json")
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Phase 9.6 validation results not yet generated.")


@router.get("/phase9-6/volatility")
def get_phase9_6_volatility():
    """Return H001 Volatility Persistence evaluation and forecast comparisons."""
    import json
    from pathlib import Path
    p = Path("data/phase9_6_research_validation.json")
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("volatility_research", {})
    raise HTTPException(status_code=404, detail="Phase 9.6 results not found.")


@router.get("/phase9-6/costs")
def get_phase9_6_costs():
    """Return Cost Decomposition and Case A/B/C classification."""
    import json
    from pathlib import Path
    p = Path("data/phase9_6_research_validation.json")
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            cd = data.get("cost_decomposition", {})
            return {
                "cost_decomposition": cd,
                "case_classification": cd.get("case_classification") or cd.get("failure_mode"),
                "turnover_friction": data.get("turnover_analysis", {}),
            }
    raise HTTPException(status_code=404, detail="Phase 9.6 results not found.")



@router.get("/phase9-6/shortlist")
def get_phase9_6_shortlist():
    """Return the 100-point research scores and Top 3 candidate shortlist."""
    import json
    from pathlib import Path
    p = Path("data/phase9_6_research_validation.json")
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "research_scores": data.get("research_scores", []),
                "top_3_shortlist": data.get("top_3_shortlist", []),
                "primary_classification": data.get("primary_classification"),
            }
    raise HTTPException(status_code=404, detail="Phase 9.6 results not found.")


@router.get("/phase9-6/phase10-gate")
def get_phase9_6_phase10_gate():
    """Return the authoritative Phase 10 paper trading readiness decision."""
    import json
    from pathlib import Path
    p = Path("data/phase9_6_research_validation.json")
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "phase_10_gate": data.get("phase_10_gate"),
                "phase_10_gate_reason": data.get("phase_10_gate_reason"),
                "safety_status": data.get("safety_status"),
            }
    raise HTTPException(status_code=404, detail="Phase 9.6 results not found.")

