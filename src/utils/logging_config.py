"""
Structured logging configuration.

Named logging_config.py to avoid shadowing the stdlib logging module.
Provides JSON-formatted logs for production and human-readable logs for dev.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

from src.utils.config import get_config


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger for the application.

    Args:
        level: Override log level. If None, reads from config/env.

    Returns:
        The configured root logger.
    """
    config = get_config()
    log_level = (level or config.env.log_level).upper()

    # Create a formatter — readable for dev
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))

    # Configure root logger
    root_logger = logging.getLogger("indian_options_ai")
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Remove any existing handlers to avoid duplicates on re-init
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger under the application namespace.

    Usage:
        logger = get_logger(__name__)
        logger.info("Fetching option chain for NIFTY")
    """
    return logging.getLogger(f"indian_options_ai.{name}")
