"""
Transparent Decomposable Strategy Scoring Engine.

CRITICAL REQUIREMENT:
Every strategy score must be fully decomposable into component scores so the user
can understand WHY a candidate ranked highly or poorly.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from src.strategies.suitability import MarketThesis
from src.strategies.templates import StrategyCandidate


class ComponentScores(BaseModel):
    """Decomposable component scores summing to 100 max."""
    directional_alignment: float = Field(ge=0.0, le=25.0, description="Directional thesis alignment (0-25)")
    volatility_alignment: float = Field(ge=0.0, le=25.0, description="IV vs RV environment fit (0-25)")
    expected_move_alignment: float = Field(ge=0.0, le=15.0, description="Move boundary suitability (0-15)")
    liquidity: float = Field(ge=0.0, le=15.0, description="Spread & volume execution quality (0-15)")
    risk_reward: float = Field(ge=0.0, le=20.0, description="Max loss vs max profit ratio (0-20)")


class StrategyScore(BaseModel):
    """Transparent scoring result for a candidate strategy."""
    overall_score: float = Field(ge=0.0, le=100.0)
    components: ComponentScores
    positive_evidence: list[str] = Field(default_factory=list)
    negative_evidence: list[str] = Field(default_factory=list)
    major_risks: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


def evaluate_and_score_strategy(
    candidate: StrategyCandidate,
    thesis: MarketThesis,
) -> StrategyScore:
    """
    Evaluates candidate strategy against market thesis and computes decomposable score.
    """
    pos_evidence = []
    neg_evidence = []
    risks = []
    missing = []

    dir_score = 0.0
    vol_score = 0.0
    em_score = 10.0
    liq_score = candidate.liquidity_score * 15.0
    rr_score = 10.0

    name = candidate.strategy_name.upper()
    d_view = thesis.direction_view.upper()
    v_view = thesis.volatility_view.upper()
    net_d = candidate.net_greeks.net_delta
    net_v = candidate.net_greeks.net_vega

    # 1. Directional Alignment (0-25)
    if "BULL" in d_view:
        if net_d > 5.0:
            dir_score = 25.0
            pos_evidence.append(f"Net Delta (+{net_d:.1f}) strongly aligns with Bullish thesis.")
        elif net_d > 0.0:
            dir_score = 18.0
            pos_evidence.append(f"Net Delta (+{net_d:.1f}) is mildly bullish.")
        else:
            dir_score = 5.0
            neg_evidence.append(f"Strategy Delta ({net_d:.1f}) conflicts with Bullish thesis.")

    elif "BEAR" in d_view:
        if net_d < -5.0:
            dir_score = 25.0
            pos_evidence.append(f"Net Delta ({net_d:.1f}) strongly aligns with Bearish thesis.")
        elif net_d < 0.0:
            dir_score = 18.0
            pos_evidence.append(f"Net Delta ({net_d:.1f}) is mildly bearish.")
        else:
            dir_score = 5.0
            neg_evidence.append(f"Strategy Delta ({net_d:.1f}) conflicts with Bearish thesis.")

    elif "NEUTRAL" in d_view or "SIDEWAYS" in d_view:
        if abs(net_d) <= 5.0:
            dir_score = 25.0
            pos_evidence.append(f"Delta-neutral profile (|Delta|={abs(net_d):.1f} <= 5.0) matches Sideways regime.")
        else:
            dir_score = 8.0
            neg_evidence.append(f"Directional exposure (|Delta|={abs(net_d):.1f}) in Sideways regime.")

    else:  # UNCERTAIN
        dir_score = 12.0
        missing.append("Directional thesis is UNCERTAIN.")

    # 2. Volatility Alignment (0-25)
    if v_view == "IV_HIGH":
        # Prefer net credit / net negative vega
        if net_v < 0.0 or "CONDOR" in name or "SPREAD" in name:
            vol_score = 25.0
            pos_evidence.append("Defined-risk premium structure leverages elevated IV.")
        elif "LONG" in name and net_v > 0.0:
            vol_score = 8.0
            neg_evidence.append("Purchasing expensive implied volatility (Long Vega) in high IV environment.")
            risks.append("High volatility crush risk if IV contracts rapidly.")
        else:
            vol_score = 15.0

    elif v_view == "IV_LOW":
        # Prefer net positive vega / debit structures
        if net_v > 0.0 or "LONG" in name or "DEBIT" in name:
            vol_score = 25.0
            pos_evidence.append("Purchasing underpriced implied volatility (Long Vega) in low IV environment.")
        else:
            vol_score = 12.0
            neg_evidence.append("Selling low-premium options in low IV regime.")

    else:
        vol_score = 18.0

    # 3. Risk/Reward Score (0-20)
    if candidate.max_loss is not None and candidate.max_loss < 0 and candidate.max_profit is not None and candidate.max_profit > 0:
        ratio = abs(candidate.max_profit / candidate.max_loss)
        if ratio >= 1.5:
            rr_score = 20.0
            pos_evidence.append(f"Favorable Risk/Reward ratio of {ratio:.2f}:1.")
        elif ratio >= 1.0:
            rr_score = 15.0
        else:
            rr_score = 10.0
            neg_evidence.append(f"Sub-optimal Risk/Reward ratio of {ratio:.2f}:1.")
    elif candidate.max_loss == float("-inf"):
        rr_score = 2.0
        risks.append("CRITICAL RISK: Strategy carries UNLIMITED downside loss potential!")
    else:
        rr_score = 12.0

    # Major Risks summary
    if candidate.dte <= 7:
        risks.append(f"Short DTE ({candidate.dte} days): Accelerated Gamma and Theta decay risk near expiry.")

    # Components
    components = ComponentScores(
        directional_alignment=round(dir_score, 1),
        volatility_alignment=round(vol_score, 1),
        expected_move_alignment=round(em_score, 1),
        liquidity=round(liq_score, 1),
        risk_reward=round(rr_score, 1),
    )

    total_score = round(dir_score + vol_score + em_score + liq_score + rr_score, 1)
    confidence = round(thesis.direction_confidence * (candidate.liquidity_score or 0.8), 2)

    return StrategyScore(
        overall_score=total_score,
        components=components,
        positive_evidence=pos_evidence,
        negative_evidence=neg_evidence,
        major_risks=risks,
        missing_info=missing,
        confidence=confidence,
    )
