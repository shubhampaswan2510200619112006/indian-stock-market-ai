"""
Options Prediction Layer for ML Engine.
Translates model predictions & uncertainty estimates into strategy requests.
Strictly decoupled from trade execution.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from src.ml.sufficiency import MLDataCoverageStatus


class SignalDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    NO_TRADE = "NO_TRADE"


@dataclass
class MLStrategySignal:
    timestamp: str
    symbol: str
    direction: SignalDirection
    predicted_probability: float
    uncertainty_score: float
    recommended_strategy_name: str
    rationale: str
    is_trade_allowed: bool


class OptionsPredictionLayer:
    """
    Translates ML probabilistic outputs into strategy candidates.
    Enforces mandatory NO_TRADE when confidence is low or data scale is limited.
    """

    def __init__(self, bullish_threshold: float = 0.55, bearish_threshold: float = 0.45, min_confidence: float = 0.55):
        self.bullish_threshold = bullish_threshold
        self.bearish_threshold = bearish_threshold
        self.min_confidence = min_confidence

    def generate_signal(
        self,
        symbol: str,
        timestamp_str: str,
        predicted_proba: float,
        data_coverage_status: MLDataCoverageStatus,
    ) -> MLStrategySignal:
        """
        Maps ML predicted probability to a strategy signal.
        """
        uncertainty = 1.0 - abs(predicted_proba - 0.5) * 2.0  # 0 = max certainty, 1 = max uncertainty

        # If data coverage is INSUFFICIENT or uncertainty is too high -> NO_TRADE
        if data_coverage_status == MLDataCoverageStatus.INSUFFICIENT:
            return MLStrategySignal(
                timestamp=timestamp_str,
                symbol=symbol,
                direction=SignalDirection.NO_TRADE,
                predicted_probability=predicted_proba,
                uncertainty_score=uncertainty,
                recommended_strategy_name="NO_TRADE",
                rationale="Data sufficiency status is INSUFFICIENT. Trading disallowed.",
                is_trade_allowed=False,
            )

        if predicted_proba >= self.bullish_threshold:
            direction = SignalDirection.BULLISH
            strategy = "Bull Call Spread"
            rationale = f"Model predicts bullish return with P={predicted_proba:.2f} (above {self.bullish_threshold:.2f} threshold)."
            allowed = True
        elif predicted_proba <= self.bearish_threshold:
            direction = SignalDirection.BEARISH
            strategy = "Bear Put Spread"
            rationale = f"Model predicts bearish return with P={predicted_proba:.2f} (below {self.bearish_threshold:.2f} threshold)."
            allowed = True
        else:
            direction = SignalDirection.NO_TRADE
            strategy = "NO_TRADE"
            rationale = f"Model probability P={predicted_proba:.2f} is neutral/uncertain (between {self.bearish_threshold} and {self.bullish_threshold})."
            allowed = False

        return MLStrategySignal(
            timestamp=timestamp_str,
            symbol=symbol,
            direction=direction,
            predicted_probability=predicted_proba,
            uncertainty_score=uncertainty,
            recommended_strategy_name=strategy,
            rationale=rationale,
            is_trade_allowed=allowed,
        )
