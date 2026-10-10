"""
Centralized configuration management.

Loads settings from:
1. .env file (secrets, connection strings)
2. config/settings.yaml (application parameters)
3. Environment variable overrides

Uses pydantic-settings for type-safe, validated configuration.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# ---------------------------------------------------------------------------
# Resolve project root (two levels up from src/utils/config.py)
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _THIS_DIR.parent.parent

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------------
# Pydantic Settings — populated from environment variables / .env
# ---------------------------------------------------------------------------
class AppSettings(BaseSettings):
    """Environment-driven settings (secrets, connection strings)."""

    # Database
    database_url: str = Field(
        default="sqlite:///./data/indian_options.db",
        description="SQLAlchemy database URL. SQLite for dev, PostgreSQL for production.",
    )

    # Data providers
    market_data_provider: str = Field(default="nse")
    options_data_provider: str = Field(default="nse")

    # Rate limiting
    rate_limit_delay_seconds: float = Field(default=2.0)
    cache_ttl_live_seconds: int = Field(default=60)
    cache_ttl_closed_seconds: int = Field(default=3600)

    # API server
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    # Logging
    log_level: str = Field(default="INFO")

    # Financial
    risk_free_rate: float = Field(default=0.07)

    # Timezone
    timezone: str = Field(default="Asia/Kolkata")

    # Optional broker API keys — all default to empty string
    kite_api_key: str = Field(default="")
    kite_api_secret: str = Field(default="")
    # Kite access token: obtained daily via OAuth. Set in .env — never hardcode.
    kite_access_token: str = Field(default="")
    dhan_client_id: str = Field(default="")
    dhan_access_token: str = Field(default="")
    fyers_app_id: str = Field(default="")
    fyers_secret_key: str = Field(default="")
    angelone_api_key: str = Field(default="")
    angelone_client_id: str = Field(default="")
    angelone_client_pin: str = Field(default="")
    angelone_totp_secret: str = Field(default="")
    breeze_api_key: str = Field(default="")
    breeze_api_secret: str = Field(default="")
    news_api_key: str = Field(default="")
    llm_api_key: str = Field(default="")
    llm_model: str = Field(default="")

    # Phase 16 — Upstox API (market data only)
    upstox_api_key: str = Field(default="")
    upstox_api_secret: str = Field(default="")
    upstox_access_token: str = Field(default="")

    # Phase 16 — Bhavcopy
    # Max trading days to backfill on first run. Configurable; default is conservative.
    bhavcopy_backfill_days: int = Field(default=30)
    # Local directory where raw Bhavcopy archives are stored before parsing.
    bhavcopy_raw_dir: str = Field(default="./data/bhavcopy/raw")

    # Phase 16 — Paid historical options provider key placeholder
    paid_options_provider_key: str = Field(default="")
    paid_options_provider_name: str = Field(default="")

    model_config = {"env_file": str(PROJECT_ROOT / ".env"), "extra": "ignore"}


# ---------------------------------------------------------------------------
# YAML settings — application-level config (non-secret)
# ---------------------------------------------------------------------------
def _load_yaml_settings() -> dict[str, Any]:
    """Load config/settings.yaml from project root."""
    yaml_path = PROJECT_ROOT / "config" / "settings.yaml"
    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


# ---------------------------------------------------------------------------
# Unified config access
# ---------------------------------------------------------------------------
class Config:
    """Unified configuration access combining .env and settings.yaml."""

    def __init__(self) -> None:
        self.env = AppSettings()
        self.yaml = _load_yaml_settings()

    # --- Convenience accessors for YAML sections ---

    @property
    def underlyings(self) -> list[dict[str, Any]]:
        return self.yaml.get("underlyings", [])

    @property
    def enabled_underlyings(self) -> list[dict[str, Any]]:
        return [u for u in self.underlyings if u.get("enabled", False)]

    @property
    def market_config(self) -> dict[str, Any]:
        return self.yaml.get("market", {})

    @property
    def data_freshness_config(self) -> dict[str, Any]:
        return self.yaml.get("data_freshness", {})

    @property
    def option_chain_config(self) -> dict[str, Any]:
        return self.yaml.get("option_chain", {})

    @property
    def costs_config(self) -> dict[str, Any]:
        return self.yaml.get("costs", {})

    def get_underlying(self, symbol: str) -> dict[str, Any] | None:
        """Look up an underlying by symbol."""
        for u in self.underlyings:
            if u["symbol"].upper() == symbol.upper():
                return u
        return None


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Return the singleton Config instance (cached)."""
    return Config()
