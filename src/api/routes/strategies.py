"""
Options Strategy Engine API Routes.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.features.market_regime import MarketRegimeEngine
from src.ingestion.base import DataUnavailableError
from src.ingestion.provider_factory import get_market_data_provider, get_options_provider
from src.ingestion.schemas import TimeFrame
from src.ingestion.yfinance_provider import YFinanceProvider
from src.options.surface import compute_volatility_surface
from src.preprocessing.cleaning import clean_option_chain
from src.strategies.engine import StrategyResearchEngine, StrategyResearchResult
from src.strategies.position_sizing import PositionSizingResult, calculate_position_size
from src.strategies.suitability import MarketThesis

router = APIRouter(prefix="/strategies", tags=["Options Strategies"])


class PositionSizingRequest(BaseModel):
    symbol: str = "NIFTY"
    strategy_name: str = "Bull Call Spread"
    account_equity: float = 500000.0
    max_risk_pct: float = 2.0
    strategy_max_loss: float = 5000.0
    capital_required: float = 12000.0
    spot_price: float = 24000.0
    lot_size: int = 25


@router.get("/candidates/{symbol}", response_model=StrategyResearchResult)
def get_strategy_candidates(
    symbol: str,
    expiry: Optional[str] = Query(default=None, description="Expiry date (YYYY-MM-DD)"),
):
    """
    Evaluates market thesis, constructs multi-leg candidate strategies, scores suitability,
    and returns ranked candidates or mandatory NO-TRADE decision.
    """
    options_provider = get_options_provider()
    market_provider = get_market_data_provider()

    try:
        exp_date = date.fromisoformat(expiry) if expiry else None
        chain = options_provider.get_option_chain(symbol.upper(), exp_date)
        chain = clean_option_chain(chain)

        # Build Market Thesis from Phase 2 & Phase 3
        end_d = date.today()
        start_d = end_d - timedelta(days=120)

        nifty_df = market_provider.get_ohlcv(symbol="NIFTY", start=start_d, end=end_d)
        regime_engine = MarketRegimeEngine()
        vix_val = market_provider.get_india_vix() if isinstance(market_provider, YFinanceProvider) else None
        regime_res = regime_engine.evaluate_regime(nifty_df, vix_value=vix_val, symbol=symbol.upper())

        surface = compute_volatility_surface(chain)
        atm_iv = surface.atm_iv or 0.15

        # Infer directional & volatility views
        d_view = "BULLISH" if "BULL" in regime_res.regime.value else ("BEARISH" if "BEAR" in regime_res.regime.value else "NEUTRAL")
        v_view = "IV_HIGH" if (vix_val and vix_val >= 22.0) or atm_iv > 0.22 else ("IV_LOW" if atm_iv < 0.12 else "IV_FAIR")

        thesis = MarketThesis(
            symbol=symbol.upper(),
            regime=regime_res,
            surface=surface,
            vix_value=vix_val,
            direction_view=d_view,
            direction_confidence=regime_res.confidence,
            volatility_view=v_view,
            iv_rv_spread=(atm_iv - 0.15),
        )

        research_engine = StrategyResearchEngine()
        result = research_engine.evaluate_strategies(chain, thesis)

        return result

    except DataUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error researching strategy candidates: {e}")


@router.post("/position-size", response_model=PositionSizingResult)
def compute_position_size_endpoint(req: PositionSizingRequest):
    """
    Computes research-grade position sizing (lots, quantity, defined loss, account risk %)
    for a given strategy candidate and risk budget.
    """
    try:
        from src.options.portfolio_greeks import PortfolioGreeks
        from src.strategies.templates import StrategyCandidate, StrategyLegDetail

        dummy_cand = StrategyCandidate(
            strategy_name=req.strategy_name,
            symbol=req.symbol.upper(),
            expiry_date=date.today() + timedelta(days=7),
            dte=7,
            spot_price=req.spot_price,
            legs=[],
            net_cost_or_credit=req.strategy_max_loss,
            capital_required=req.capital_required,
            max_profit=req.strategy_max_loss * 1.5,
            max_loss=-req.strategy_max_loss,
            breakevens=[req.spot_price],
            net_greeks=PortfolioGreeks(),
            liquidity_score=0.8,
        )

        res = calculate_position_size(
            candidate=dummy_cand,
            account_equity=req.account_equity,
            max_risk_pct=req.max_risk_pct,
            lot_size=req.lot_size,
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing position size: {e}")
