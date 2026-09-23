"""
Strategy Suitability Assessment Engine.

Evaluates directional alignment, volatility environment, expected-move comparison,
time decay exposure, liquidity metrics, and defined vs undefined risk profiles.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from src.ingestion.schemas import MarketRegimeResult, MarketRegimeType
from src.options.surface import VolatilitySurfaceResult


class MarketThesis(BaseModel):
    """
    Synthesized market thesis inputs from Phase 2 (Technical/Regime) and Phase 3 (IV/Surface).
    """
    symbol: str = "NIFTY"
    regime: MarketRegimeResult
    surface: VolatilitySurfaceResult
    realized_vol_20d: Optional[float] = None
    atr_14: Optional[float] = None
    vix_value: Optional[float] = None

    # Directional opinion
    direction_view: str = Field(description="BULLISH, BEARISH, NEUTRAL, or UNCERTAIN")
    direction_confidence: float = Field(ge=0.0, le=1.0)

    # Volatility opinion
    volatility_view: str = Field(description="IV_HIGH, IV_LOW, IV_FAIR, or VOL_EXPANDING")
    iv_rv_spread: Optional[float] = None  # IV - RV20


class SuitabilityAssessment(BaseModel):
    """Structured assessment of a candidate strategy against the active MarketThesis."""
    strategy_name: str
    directional_fit: str  # "HIGH", "MEDIUM", "LOW", "MISALIGNED"
    volatility_fit: str   # "HIGH", "MEDIUM", "LOW", "MISALIGNED"
    expected_move_fit: str
    time_suitability: str
    liquidity_fit: str
    risk_profile: str     # "DEFINED_RISK", "UNDEFINED_RISK"
