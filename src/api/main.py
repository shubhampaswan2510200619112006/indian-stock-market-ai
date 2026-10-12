"""
FastAPI application entry point.

Provides REST API for the Indian Options AI platform.
CORS is enabled for Streamlit dashboard communication.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import (
    auth,
    backtest,
    data_infrastructure,
    health,
    live,
    market,
    ml,
    news,
    options,
    paper_trading,
    regime,
    research,
    strategies,
    technical,
)
from src.database.connection import init_db
from src.utils.config import get_config
from src.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    setup_logging()
    logger.info("Starting Indian Options AI API...")

    # Initialize database tables
    init_db()
    logger.info("Database initialized")

    # Seed underlyings from config
    _seed_underlyings()

    yield

    # Shutdown
    logger.info("Shutting down Indian Options AI API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = get_config()

    app = FastAPI(
        title="Indian Options AI",
        description=(
            "AI-powered options research and analysis platform for Indian markets (NSE). "
            "Phase 1: Real data + Option chain. Phase 2: Technical/Regime. Phase 3: Volatility/Greeks. "
            "Phase 4: Strategy Engine. Phase 5: Backtesting. Phase 6: ML. Phase 7: Live Terminal & News. "
            "Phase 8: Paper Trading & Simulated Execution."
        ),
        version=config.yaml.get("app", {}).get("version", "0.8.0"),
        lifespan=lifespan,
    )

    # Secure CORS configuration: Restrict to explicit domains or configurable environment origins
    cors_origins_env = os.getenv("CORS_ORIGINS", "")
    if cors_origins_env.strip():
        allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
    else:
        # Default trusted origins for local Streamlit dashboard and dev frontend
        allowed_origins = [
            "http://localhost:8501",
            "http://127.0.0.1:8501",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]

    # Regex pattern to securely allow Streamlit Community Cloud deployments
    origin_regex = os.getenv("CORS_ORIGIN_REGEX", r"^https:\/\/.*\.streamlit\.app$")
    allow_credentials = True
    if allowed_origins == ["*"]:
        allow_credentials = False  # W3C CORS forbids credentials when allow_origins is wildcard '*'

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=origin_regex,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "Accept", "Origin"],
    )

    # Register routers
    app.include_router(auth.router)
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(market.router, prefix="/api/v1/market", tags=["Market Data"])
    app.include_router(options.router, prefix="/api/v1/options", tags=["Options"])
    app.include_router(technical.router, prefix="/api/v1", tags=["Technical Analysis"])
    app.include_router(regime.router, prefix="/api/v1", tags=["Market Regime"])
    app.include_router(strategies.router, prefix="/api/v1", tags=["Options Strategies"])
    app.include_router(backtest.router, prefix="/api/v1", tags=["Backtesting & Validation"])
    app.include_router(ml.router)
    app.include_router(live.router)
    app.include_router(news.router)
    app.include_router(paper_trading.router)
    app.include_router(data_infrastructure.router)
    app.include_router(research.router)

    return app




def _seed_underlyings():
    """Seed the underlyings table from settings.yaml."""
    try:
        from src.database.repository import Repository
        config = get_config()
        repo = Repository()
        for u in config.enabled_underlyings:
            repo.upsert_underlying(
                symbol=u["symbol"],
                name=u["name"],
                exchange=u.get("exchange", "NSE"),
                instrument_type=u.get("instrument_type", "INDEX"),
                lot_size=u.get("lot_size", 1),
                tick_size=u.get("tick_size", 0.05),
            )
        repo.close()
        logger.info(f"Seeded {len(config.enabled_underlyings)} underlyings")
    except Exception as e:
        logger.warning(f"Could not seed underlyings: {e}")


# Application instance
app = create_app()
