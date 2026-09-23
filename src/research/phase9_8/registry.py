"""
Phase 9.8 — Step 3: Hypothesis Registration & Pre-Registered Criteria Engine.

Registers P98-H001 through P98-H008 with permanently frozen criteria:
- P98-H001: Opening Range Breakout (ORB 15m) Directional Continuation
- P98-H002: Opening Gap (Overnight Gap > 0.3%) Mean-Reversion
- P98-H003: Short-Horizon Momentum (30m normalized momentum)
- P98-H004: Intraday Volatility Compression Breakout (Garman-Klass ratio < 20th percentile)
- P98-H005: Event-Driven Macro Announcement Drift (RBI MPC rate decisions)
- P98-H006: Cross-Sectional Relative Strength / Momentum (Top 2 vs Bottom 2 Equities)
- P98-H007: Market Regime as Forecast Uncertainty / Calibration Context
- P98-H008: Options Microstructure LTP Surface vs Executable Boundary
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np


class HypothesisClassification(str, Enum):
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    PROMISING_RESEARCH_CANDIDATE = "PROMISING_RESEARCH_CANDIDATE"
    NO_EVIDENCE_OF_EDGE = "NO_EVIDENCE_OF_EDGE"


class EvaluationType(str, Enum):
    EXPLORATORY = "EXPLORATORY"
    CONFIRMATORY = "CONFIRMATORY"


@dataclass
class Phase98Hypothesis:
    id: str
    created_at: str
    status: str  # "REGISTERED_FROZEN", "EVALUATED"
    economic_mechanism: str
    instrument: str
    dataset: str
    features: List[str]
    target: str
    prediction_time: str
    execution_time: str
    exit_time: str
    holding_period: str
    cost_model: str
    baseline: str
    success_criteria: str
    failure_criteria: str
    exploratory_or_confirmatory: EvaluationType
    result: Optional[Dict[str, Any]] = None
    final_classification: HypothesisClassification = HypothesisClassification.INCONCLUSIVE


class Phase98HypothesisRegistry:
    """
    Maintains the frozen registry of all Phase 9.8 hypotheses.
    """

    FROZEN_HYPOTHESES: List[Phase98Hypothesis] = [
        Phase98Hypothesis(
            id="P98-H001",
            created_at="2026-09-09T00:00:00Z",
            status="REGISTERED_FROZEN",
            economic_mechanism="First 15-minute range breakout on NIFTY reflects institutional opening imbalances predicting remainder-of-day trend.",
            instrument="NIFTY",
            dataset="TIER_B_INTRADAY_INDEX (5m/15m bars, ~59 sessions)",
            features=["orb_15m_high", "orb_15m_low", "breakout_direction", "opening_volume_ratio"],
            target="target_fwd_ret_remainder_day (09:30 IST to 15:15 IST close)",
            prediction_time="09:30:00 IST (at close of first 15m bar)",
            execution_time="09:30:00 IST (bar close price)",
            exit_time="15:15:00 IST (MOC intraday exit)",
            holding_period="5.75 hours (same-day intraday)",
            cost_model="Indian statutory intraday friction (roundtrip 5 bps + 5 bps slippage = 10 bps)",
            baseline="Naive random walk (50% direction, 0 bps drift)",
            success_criteria="Net Sharpe > 0.50, Win Rate > 53.0%, Net Expectancy > 5.0 bps/trade after costs with N >= 60 trades.",
            failure_criteria="Net Sharpe <= 0.0 OR Net Expectancy <= 0.0 bps/trade OR N < 40 trades (INSUFFICIENT_DATA).",
            exploratory_or_confirmatory=EvaluationType.EXPLORATORY,  # Limited ~59 session sample
        ),
        Phase98Hypothesis(
            id="P98-H002",
            created_at="2026-09-09T00:00:00Z",
            status="REGISTERED_FROZEN",
            economic_mechanism="Overnight index gaps > 0.3% reflect pre-market sentiment overreaction that mean-reverts during opening 30 minutes.",
            instrument="NIFTY",
            dataset="TIER_B_INTRADAY_INDEX (5m bars, ~59 sessions)",
            features=["overnight_gap_pct", "gap_direction", "pre_market_volume_normalized"],
            target="target_fwd_ret_opening_30m (09:15 IST open to 09:45 IST)",
            prediction_time="09:15:00 IST (official market open)",
            execution_time="09:15:00 IST (open auction price)",
            exit_time="09:45:00 IST (at close of 09:40-09:45 bar)",
            holding_period="30 minutes",
            cost_model="Indian statutory intraday friction (10 bps roundtrip)",
            baseline="Continuation drift / zero reversion baseline",
            success_criteria="Mean-reversion Win Rate > 55.0% AND Net Expectancy > 5.0 bps/trade after costs.",
            failure_criteria="Net Expectancy <= 0.0 bps/trade OR gap events N < 20 (INSUFFICIENT_DATA).",
            exploratory_or_confirmatory=EvaluationType.EXPLORATORY,
        ),
        Phase98Hypothesis(
            id="P98-H003",
            created_at="2026-09-09T00:00:00Z",
            status="REGISTERED_FROZEN",
            economic_mechanism="Intraday 30-minute normalized momentum persists over the subsequent 30-minute bar due to execution order slicing.",
            instrument="NIFTY",
            dataset="TIER_B_INTRADAY_INDEX (15m/30m resampled bars)",
            features=["ret_30m", "normalized_vol_30m", "vwap_distance_bps"],
            target="target_fwd_ret_30m (next 30-minute bar return)",
            prediction_time="T (bar close timestamp)",
            execution_time="T (clean bar close)",
            exit_time="T + 30 minutes (next bar close)",
            holding_period="30 minutes",
            cost_model="Indian statutory intraday friction (10 bps roundtrip)",
            baseline="AR(1) linear statistical model",
            success_criteria="Directional Accuracy > 54.0% AND Net Sharpe > 0.50 after realistic turnover costs.",
            failure_criteria="Net Sharpe <= 0.0 OR Turnover friction exceeds gross alpha.",
            exploratory_or_confirmatory=EvaluationType.EXPLORATORY,
        ),
        Phase98Hypothesis(
            id="P98-H004",
            created_at="2026-09-09T00:00:00Z",
            status="REGISTERED_FROZEN",
            economic_mechanism="Intraday volatility compression (Garman-Klass ratio < 20th percentile) followed by volume surge precedes directional expansion.",
            instrument="NIFTY",
            dataset="TIER_B_INTRADAY_INDEX (15m bars)",
            features=["gk_vol_compression_ratio", "volume_surge_ratio", "bollinger_bandwidth_15m"],
            target="target_fwd_vol_expansion_60m (subsequent 60-minute range expansion)",
            prediction_time="T (compression signal bar close)",
            execution_time="T (entry bar close)",
            exit_time="T + 60 minutes",
            holding_period="60 minutes",
            cost_model="Indian statutory intraday friction (10 bps roundtrip)",
            baseline="Unconditional 60m historical volatility",
            success_criteria="Volatility expansion directional accuracy > 55.0% AND Net Expectancy > 10.0 bps.",
            failure_criteria="Net Expectancy <= 0.0 bps OR compression signals N < 25.",
            exploratory_or_confirmatory=EvaluationType.EXPLORATORY,
        ),
        Phase98Hypothesis(
            id="P98-H005",
            created_at="2026-09-09T00:00:00Z",
            status="REGISTERED_FROZEN",
            economic_mechanism="RBI MPC policy rate decisions induce institutional portfolio reallocations creating 3-session post-announcement directional drift.",
            instrument="NIFTY",
            dataset="TIER_D_EVENT (21 verified macro announcements, 2024–2026)",
            features=["announcement_day_ret", "repo_rate_surprise", "stance_change_flag"],
            target="target_fwd_ret_3d (post-announcement 3 sessions close-to-close return)",
            prediction_time="Day T 15:30 IST (on announcement day close)",
            execution_time="Day T+1 09:15 IST (next-day open)",
            exit_time="Day T+4 09:15 IST (open-to-open 3-session holding)",
            holding_period="3 sessions",
            cost_model="Indian statutory swing friction (roundtrip 10 bps delivery/futures)",
            baseline="Historical unconditional 3-day market drift",
            success_criteria="Directional alignment > 60.0% with statistically significant drift (p < 0.05).",
            failure_criteria="Directional alignment <= 55.0% OR p >= 0.05 OR sample N < 15.",
            exploratory_or_confirmatory=EvaluationType.CONFIRMATORY,
        ),
        Phase98Hypothesis(
            id="P98-H006",
            created_at="2026-09-09T00:00:00Z",
            status="REGISTERED_FROZEN",
            economic_mechanism="Cross-sectional 20-day relative strength divergence between Top 2 and Bottom 2 liquid equities generates positive long-short spread.",
            instrument="TOP_10_LIQUID_EQUITIES",
            dataset="TIER_C_CROSS_SECTIONAL (2-year daily OHLCV, SURVIVORSHIP_BIAS_RISK = TRUE)",
            features=["relative_strength_20d", "index_beta_60d", "cross_sectional_dispersion"],
            target="target_fwd_spread_ret_5d (Long Top 2, Short Bottom 2 over 5 sessions)",
            prediction_time="Day T 15:30 IST (weekly rebalance close)",
            execution_time="Day T+1 09:15 IST (open execution)",
            exit_time="Day T+6 09:15 IST (5 sessions open-to-open)",
            holding_period="5 sessions",
            cost_model="Indian statutory delivery friction (STT 10 bps on buy+sell, exchange, GST, stamp = 25 bps roundtrip)",
            baseline="Cap-weighted NIFTY 50 benchmark return",
            success_criteria="Spread Return > 1.0% with Long-Short Net Sharpe > 0.50 after delivery frictions.",
            failure_criteria="Long-Short Net Sharpe <= 0.0 OR survivorship bias invalidates causal inference.",
            exploratory_or_confirmatory=EvaluationType.CONFIRMATORY,
        ),
        Phase98Hypothesis(
            id="P98-H007",
            created_at="2026-09-09T00:00:00Z",
            status="REGISTERED_FROZEN",
            economic_mechanism="Conditioning ML directional probability forecasts on macro market regimes improves out-of-sample Brier score calibration without regime-picking.",
            instrument="NIFTY",
            dataset="TIER_A_DAILY_INDEX (495 sessions, 6 distinct regimes)",
            features=["market_regime_encoded", "regime_stability_score", "spot_momentum", "volatility_regime"],
            target="target_fwd_dir_1d (1D forward direction probability calibration)",
            prediction_time="Day T 15:30 IST",
            execution_time="Day T+1 09:15 IST",
            exit_time="Day T+2 09:15 IST",
            holding_period="1 session",
            cost_model="Not applicable (Pure probabilistic calibration metric)",
            baseline="Unconditioned Logistic Regression / Walk-Forward ML model",
            success_criteria="Brier Score reduction >= 5.0% AND Log-Loss reduction >= 0.02 across all regimes unconditionally.",
            failure_criteria="Brier Score reduction < 2.0% OR calibration degradation in sideways regimes.",
            exploratory_or_confirmatory=EvaluationType.CONFIRMATORY,
        ),
        Phase98Hypothesis(
            id="P98-H008",
            created_at="2026-09-09T00:00:00Z",
            status="REGISTERED_FROZEN",
            economic_mechanism="Historical options quotes contain 102 paired Bid/Ask observations (0.68% quote coverage) but 0.0% continuous executable surface coverage, strictly enforcing execution backtesting block.",
            instrument="NIFTY_OPTIONS",
            dataset="TIER_E_OPTIONS (14,132 Bhavcopy records in SQLite)",
            features=["ltp_settlement_price", "bid_price", "ask_price", "open_interest"],
            target="options_executable_quote_availability",
            prediction_time="Contemporaneous quote timestamp",
            execution_time="N/A (Execution blocked)",
            exit_time="N/A (Execution blocked)",
            holding_period="N/A",
            cost_model="Full options statutory friction (STT 10 bps on sell premium, exchange 5 bps, GST, stamp)",
            baseline="Theoretical Black-Scholes valuation",
            success_criteria="Legitimate paired Bid/Ask quote coverage >= 50.0% with timestamped depth.",
            failure_criteria="Paired Bid/Ask quote coverage < 5.0% -> Strictly BLOCKED.",
            exploratory_or_confirmatory=EvaluationType.CONFIRMATORY,
        ),
    ]

    @classmethod
    def get_all(cls) -> List[Phase98Hypothesis]:
        return list(cls.FROZEN_HYPOTHESES)

    @classmethod
    def save_registry(cls, filepath: str = "data/phase9_8/research_registry.json") -> None:
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(h) for h in cls.FROZEN_HYPOTHESES]
        # Format enums
        for item in data:
            item["exploratory_or_confirmatory"] = item["exploratory_or_confirmatory"].value if isinstance(item["exploratory_or_confirmatory"], EvaluationType) else str(item["exploratory_or_confirmatory"])
            item["final_classification"] = item["final_classification"].value if isinstance(item["final_classification"], HypothesisClassification) else str(item["final_classification"])
        
        def _json_default(obj: Any) -> Any:
            if isinstance(obj, (bool, np.bool_)):
                return bool(obj)
            if isinstance(obj, (int, np.integer)):
                return int(obj)
            if isinstance(obj, (float, np.floating)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            if hasattr(obj, "value"):
                return obj.value
            return str(obj)

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=_json_default)

    @classmethod
    def update_result(
        cls,
        hypothesis_id: str,
        result_dict: Dict[str, Any],
        final_classification: HypothesisClassification,
    ) -> None:
        for h in cls.FROZEN_HYPOTHESES:
            if h.id == hypothesis_id:
                h.status = "EVALUATED"
                h.result = result_dict
                h.final_classification = final_classification
                break
        cls.save_registry()
