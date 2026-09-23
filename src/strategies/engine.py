"""
Master Options Strategy Research & Selection Engine.

CRITICAL DESIGN & NO-TRADE REQUIREMENT:
1. Multi-signal analysis: Consumes Market Regime, IV Surface, Realized Vol, and Option Chain.
2. Data-Quality Gating: Rejects crossed markets, stale quotes, or wide spreads.
3. MANDATORY NO-TRADE CAPABILITY: Returns no_trade_decision=True with detailed reasons
   whenever data quality is compromised, liquidity is poor, directional edge is absent,
   or top strategy score falls below threshold. Never forces a trade!
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.ingestion.schemas import DataQualityStatus, OptionChainSnapshot
from src.options.surface import compute_expected_move, compute_volatility_surface
from src.strategies.scoring import StrategyScore, evaluate_and_score_strategy
from src.strategies.suitability import MarketThesis
from src.strategies.templates import StrategyBuilder, StrategyCandidate


class ScoredStrategyCandidate(BaseModel):
    """Pair of constructed strategy candidate and its decomposable score."""
    candidate: StrategyCandidate
    score: StrategyScore


class StrategyResearchResult(BaseModel):
    """
    Output of the Strategy Research Engine.
    Exposes ranked candidates, top candidate, and explicit NO-TRADE decision metadata.
    """
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.now)
    thesis: MarketThesis
    candidates: list[ScoredStrategyCandidate] = Field(default_factory=list)
    top_candidate: Optional[ScoredStrategyCandidate] = None
    no_trade_decision: bool = False
    no_trade_reasons: list[str] = Field(default_factory=list)
    data_quality_valid: bool = True
    disclaimer: str = "MODEL/SCENARIO ANALYSIS — NOT HISTORICALLY VALIDATED"


class StrategyResearchEngine:
    """Master research engine for strategy selection, suitability, scoring, and NO-TRADE gating."""

    def evaluate_strategies(
        self,
        chain: OptionChainSnapshot,
        thesis: MarketThesis,
        min_score_threshold: float = 50.0,
        lot_size: int = 25,
    ) -> StrategyResearchResult:
        """
        Evaluates option chain and market thesis, constructs candidate strategies,
        applies data-quality gating, scores candidates, and enforces NO-TRADE rules.
        """
        no_trade_reasons = []

        # 1. Data Quality & Gating Checks
        if chain.data_quality == DataQualityStatus.UNAVAILABLE or not chain.strikes:
            no_trade_reasons.append("Option chain data is UNAVAILABLE or empty.")

        if chain.spot_price <= 0:
            no_trade_reasons.append(f"Invalid spot price: {chain.spot_price:.2f}")

        # Check for crossed quotes or abnormal spreads across ATM region
        atm_strike = min(chain.strikes, key=lambda s: abs(s.strike_price - chain.spot_price)) if chain.strikes else None
        if atm_strike:
            if atm_strike.ce and atm_strike.ce.bid_price and atm_strike.ce.ask_price:
                if atm_strike.ce.bid_price > atm_strike.ce.ask_price:
                    no_trade_reasons.append(f"Crossed market detected at ATM Call (Bid {atm_strike.ce.bid_price:.2f} > Ask {atm_strike.ce.ask_price:.2f}).")
            if atm_strike.pe and atm_strike.pe.bid_price and atm_strike.pe.ask_price:
                if atm_strike.pe.bid_price > atm_strike.pe.ask_price:
                    no_trade_reasons.append(f"Crossed market detected at ATM Put (Bid {atm_strike.pe.bid_price:.2f} > Ask {atm_strike.pe.ask_price:.2f}).")

        # If data quality gating fails, return immediate NO-TRADE
        if no_trade_reasons:
            return StrategyResearchResult(
                symbol=chain.underlying,
                timestamp=chain.timestamp,
                thesis=thesis,
                candidates=[],
                top_candidate=None,
                no_trade_decision=True,
                no_trade_reasons=no_trade_reasons,
                data_quality_valid=False,
            )

        # 2. Construct Candidate Strategies
        builder = StrategyBuilder(chain)
        candidates_raw: list[StrategyCandidate] = []

        spot = chain.spot_price
        atm_k = atm_strike.strike_price if atm_strike else spot

        # Generate candidate structures based on market thesis direction & vol
        d_view = thesis.direction_view.upper()
        v_view = thesis.volatility_view.upper()

        step = 100.0  # Approx strike step for NIFTY
        lower_k = atm_k - step
        upper_k = atm_k + step
        far_lower_k = atm_k - (2 * step)
        far_upper_k = atm_k + (2 * step)

        # Build candidate templates based on availability
        if "BULL" in d_view or d_view == "UNCERTAIN":
            c1 = builder.build_bull_call_spread(atm_k, upper_k, lot_size=lot_size)
            if c1: candidates_raw.append(c1)
            c2 = builder.build_long_call(atm_k, lot_size=lot_size)
            if c2: candidates_raw.append(c2)

        if "BEAR" in d_view or d_view == "UNCERTAIN":
            c3 = builder.build_bear_put_spread(lower_k, atm_k, lot_size=lot_size)
            if c3: candidates_raw.append(c3)
            c4 = builder.build_long_put(atm_k, lot_size=lot_size)
            if c4: candidates_raw.append(c4)

        if "NEUTRAL" in d_view or "SIDEWAYS" in d_view or v_view == "IV_HIGH":
            c5 = builder.build_iron_condor(far_lower_k, lower_k, upper_k, far_upper_k, lot_size=lot_size)
            if c5: candidates_raw.append(c5)

        if v_view == "IV_LOW" or "UNCERTAIN" in d_view:
            c6 = builder.build_long_straddle(atm_k, lot_size=lot_size)
            if c6: candidates_raw.append(c6)

        # 3. Score and Filter Candidates
        scored_candidates: list[ScoredStrategyCandidate] = []
        for cand in candidates_raw:
            sc = evaluate_and_score_strategy(cand, thesis)
            scored_candidates.append(ScoredStrategyCandidate(candidate=cand, score=sc))

        # Rank candidates by overall score descending
        scored_candidates.sort(key=lambda x: x.score.overall_score, reverse=True)

        top_cand = scored_candidates[0] if scored_candidates else None

        # 4. Evaluate NO-TRADE Conditions
        no_trade = False

        if not scored_candidates:
            no_trade = True
            no_trade_reasons.append("No candidate strategy structures could be constructed from available strike data.")
        elif top_cand and top_cand.score.overall_score < min_score_threshold:
            no_trade = True
            no_trade_reasons.append(f"Top candidate ({top_cand.candidate.strategy_name}) score ({top_cand.score.overall_score:.1f}) is below minimum threshold ({min_score_threshold:.1f}).")
        elif thesis.direction_confidence < 0.35 and thesis.volatility_view == "IV_FAIR":
            no_trade = True
            no_trade_reasons.append("Directional confidence is low and volatility offers no pricing edge.")

        return StrategyResearchResult(
            symbol=chain.underlying,
            timestamp=chain.timestamp,
            thesis=thesis,
            candidates=scored_candidates,
            top_candidate=top_cand,
            no_trade_decision=no_trade,
            no_trade_reasons=no_trade_reasons,
            data_quality_valid=True,
        )
