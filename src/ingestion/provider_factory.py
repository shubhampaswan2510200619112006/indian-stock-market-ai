"""
Provider factory — creates the appropriate data providers based on config.

Supports registration of new providers without modifying existing code.
Adding a new provider (e.g., Kite Connect):
1. Implement MarketDataProvider and/or OptionsDataProvider
2. Register it in the REGISTRY dicts below
3. Set MARKET_DATA_PROVIDER=kite in .env
"""

from __future__ import annotations

from typing import Type

from src.ingestion.base import (
    MarketDataProvider,
    OptionsDataProvider,
)
from src.utils.config import get_config
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Provider registries
# Extend these to add new providers without changing factory logic.
# ---------------------------------------------------------------------------
MARKET_PROVIDER_REGISTRY: dict[str, Type[MarketDataProvider]] = {}
OPTIONS_PROVIDER_REGISTRY: dict[str, Type[OptionsDataProvider]] = {}


def _register_defaults() -> None:
    """Register the built-in providers."""
    from src.ingestion.nse_provider import NSEProvider
    from src.ingestion.yfinance_provider import YFinanceProvider

    # NSE direct — provides both market quotes and option chains
    MARKET_PROVIDER_REGISTRY["nse"] = NSEProvider
    OPTIONS_PROVIDER_REGISTRY["nse"] = NSEProvider

    # yfinance — market quotes and OHLCV only (no option chains)
    MARKET_PROVIDER_REGISTRY["yfinance"] = YFinanceProvider

    # Phase 16: Kite Connect — MARKET DATA ONLY
    # These providers are registered but will degrade safely if credentials absent.
    # They MUST NOT be used for trading or order execution.
    try:
        from src.ingestion.kite_provider import KiteProvider
        MARKET_PROVIDER_REGISTRY["kite"] = KiteProvider
        OPTIONS_PROVIDER_REGISTRY["kite"] = KiteProvider
    except Exception as exc:
        logger.warning(f"KiteProvider registration failed (optional): {exc}")

    # Phase 16: Upstox — MARKET DATA ONLY (not a silent fallback for Kite)
    try:
        from src.ingestion.upstox_provider import UpstoxProvider
        MARKET_PROVIDER_REGISTRY["upstox"] = UpstoxProvider
    except Exception as exc:
        logger.warning(f"UpstoxProvider registration failed (optional): {exc}")

    # Phase 17A: Angel One SmartAPI — MARKET DATA + OPTIONS DATA
    try:
        from src.ingestion.angelone_provider import AngelOneProvider
        MARKET_PROVIDER_REGISTRY["angelone"] = AngelOneProvider
        OPTIONS_PROVIDER_REGISTRY["angelone"] = AngelOneProvider
    except Exception as exc:
        logger.warning(f"AngelOneProvider registration failed (optional): {exc}")


def register_market_provider(name: str, cls: Type[MarketDataProvider]) -> None:
    """Register a custom market data provider."""
    MARKET_PROVIDER_REGISTRY[name.lower()] = cls
    logger.info(f"Registered market provider: {name}")


def register_options_provider(name: str, cls: Type[OptionsDataProvider]) -> None:
    """Register a custom options data provider."""
    OPTIONS_PROVIDER_REGISTRY[name.lower()] = cls
    logger.info(f"Registered options provider: {name}")


def get_market_provider() -> MarketDataProvider:
    """
    Create and return the configured market data provider.

    Reads MARKET_DATA_PROVIDER from .env/config.
    Falls back to 'nse' if not configured.
    """
    if not MARKET_PROVIDER_REGISTRY:
        _register_defaults()

    config = get_config()
    provider_name = config.env.market_data_provider.lower()

    if provider_name not in MARKET_PROVIDER_REGISTRY:
        available = ", ".join(MARKET_PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown market data provider: '{provider_name}'. "
            f"Available: {available}. "
            f"Set MARKET_DATA_PROVIDER in .env to one of these."
        )

    cls = MARKET_PROVIDER_REGISTRY[provider_name]
    instance = cls()
    logger.info(f"Using market data provider: {instance.provider_name} ({provider_name})")
    return instance


# Alias for backward compatibility
get_market_data_provider = get_market_provider


def get_options_provider() -> OptionsDataProvider:
    """
    Create and return the configured options data provider.

    Reads OPTIONS_DATA_PROVIDER from .env/config.
    Falls back to 'nse' if not configured.
    """
    if not OPTIONS_PROVIDER_REGISTRY:
        _register_defaults()

    config = get_config()
    provider_name = config.env.options_data_provider.lower()

    if provider_name not in OPTIONS_PROVIDER_REGISTRY:
        available = ", ".join(OPTIONS_PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown options data provider: '{provider_name}'. "
            f"Available: {available}. "
            f"Set OPTIONS_DATA_PROVIDER in .env to one of these."
        )

    cls = OPTIONS_PROVIDER_REGISTRY[provider_name]
    logger.info(f"Using options data provider: {provider_name}")
    return cls()


def get_available_providers() -> dict[str, list[str]]:
    """Get all registered provider names."""
    if not MARKET_PROVIDER_REGISTRY:
        _register_defaults()
    return {
        "market": list(MARKET_PROVIDER_REGISTRY.keys()),
        "options": list(OPTIONS_PROVIDER_REGISTRY.keys()),
    }


def get_intraday_provider(preferred: str = "kite") -> MarketDataProvider:
    """
    Return the requested intraday provider for MARKET DATA ONLY.

    IMPORTANT: This is NOT a fallback chain. If 'preferred' is not READY,
    this function returns the requested provider with its UNAVAILABLE state —
    it does NOT silently substitute another provider.

    The caller must inspect provider.capability_report to understand what
    data is actually available before using the provider.

    Args:
        preferred: 'kite' or 'upstox'. Default 'kite'.

    Returns:
        A MarketDataProvider instance. Caller must check capability_report.

    Raises:
        ValueError: If the requested provider is not registered.
    """
    if not MARKET_PROVIDER_REGISTRY:
        _register_defaults()

    provider_name = preferred.lower()
    if provider_name not in MARKET_PROVIDER_REGISTRY:
        available = ", ".join(MARKET_PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Intraday provider '{provider_name}' not registered. "
            f"Available: {available}."
        )

    cls = MARKET_PROVIDER_REGISTRY[provider_name]
    provider = cls()
    logger.info(
        f"Intraday provider '{provider_name}' created. "
        f"Capability summary: {getattr(provider, 'capability_report', {}).summary() if hasattr(provider, 'capability_report') else 'N/A'}"
    )
    return provider
