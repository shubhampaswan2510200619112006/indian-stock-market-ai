"""
Phase 9.6 — Research Hypothesis Registry.

Pre-registers all research hypotheses with frozen evaluation criteria BEFORE evaluation:
- Freezes primary metric, secondary metrics, minimum sample size, success/failure thresholds.
- Enforces distinction: PRE_REGISTERED_CONFIRMATORY vs EXPLORATORY.
- Immutability: Modifications after result observation are strictly prohibited (requires a new ID).
- Avoids retrospective threshold tuning, parameter search, and cherry-picking.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
import os
from typing import Any, Dict, List, Optional


class HypothesisType(str, Enum):
    PRE_REGISTERED_CONFIRMATORY = "PRE_REGISTERED_CONFIRMATORY"
    EXPLORATORY = "EXPLORATORY"


class HypothesisStatus(str, Enum):
    REGISTERED = "REGISTERED"
    EVALUATED = "EVALUATED"
    SURVIVED = "SURVIVED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class ResearchHypothesis:
    hypothesis_id: str
    research_question: str
    economic_rationale: str
    hypothesis_type: HypothesisType
    target: str
    feature_group: str
    instrument_scope: str
    holding_period: str
    entry_rule: str
    exit_rule: str
    cost_assumption: str
    slippage_assumption: str
    validation_method: str
    primary_metric: str
    secondary_metrics: List[str]
    minimum_sample_requirement: int
    success_criteria: str
    failure_criteria: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: HypothesisStatus = HypothesisStatus.REGISTERED
    status_reason: str = ""
    primary_metric_result: Optional[float] = None
    oos_samples_evaluated: int = 0
    oos_trades_evaluated: int = 0
    is_frozen: bool = True
    evidence_notes: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_pre_registered(self) -> bool:
        return self.hypothesis_type == HypothesisType.PRE_REGISTERED_CONFIRMATORY

    @property
    def min_sample_size(self) -> int:
        return self.minimum_sample_requirement

    @property
    def statutory_fees_bps(self) -> float:
        return 5.0

    @property
    def slippage_bps(self) -> float:
        return 5.0

    @property
    def min_oos_improvement(self) -> float:
        return 0.02

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["hypothesis_type"] = self.hypothesis_type.value if hasattr(self.hypothesis_type, "value") else str(self.hypothesis_type)
        d["status"] = self.status.value if hasattr(self.status, "value") else str(self.status)
        d["is_pre_registered"] = self.is_pre_registered
        d["min_sample_size"] = self.min_sample_size
        d["min_oos_improvement"] = self.min_oos_improvement
        return d



class HypothesisRegistry:
    """
    Registry for tracking pre-registered research hypotheses.
    """

    def __init__(self, filepath: str = "./data/research_hypothesis_registry.json"):
        self.filepath = filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            self._save([])

    def _load(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, data: List[Dict[str, Any]]) -> None:
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def register(self, hypothesis: ResearchHypothesis) -> None:
        records = self._load()
        for r in records:
            if r["hypothesis_id"] == hypothesis.hypothesis_id:
                if r.get("is_frozen", True) and r.get("status") != HypothesisStatus.REGISTERED.value:
                    raise ValueError(
                        f"Cannot modify frozen hypothesis {hypothesis.hypothesis_id} after evaluation! "
                        f"Create a new hypothesis ID for exploratory or altered parameters."
                    )
        # Update or append
        records = [r for r in records if r["hypothesis_id"] != hypothesis.hypothesis_id]
        h_dict = asdict(hypothesis)
        h_dict["hypothesis_type"] = hypothesis.hypothesis_type.value
        h_dict["status"] = hypothesis.status.value
        records.append(h_dict)
        self._save(records)

    def update_evaluation(
        self,
        hypothesis_id: str,
        status: HypothesisStatus,
        status_reason: str,
        primary_metric_result: float,
        oos_samples: int,
        oos_trades: int,
        evidence_notes: Optional[Dict[str, Any]] = None,
    ) -> None:
        records = self._load()
        found = False
        for r in records:
            if r["hypothesis_id"] == hypothesis_id:
                r["status"] = status.value
                r["status_reason"] = status_reason
                r["primary_metric_result"] = primary_metric_result
                r["oos_samples_evaluated"] = oos_samples
                r["oos_trades_evaluated"] = oos_trades
                r["is_frozen"] = True
                if evidence_notes:
                    r["evidence_notes"] = evidence_notes
                found = True
                break
        if not found:
            raise KeyError(f"Hypothesis {hypothesis_id} not registered.")
        self._save(records)

    def get(self, hypothesis_id: str) -> Optional[Dict[str, Any]]:
        for r in self._load():
            if r["hypothesis_id"] == hypothesis_id:
                return r
        return None

    def list_all(self) -> List[Dict[str, Any]]:
        return self._load()

    def get_audit_summary(self) -> Dict[str, Any]:
        records = self._load()
        total = len(records)
        survived = sum(1 for r in records if r.get("status") == HypothesisStatus.SURVIVED.value)
        rejected = sum(1 for r in records if r.get("status") == HypothesisStatus.REJECTED.value)
        inconclusive = sum(1 for r in records if r.get("status") == HypothesisStatus.INCONCLUSIVE.value)
        registered = sum(1 for r in records if r.get("status") == HypothesisStatus.REGISTERED.value)
        return {
            "total_hypotheses_registered": total,
            "total_hypotheses_evaluated": total - registered,
            "total_hypotheses_surviving": survived,
            "total_hypotheses_rejected": rejected,
            "total_hypotheses_inconclusive": inconclusive,
        }


def get_default_phase9_6_hypotheses() -> List[ResearchHypothesis]:
    """
    Returns the initial pre-registered set of Phase 9.6 research hypotheses.
    All criteria are frozen prior to running any evaluation.
    """
    return [
        ResearchHypothesis(
            hypothesis_id="H001_VOLATILITY_PERSISTENCE",
            research_question="Does realized volatility exhibit predictable out-of-sample persistence beating EWMA and rolling mean baselines, and does this predictability yield economic value?",
            economic_rationale="Volatility clusters in financial markets due to persistent uncertainty, order-flow autocorrelation, and institutional risk-budget adjustments.",
            hypothesis_type=HypothesisType.PRE_REGISTERED_CONFIRMATORY,
            target="target_fwd_rv_5d",
            feature_group="F4_Volatility",
            instrument_scope="NIFTY",
            holding_period="5_sessions",
            entry_rule="Forecasted RV > 90th percentile historical RV",
            exit_rule="Forecasted RV reverts to median or 5 sessions elapse",
            cost_assumption="5 bps roundtrip statutory fees",
            slippage_assumption="5 bps half-spread",
            validation_method="Chronological Walk-Forward (expanding, purge=5)",
            primary_metric="RMSE vs EWMA Baseline (Lower is better)",
            secondary_metrics=["MAE", "Directional Volatility Accuracy", "Rank Correlation"],
            minimum_sample_requirement=60,
            success_criteria="RMSE < EWMA RMSE by at least 5% AND directional volatility accuracy > 55%",
            failure_criteria="RMSE >= EWMA RMSE OR directional volatility accuracy <= 50%",
        ),
        ResearchHypothesis(
            hypothesis_id="H002_TARGET_REFORMULATION_MULTI_DAY",
            research_question="Does predicting 3D or 5D multi-session direction or risk-adjusted return (Return / ATR) achieve higher OOS directional accuracy than noisy 1D direction?",
            economic_rationale="1-day price movements in liquid benchmark indices are dominated by microstructure noise; trends and institutional rebalancing manifest over multi-day horizons.",
            hypothesis_type=HypothesisType.PRE_REGISTERED_CONFIRMATORY,
            target="target_fwd_dir_5d",
            feature_group="F2_Price_Action",
            instrument_scope="NIFTY",
            holding_period="5_sessions",
            entry_rule="Model probability > 0.50 (long) or < 0.50 (short)",
            exit_rule="5 trading sessions elapse",
            cost_assumption="5 bps roundtrip statutory fees",
            slippage_assumption="5 bps half-spread",
            validation_method="Chronological Walk-Forward (expanding, purge=5)",
            primary_metric="OOS Directional Accuracy",
            secondary_metrics=["Net Sharpe Ratio", "Brier Score", "Expectancy"],
            minimum_sample_requirement=60,
            success_criteria="OOS Accuracy > 54.0% AND Net Sharpe > 0.50 after costs",
            failure_criteria="OOS Accuracy <= 50.0% OR Net Sharpe <= 0.0",
        ),
        ResearchHypothesis(
            hypothesis_id="H003_REGIME_CONDITIONED_VOLATILITY",
            research_question="Is the absence of edge in Phase 9.5 caused by regime mismatch (e.g. models failing in SIDEWAYS regimes while maintaining edge in HIGH_VOLATILITY regimes)?",
            economic_rationale="Directional momentum and breakout models perform poorly in sideways range-bound markets, but can extract edge during persistent trend or high-volatility shocks.",
            hypothesis_type=HypothesisType.PRE_REGISTERED_CONFIRMATORY,
            target="target_fwd_dir_1d",
            feature_group="F5_Regime",
            instrument_scope="NIFTY",
            holding_period="1_session",
            entry_rule="Signal generated only when market regime is BULL, BEAR, or HIGH_VOLATILITY (filter out SIDEWAYS)",
            exit_rule="Next session close",
            cost_assumption="5 bps roundtrip statutory fees",
            slippage_assumption="5 bps half-spread",
            validation_method="Chronological Walk-Forward across 6 regimes",
            primary_metric="Regime-Conditioned OOS Accuracy & Net Sharpe",
            secondary_metrics=["Win Rate in Non-Sideways Regimes", "Expectancy"],
            minimum_sample_requirement=20,  # per non-sideways regime
            success_criteria="Non-sideways OOS Accuracy > 54.0% AND Net Sharpe > 0.50",
            failure_criteria="Non-sideways OOS Accuracy <= 50.0% OR Net Sharpe <= 0.0 across all regimes",
        ),
        ResearchHypothesis(
            hypothesis_id="H004_HIGH_CONFIDENCE_THRESHOLD",
            research_question="Does restricting trade execution to high-conviction probability buckets (e.g. P > 0.60 or P < 0.40) improve trade expectancy and reduce turnover friction?",
            economic_rationale="Marginal predictions (P ~ 0.51) incur full transaction costs with negligible alpha; high conviction trades filter out noise.",
            hypothesis_type=HypothesisType.PRE_REGISTERED_CONFIRMATORY,
            target="target_fwd_dir_1d",
            feature_group="F3_Volume",
            instrument_scope="NIFTY",
            holding_period="1_session",
            entry_rule="Long if P >= 0.60; Short if P <= 0.40; Cash if 0.40 < P < 0.60",
            exit_rule="Next session close",
            cost_assumption="5 bps roundtrip statutory fees",
            slippage_assumption="5 bps half-spread",
            validation_method="Chronological Walk-Forward",
            primary_metric="High-Conviction Trade Expectancy & Win Rate",
            secondary_metrics=["Total Trades", "Turnover Reduction %", "Net Return"],
            minimum_sample_requirement=15,  # minimum high-conviction trades
            success_criteria="Win Rate > 55.0% AND Net Expectancy > 0.10% per trade (with >= 15 trades)",
            failure_criteria="Win Rate <= 50.0% OR Trade Count < 10 (INSUFFICIENT_SAMPLE)",
        ),
        ResearchHypothesis(
            hypothesis_id="H005_LONG_SHORT_ASYMMETRY",
            research_question="Does the system exhibit material long/short performance asymmetry, and does a Long-Only directional model outperform symmetric long-short trading?",
            economic_rationale="Secular upward equity drift and short-sale frictions create structural asymmetry between long and short positions in index products.",
            hypothesis_type=HypothesisType.PRE_REGISTERED_CONFIRMATORY,
            target="target_fwd_dir_1d",
            feature_group="F1_Price",
            instrument_scope="NIFTY",
            holding_period="1_session",
            entry_rule="Long signals only (Short signals mapped to 100% Cash)",
            exit_rule="Next session close",
            cost_assumption="5 bps roundtrip statutory fees",
            slippage_assumption="5 bps half-spread",
            validation_method="Chronological Walk-Forward",
            primary_metric="Long-Only Net Sharpe vs Symmetric Sharpe",
            secondary_metrics=["Win Rate Long vs Win Rate Short", "Max Drawdown"],
            minimum_sample_requirement=30,
            success_criteria="Long-Only Net Sharpe > Symmetric Net Sharpe by at least 1.0 AND Long Sharpe > 0.0",
            failure_criteria="Long-Only Net Sharpe <= 0.0",
        ),
        ResearchHypothesis(
            hypothesis_id="H006_HOLDING_PERIOD_SWING",
            research_question="Does extending holding periods from daily (1 session) to swing (3 to 5 sessions) reduce transaction fee drag sufficiently to achieve positive net expectancy?",
            economic_rationale="Transaction costs and slippage consume 10-15 bps per roundtrip trade; longer holding periods reduce turnover friction per unit of expected price move.",
            hypothesis_type=HypothesisType.PRE_REGISTERED_CONFIRMATORY,
            target="target_fwd_ret_5d",
            feature_group="F2_Price_Action",
            instrument_scope="NIFTY",
            holding_period="5_sessions",
            entry_rule="Signal at T, held for 5 sessions",
            exit_rule="Exit at T+5 close",
            cost_assumption="5 bps roundtrip statutory fees",
            slippage_assumption="5 bps half-spread",
            validation_method="Chronological Walk-Forward (purge=5)",
            primary_metric="Net Compounded Return & Sharpe at 5D vs 1D",
            secondary_metrics=["Turnover %", "Cost Drag Reduction"],
            minimum_sample_requirement=40,
            success_criteria="Net Sharpe at 5D > Net Sharpe at 1D AND Net Sharpe > 0.0",
            failure_criteria="Net Sharpe at 5D <= 0.0",
        ),
        ResearchHypothesis(
            hypothesis_id="H007_OPTIONS_OI_PCR_ALPHA",
            research_question="Do aggregated options market indicators (Put-Call Ratio, Open Interest changes, ATM IV) provide incremental out-of-sample predictive information over price action alone?",
            economic_rationale="Informed derivatives market participants position in options contracts prior to major index price adjustments.",
            hypothesis_type=HypothesisType.PRE_REGISTERED_CONFIRMATORY,
            target="target_fwd_dir_1d",
            feature_group="F6_Options",
            instrument_scope="NIFTY",
            holding_period="1_session",
            entry_rule="Model trained with Tier E (Price + Action + Volume + Regime + Options)",
            exit_rule="Next session close",
            cost_assumption="5 bps roundtrip statutory fees",
            slippage_assumption="5 bps half-spread",
            validation_method="Chronological Walk-Forward (Tier E vs Tier D ablation)",
            primary_metric="Incremental OOS Accuracy (Tier E vs Tier D)",
            secondary_metrics=["Net Sharpe Incremental Delta", "Brier Score Delta"],
            minimum_sample_requirement=60,
            success_criteria="Tier E Accuracy > Tier D Accuracy by at least 2.0% (p < 0.05)",
            failure_criteria="Tier E Accuracy <= Tier D Accuracy",
        ),
        ResearchHypothesis(
            hypothesis_id="H008_VOLATILITY_STRATEGY_MAPPING",
            research_question="Does mapping volatility forecasts to defined-risk options structures (Straddles in high vol, Iron Condors in low vol) outperform naive directional mapping in LTP research?",
            economic_rationale="Options strategies profit directly from volatility expansion or theta decay; forcing directional bets on volatility-derived signals is sub-optimal.",
            hypothesis_type=HypothesisType.PRE_REGISTERED_CONFIRMATORY,
            target="target_fwd_rv_5d",
            feature_group="F4_Volatility",
            instrument_scope="NIFTY",
            holding_period="5_sessions",
            entry_rule="High Vol Forecast -> Long Straddle; Low Vol Forecast -> Defined-Risk Iron Condor",
            exit_rule="5 trading sessions elapse or expiry",
            cost_assumption="5 bps roundtrip fees (LTP Research)",
            slippage_assumption="Execution data blocked; LTP research mark-to-market only",
            validation_method="Chronological Options LTP Research Audit",
            primary_metric="LTP Strategy Net PnL & Profit Factor",
            secondary_metrics=["Max Drawdown", "Win Rate", "Net Greeks Exposure"],
            minimum_sample_requirement=30,
            success_criteria="LTP Strategy Profit Factor > 1.20 with zero execution validity claims",
            failure_criteria="Profit Factor <= 1.0 OR Execution Data Disclaimers Violated",
        ),
    ]


def get_all_registered_hypotheses() -> List[ResearchHypothesis]:
    """Return all 8 pre-registered Phase 9.6 research hypotheses."""
    return get_default_phase9_6_hypotheses()


def get_hypothesis_by_id(hypothesis_id: str) -> Optional[ResearchHypothesis]:
    """Lookup pre-registered hypothesis by ID."""
    for h in get_default_phase9_6_hypotheses():
        if h.hypothesis_id == hypothesis_id:
            return h
    return None

