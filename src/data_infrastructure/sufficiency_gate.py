"""
Phase 9 — Capability-Specific Data Sufficiency Gate.

Evaluates whether a dataset satisfies specific empirical criteria for:
- Technical Feature Generation
- Historical Equity Backtesting
- Options Settlement & Volatility Research (LTP/OI/IV)
- Options Execution Backtesting (Requires Bid/Ask)
- Machine Learning Model Training (Chronological sample size)
- Walk-Forward Validation
- Paper Trading Execution (Equity)
- Options Paper Execution (Strictly BLOCKED until verified)

Does NOT create one global gate that blocks unrelated research.
Returns PASS, WARNING, or FAIL with explicit, actionable reasons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional


@dataclass
class SufficiencyEvaluation:
    capability: str
    status: str  # PASS, WARNING, FAIL, BLOCKED
    is_sufficient: bool
    reasons: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class DataSufficiencyGate:
    """
    Capability-specific gatekeeper evaluating data adequacy before downstream usage.
    """

    # Thresholds
    MIN_EQUITY_BACKTEST_SESSIONS: int = 15
    MIN_ML_TRAINING_SESSIONS: int = 60
    MIN_OPTIONS_BACKTEST_QUOTES: int = 30
    MIN_BID_ASK_COVERAGE_FOR_EXECUTION_PCT: float = 70.0

    @classmethod
    def evaluate_all(
        cls,
        symbol: str,
        trading_sessions_count: int,
        option_quotes_count: int = 0,
        bid_ask_coverage_pct: float = 0.0,
        iv_coverage_pct: float = 0.0,
        is_live_options_verified: bool = False,
        is_live_bid_ask_available: bool = False,
    ) -> Dict[str, SufficiencyEvaluation]:
        """Runs all capability evaluations in parallel."""
        return {
            "feature_generation": cls.check_feature_generation(trading_sessions_count),
            "historical_equity_backtest": cls.check_equity_backtest(trading_sessions_count),
            "options_ltp_oi_research": cls.check_options_ltp_research(option_quotes_count),
            "options_execution_backtest": cls.check_options_execution_backtest(option_quotes_count, bid_ask_coverage_pct),
            "ml_training": cls.check_ml_training(trading_sessions_count),
            "walk_forward_validation": cls.check_walk_forward(trading_sessions_count),
            "paper_equity_execution": cls.check_paper_equity_execution(is_live_bid_ask_available),
            "options_paper_execution": cls.check_options_paper_execution(is_live_options_verified),
        }

    @classmethod
    def check_feature_generation(cls, sessions_count: int) -> SufficiencyEvaluation:
        reasons = []
        if sessions_count >= 14:  # Minimum for RSI 14, ATR 14
            status = "PASS"
            is_suff = True
        elif sessions_count >= 5:
            status = "WARNING"
            is_suff = True
            reasons.append(f"Only {sessions_count} sessions available; longer-period indicators (e.g. SMA50) will be NaN.")
        else:
            status = "FAIL"
            is_suff = False
            reasons.append(f"Insufficient sessions ({sessions_count}) for minimum 5-day technical indicator calculation.")

        return SufficiencyEvaluation(
            capability="feature_generation",
            status=status,
            is_sufficient=is_suff,
            reasons=reasons,
            metrics={"sessions_count": sessions_count},
        )

    @classmethod
    def check_equity_backtest(cls, sessions_count: int) -> SufficiencyEvaluation:
        reasons = []
        if sessions_count >= cls.MIN_EQUITY_BACKTEST_SESSIONS:
            status = "PASS"
            is_suff = True
        else:
            status = "FAIL"
            is_suff = False
            reasons.append(f"Requires at least {cls.MIN_EQUITY_BACKTEST_SESSIONS} trading sessions for meaningful backtest. Found: {sessions_count}.")

        return SufficiencyEvaluation(
            capability="historical_equity_backtest",
            status=status,
            is_sufficient=is_suff,
            reasons=reasons,
            metrics={"sessions_count": sessions_count, "required_min": cls.MIN_EQUITY_BACKTEST_SESSIONS},
        )

    @classmethod
    def check_options_ltp_research(cls, option_quotes_count: int) -> SufficiencyEvaluation:
        reasons = []
        if option_quotes_count >= cls.MIN_OPTIONS_BACKTEST_QUOTES:
            status = "PASS"
            is_suff = True
        elif option_quotes_count > 0:
            status = "WARNING"
            is_suff = True
            reasons.append(f"Limited options quotes ({option_quotes_count} < {cls.MIN_OPTIONS_BACKTEST_QUOTES}).")
        else:
            status = "FAIL"
            is_suff = False
            reasons.append("Zero option quote records available for settlement/OI research.")

        return SufficiencyEvaluation(
            capability="options_ltp_oi_research",
            status=status,
            is_sufficient=is_suff,
            reasons=reasons,
            metrics={"option_quotes_count": option_quotes_count},
        )

    @classmethod
    def check_options_execution_backtest(
        cls,
        option_quotes_count: int,
        bid_ask_coverage_pct: float,
    ) -> SufficiencyEvaluation:
        reasons = []
        if option_quotes_count < cls.MIN_OPTIONS_BACKTEST_QUOTES:
            return SufficiencyEvaluation(
                capability="options_execution_backtest",
                status="FAIL",
                is_sufficient=False,
                reasons=[f"Insufficient options quotes count: {option_quotes_count}."],
                metrics={"option_quotes_count": option_quotes_count, "bid_ask_coverage_pct": bid_ask_coverage_pct},
            )

        if bid_ask_coverage_pct >= cls.MIN_BID_ASK_COVERAGE_FOR_EXECUTION_PCT:
            status = "PASS"
            is_suff = True
        else:
            status = "FAIL"
            is_suff = False
            reasons.append(
                f"Historical Bid/Ask coverage ({bid_ask_coverage_pct:.1f}%) is below required {cls.MIN_BID_ASK_COVERAGE_FOR_EXECUTION_PCT}%. "
                "Execution slippage and realistic fills cannot be modeled."
            )

        return SufficiencyEvaluation(
            capability="options_execution_backtest",
            status=status,
            is_sufficient=is_suff,
            reasons=reasons,
            metrics={"option_quotes_count": option_quotes_count, "bid_ask_coverage_pct": bid_ask_coverage_pct},
        )

    @classmethod
    def check_ml_training(cls, sessions_count: int) -> SufficiencyEvaluation:
        reasons = []
        if sessions_count >= cls.MIN_ML_TRAINING_SESSIONS:
            status = "PASS"
            is_suff = True
        elif sessions_count >= 30:
            status = "WARNING"
            is_suff = False
            reasons.append(f"Sample size {sessions_count} sessions is marginally low for ML training. High risk of overfitting.")
        else:
            status = "FAIL"
            is_suff = False
            reasons.append(f"Insufficient historical data ({sessions_count} sessions < {cls.MIN_ML_TRAINING_SESSIONS}) for statistical ML training.")

        return SufficiencyEvaluation(
            capability="ml_training",
            status=status,
            is_sufficient=is_suff,
            reasons=reasons,
            metrics={"sessions_count": sessions_count, "required_min": cls.MIN_ML_TRAINING_SESSIONS},
        )

    @classmethod
    def check_walk_forward(cls, sessions_count: int) -> SufficiencyEvaluation:
        min_wf = cls.MIN_ML_TRAINING_SESSIONS + 20
        reasons = []
        if sessions_count >= min_wf:
            status = "PASS"
            is_suff = True
        else:
            status = "FAIL"
            is_suff = False
            reasons.append(f"Walk-forward validation requires at least {min_wf} sessions (train + test folds). Found: {sessions_count}.")

        return SufficiencyEvaluation(
            capability="walk_forward_validation",
            status=status,
            is_sufficient=is_suff,
            reasons=reasons,
            metrics={"sessions_count": sessions_count, "required_min": min_wf},
        )

    @classmethod
    def check_paper_equity_execution(cls, is_live_bid_ask_available: bool) -> SufficiencyEvaluation:
        reasons = []
        if is_live_bid_ask_available:
            status = "PASS"
            is_suff = True
        else:
            status = "FAIL"
            is_suff = False
            reasons.append("No verified live Bid/Ask quote feed. Public feed provides LTP only.")

        return SufficiencyEvaluation(
            capability="paper_equity_execution",
            status=status,
            is_sufficient=is_suff,
            reasons=reasons,
            metrics={"is_live_bid_ask_available": is_live_bid_ask_available},
        )

    @classmethod
    def check_options_paper_execution(cls, is_live_options_verified: bool) -> SufficiencyEvaluation:
        reasons = []
        if is_live_options_verified:
            status = "PASS"
            is_suff = True
        else:
            status = "BLOCKED"
            is_suff = False
            reasons.append("OPTIONS PAPER TRADING: BLOCKED — LIVE OPTIONS DATA NOT VERIFIED.")

        return SufficiencyEvaluation(
            capability="options_paper_execution",
            status=status,
            is_sufficient=is_suff,
            reasons=reasons,
            metrics={"is_live_options_verified": is_live_options_verified},
        )
