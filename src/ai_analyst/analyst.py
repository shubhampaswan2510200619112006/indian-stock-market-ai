"""
AI Market Analyst & Structured Context Engine (Phase 7).
Consumes LiveMarketSnapshot aggregate object and generates structured MarketAnalysis JSON.
Enforces event-driven invalidation: NEVER called on every tick.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.live_market.snapshot import LiveMarketSnapshot


class DirectionalBias(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class ResearchSetupType(str, Enum):
    CANDIDATE = "CANDIDATE"
    NO_TRADE = "NO_TRADE"


class MarketAnalysis(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    symbol: str
    market_regime: str
    directional_bias: DirectionalBias
    # IMPORTANT: confidence is a RULE-BASED HEURISTIC — not a calibrated statistical probability.
    # A calibrated probability requires a fitted, OOS-validated ML model.
    # Do NOT present this to investors as "AI probability" or "prediction accuracy".
    confidence: float
    is_calibrated_probability: bool = False  # Always False until a real model is fitted
    confidence_note: str = "RULE_BASED_HEURISTIC — not derived from a calibrated model"
    technical_summary: str
    options_summary: str
    volatility_summary: str
    news_summary: str
    ml_summary: str
    key_support: float
    key_resistance: float
    support_resistance_method: str = "HEURISTIC_PERCENTAGE — structural analysis not yet implemented"
    bullish_factors: List[str] = Field(default_factory=list)
    bearish_factors: List[str] = Field(default_factory=list)
    uncertainty_factors: List[str] = Field(default_factory=list)
    invalidation_conditions: List[str] = Field(default_factory=list)
    research_setup: ResearchSetupType = ResearchSetupType.NO_TRADE
    recommended_strategy: str = "NO_TRADE"
    reasoning: str


class AIMarketAnalyst:
    """
    Structured AI Market Analyst.
    Consumes unified LiveMarketSnapshot and produces typed MarketAnalysis.
    Uses event-driven invalidation to prevent tick-by-tick LLM calls.
    """

    def __init__(self):
        self._last_analysis: Optional[MarketAnalysis] = None
        self._last_snapshot_time: Optional[str] = None

    def analyze_snapshot(self, snapshot: LiveMarketSnapshot, force_refresh: bool = False) -> MarketAnalysis:
        """
        Generates or reuses structured market analysis.
        Reuses cached analysis if snapshot is unchanged and force_refresh is False.
        """
        if not force_refresh and self._last_analysis and self._last_snapshot_time == snapshot.timestamp:
            return self._last_analysis

        symbol = snapshot.symbol
        last_p = snapshot.market.last_price if snapshot.market else 25000.0

        # Technicals & Regime
        regime_str = snapshot.regime.get("regime", "SIDEWAYS")
        multi_tf = snapshot.multi_timeframe

        bullish_f = []
        bearish_f = []
        uncertainty_f = []

        if multi_tf:
            if "BULLISH" in multi_tf.overall_multi_tf_regime:
                directional = DirectionalBias.BULLISH
                bullish_f.append(f"Multi-timeframe trend is {multi_tf.overall_multi_tf_regime}.")
            elif "BEARISH" in multi_tf.overall_multi_tf_regime:
                directional = DirectionalBias.BEARISH
                bearish_f.append(f"Multi-timeframe trend is {multi_tf.overall_multi_tf_regime}.")
            else:
                directional = DirectionalBias.NEUTRAL
                uncertainty_f.append("Multi-timeframe signals are mixed/sideways.")
        else:
            directional = DirectionalBias.NEUTRAL

        # News & Event Context
        high_mat_news = [n for n in snapshot.news if n.get("materiality") in ["HIGH", "CRITICAL"]]
        if high_mat_news:
            uncertainty_f.append(f"High-materiality news event detected: '{high_mat_news[0].get('title')}'.")

        # ML Context
        ml_stat = snapshot.ml.get("overall_status", "NORMAL")
        if ml_stat == "OOD":
            uncertainty_f.append("Phase 6 ML feature distribution is Out-Of-Distribution (OOD).")

        # Key levels — heuristic ±1% until structural analysis is implemented
        # NOTE: These are not real support/resistance levels.
        # A proper implementation requires swing-high/swing-low analysis.
        support = round(last_p * 0.99, 2)
        resistance = round(last_p * 1.01, 2)

        # Decide setup: NO_TRADE preferred when uncertainty is high
        if len(uncertainty_f) >= 2 or directional == DirectionalBias.NEUTRAL:
            setup = ResearchSetupType.NO_TRADE
            strat = "NO_TRADE"
            reasoning = "Uncertainty is elevated due to mixed signals or high-materiality events. NO_TRADE is enforced."
        elif directional == DirectionalBias.BULLISH:
            setup = ResearchSetupType.CANDIDATE
            strat = "Bull Call Spread"
            reasoning = "Multi-timeframe alignment supports bullish research setup with defined risk."
        else:
            setup = ResearchSetupType.CANDIDATE
            strat = "Bear Put Spread"
            reasoning = "Multi-timeframe alignment supports bearish research setup with defined risk."

        analysis = MarketAnalysis(
            timestamp=snapshot.timestamp,
            symbol=symbol,
            market_regime=regime_str,
            directional_bias=directional,
            confidence=0.70 if setup == ResearchSetupType.CANDIDATE else 0.40,
            technical_summary=f"Price={last_p}, Regime={regime_str}, Multi-TF={multi_tf.overall_multi_tf_regime if multi_tf else 'N/A'}.",
            options_summary=f"Options status: {snapshot.options.get('status_label', 'UNAVAILABLE')}.",
            volatility_summary=f"Realized Vol 5D: {snapshot.volatility.get('realized_volatility_5d', 0.145):.3f}.",
            news_summary=f"Total news items ingested: {len(snapshot.news)}.",
            ml_summary=f"ML Status: {snapshot.ml.get('overall_status', 'NORMAL')} (Banner: {snapshot.ml.get('research_banner', 'LIMITED')}).",
            key_support=support,
            key_resistance=resistance,
            bullish_factors=bullish_f,
            bearish_factors=bearish_f,
            uncertainty_factors=uncertainty_f,
            invalidation_conditions=[f"Break below support {support}", f"Break above resistance {resistance}"],
            research_setup=setup,
            recommended_strategy=strat,
            reasoning=reasoning,
        )

        self._last_analysis = analysis
        self._last_snapshot_time = snapshot.timestamp
        return analysis
