"""
Health check endpoint.

Reports system health, provider status, and data freshness.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.ingestion.provider_factory import get_available_providers
from src.utils.config import get_config
from src.utils.time_utils import is_market_open, now_ist

router = APIRouter()


@router.get("/health")
def health_check():
    """System health check."""
    config = get_config()
    now = now_ist()

    return {
        "status": "healthy",
        "timestamp": now.isoformat(),
        "version": config.yaml.get("app", {}).get("version", "0.1.0"),
        "phase": 1,
        "market_open": is_market_open(),
        "providers": {
            "market_data": config.env.market_data_provider,
            "options_data": config.env.options_data_provider,
            "available": get_available_providers(),
        },
        "database": {
            "url_type": "postgresql" if "postgresql" in config.env.database_url else "sqlite",
        },
    }
