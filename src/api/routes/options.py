"""
Options data API routes.

Endpoints for option chain, expiries, and chain analysis.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.cache.memory_cache import InMemoryCache
from src.ingestion.base import DataUnavailableError
from src.ingestion.provider_factory import get_options_provider
from src.options.chain import OptionChainAnalyzer
from src.preprocessing.cleaning import clean_option_chain
from src.preprocessing.validation import validate_option_chain
from src.utils.config import get_config
from src.utils.logging_config import get_logger
from src.utils.time_utils import now_ist, parse_nse_date

logger = get_logger(__name__)
router = APIRouter()

# Module-level cache (in-memory, configurable TTL)
_cache = InMemoryCache(default_ttl_seconds=60)
_analyzer = OptionChainAnalyzer()


@router.get("/expiries/{symbol}")
def get_expiries(symbol: str):
    """Get available expiry dates for an underlying."""
    cache_key = f"expiries:{symbol.upper()}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        provider = get_options_provider()
        expiries = provider.get_expiry_dates(symbol.upper())
        result = {
            "symbol": symbol.upper(),
            "expiries": [e.isoformat() for e in expiries],
            "count": len(expiries),
            "provider": provider.provider_name,
        }
        _cache.set(cache_key, result, ttl_seconds=300)
        return result
    except DataUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "DATA_UNAVAILABLE", "message": str(e)},
        )
    except Exception as e:
        logger.error(f"Error fetching expiries for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chain/{symbol}")
def get_option_chain(
    symbol: str,
    expiry: Optional[str] = Query(default=None, description="Expiry date (YYYY-MM-DD)"),
):
    """
    Get the full option chain for an underlying.

    Returns raw chain data with per-strike CE/PE quotes.
    If data is unavailable, returns a clear error — never fake data.
    """
    expiry_date = None
    if expiry:
        try:
            expiry_date = date.fromisoformat(expiry)
        except ValueError:
            try:
                expiry_date = parse_nse_date(expiry)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "INVALID_DATE", "message": f"Cannot parse date: {expiry}"},
                )

    cache_key = f"chain:{symbol.upper()}:{expiry or 'nearest'}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        provider = get_options_provider()
        snapshot = provider.get_option_chain(symbol.upper(), expiry_date)

        # Clean and validate
        snapshot = clean_option_chain(snapshot)
        quality_report = validate_option_chain(snapshot)

        # Serialize
        result = {
            "chain": snapshot.model_dump(mode="json"),
            "data_quality": quality_report.model_dump(),
            "provider": provider.provider_name,
            "timestamp": now_ist().isoformat(),
        }

        config = get_config()
        ttl = config.env.cache_ttl_live_seconds
        _cache.set(cache_key, result, ttl_seconds=ttl)

        # Save to database (best-effort)
        try:
            from src.database.repository import Repository
            repo = Repository()
            repo.save_chain_snapshot(snapshot)
            repo.close()
        except Exception as db_err:
            logger.warning(f"Could not save chain to DB: {db_err}")

        return result

    except DataUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "DATA_UNAVAILABLE", "message": str(e)},
        )
    except Exception as e:
        logger.error(f"Error fetching option chain for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chain/{symbol}/analysis")
def get_chain_analysis(
    symbol: str,
    expiry: Optional[str] = Query(default=None, description="Expiry date (YYYY-MM-DD)"),
):
    """
    Get option chain analysis with probabilistic analytics.

    Includes: PCR, max pain, OI concentration zones, unusual activity,
    liquidity warnings, and probabilistic interpretation.
    """
    expiry_date = None
    if expiry:
        try:
            expiry_date = date.fromisoformat(expiry)
        except ValueError:
            try:
                expiry_date = parse_nse_date(expiry)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={"error": "INVALID_DATE", "message": f"Cannot parse date: {expiry}"},
                )

    cache_key = f"analysis:{symbol.upper()}:{expiry or 'nearest'}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    try:
        provider = get_options_provider()
        snapshot = provider.get_option_chain(symbol.upper(), expiry_date)
        snapshot = clean_option_chain(snapshot)

        analysis = _analyzer.analyze(snapshot)
        quality_report = validate_option_chain(snapshot)

        result = {
            "analysis": analysis.model_dump(mode="json"),
            "data_quality": quality_report.model_dump(),
            "provider": provider.provider_name,
            "timestamp": now_ist().isoformat(),
        }

        config = get_config()
        ttl = config.env.cache_ttl_live_seconds
        _cache.set(cache_key, result, ttl_seconds=ttl)

        return result

    except DataUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "DATA_UNAVAILABLE", "message": str(e)},
        )
    except Exception as e:
        logger.error(f"Error analyzing chain for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chain/{symbol}/refresh")
def refresh_chain(symbol: str):
    """
    Force a fresh data fetch (clears cache for this symbol).
    Respects rate limiting.
    """
    # Clear all cached data for this symbol
    _cache.clear()
    logger.info(f"Cache cleared for {symbol}")

    return {
        "status": "cache_cleared",
        "symbol": symbol.upper(),
        "message": "Next request will fetch fresh data from provider.",
    }


@router.get("/surface/{symbol}")
def get_volatility_surface(
    symbol: str,
    expiry: Optional[str] = Query(default=None, description="Expiry date (YYYY-MM-DD)"),
):
    """
    Get Volatility Surface analytics (ATM IV, OTM Call/Put Skew, Term Structure).
    """
    try:
        provider = get_options_provider()
        exp_date = date.fromisoformat(expiry) if expiry else None
        snapshot = provider.get_option_chain(symbol.upper(), exp_date)
        snapshot = clean_option_chain(snapshot)

        from src.options.surface import compute_volatility_surface
        surface = compute_volatility_surface(snapshot)

        return surface.model_dump(mode="json")
    except DataUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing volatility surface: {e}")


@router.get("/expected-move/{symbol}")
def get_expected_move_endpoint(
    symbol: str,
    expiry: Optional[str] = Query(default=None, description="Expiry date (YYYY-MM-DD)"),
):
    """
    Get multi-source Expected Move estimation (Model-Implied, Realized Vol, ATR-based).
    """
    try:
        provider = get_options_provider()
        exp_date = date.fromisoformat(expiry) if expiry else (date.today() + timedelta(days=7))
        snapshot = provider.get_option_chain(symbol.upper(), exp_date)
        snapshot = clean_option_chain(snapshot)

        from src.options.surface import compute_expected_move, compute_volatility_surface
        surface = compute_volatility_surface(snapshot)
        atm_iv = surface.atm_iv

        move = compute_expected_move(
            spot=snapshot.spot_price,
            expiry_date=snapshot.expiry_date,
            atm_iv=atm_iv,
            underlying=symbol.upper(),
        )

        return move.model_dump(mode="json")
    except DataUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing expected move: {e}")

