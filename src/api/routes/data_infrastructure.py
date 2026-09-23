"""
Phase 9 — Data Infrastructure & Provenance API Endpoints.

Exposes REST endpoints for:
- Providers discovery & health
- Capability verifications
- Market quotes with strict provenance
- Intraday & daily candles
- Options chain & coverage
- Data quality & sufficiency status
- Immutable dataset snapshots
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from src.data_infrastructure.calendar import NSEMarketCalendar
from src.data_infrastructure.executable_validator import ExecutableQuoteValidator
from src.data_infrastructure.health_monitor import ProviderHealthMonitor
from src.data_infrastructure.lineage import DatasetSnapshotManager
from src.data_infrastructure.models import DataStatus
from src.data_infrastructure.providers.bhavcopy_provider import NSEBhavcopyHistoricalProvider
from src.data_infrastructure.providers.market_provider import Phase9YFinanceProvider
from src.data_infrastructure.providers.options_provider import Phase9OptionsProvider
from src.data_infrastructure.providers.scorecard import build_bhavcopy_scorecard, build_yfinance_scorecard
from src.data_infrastructure.providers.verification import ProviderVerificationEngine
from src.data_infrastructure.sufficiency_gate import DataSufficiencyGate

router = APIRouter(prefix="/api/v1", tags=["Data Infrastructure"])

_market_provider = Phase9YFinanceProvider()
_options_provider = Phase9OptionsProvider()
_bhavcopy_provider = NSEBhavcopyHistoricalProvider()


@router.get("/data/providers")
def get_providers():
    """Returns active providers, their capabilities, and 15-dimension scorecards."""
    return {
        "providers": [
            {
                "name": _market_provider.provider_name,
                "type": _market_provider.provider_type,
                "capabilities": _market_provider.capabilities(),
                "scorecard": build_yfinance_scorecard().to_dict(),
                "licensing": _market_provider.licensing_info(),
            },
            {
                "name": _options_provider.provider_name,
                "type": _options_provider.provider_type,
                "capabilities": _options_provider.capabilities(),
                "licensing": _options_provider.licensing_info(),
            },
            {
                "name": _bhavcopy_provider.provider_name,
                "type": _bhavcopy_provider.provider_type,
                "capabilities": _bhavcopy_provider.capabilities(),
                "scorecard": build_bhavcopy_scorecard().to_dict(),
                "licensing": _bhavcopy_provider.licensing_info(),
            },
        ]
    }


@router.get("/data/providers/health")
def get_providers_health():
    """Evaluates real-time health across all active providers."""
    return {
        "providers_health": [
            ProviderHealthMonitor.evaluate_provider_health(_market_provider),
            ProviderHealthMonitor.evaluate_provider_health(_options_provider),
            ProviderHealthMonitor.evaluate_provider_health(_bhavcopy_provider),
        ],
        "failover_history": ProviderHealthMonitor.get_transition_history(),
    }


@router.get("/data/providers/verifications")
def get_provider_verifications(provider: Optional[str] = None):
    """Returns evidence-based verification history for providers."""
    return {
        "verifications": ProviderVerificationEngine.get_latest_verifications(provider),
    }


@router.get("/market/quote/{symbol}")
def get_market_quote(symbol: str):
    """
    Fetches normalized market observation for symbol with complete provenance.
    Discloses whether observation contains executable Bid/Ask or is valuation-only LTP.
    """
    obs = _market_provider.get_quote(symbol)
    if not obs:
        raise HTTPException(status_code=404, detail=f"Market observation unavailable for {symbol}")

    is_open, _ = NSEMarketCalendar.is_fill_eligible()
    validation = ExecutableQuoteValidator.validate_for_execution(
        side="BUY",
        bid=obs.bid_price,
        ask=obs.ask_price,
        ltp=obs.last_price,
        data_status=obs.data_status,
        is_market_open=is_open,
    )

    return {
        "symbol": obs.symbol,
        "provider": obs.provider,
        "last_price": obs.last_price,
        "bid_price": obs.bid_price,
        "ask_price": obs.ask_price,
        "volume": obs.volume,
        "data_status": obs.data_status.value,
        "is_executable": validation.is_executable,
        "execution_rejection_reason": validation.rejection_code,
        "price_classification": "VALUATION_MARK_ONLY" if not validation.is_executable else "EXECUTION_QUOTE",
        "timestamps": {
            "provider_timestamp": obs.timestamps.provider_timestamp.isoformat(),
            "received_timestamp": obs.timestamps.received_timestamp.isoformat(),
            "processed_timestamp": obs.timestamps.processed_timestamp.isoformat(),
            "latencies": obs.timestamps.calculate_latencies(),
        },
    }


@router.get("/market/candles/{symbol}")
def get_market_candles(
    symbol: str,
    timeframe: str = Query("1m", pattern="^(1m|3m|5m|15m|30m|1h|1D)$"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Fetches intraday or daily candles with derived_interval disclosure."""
    candles = _market_provider.get_intraday_candles(symbol, interval=timeframe)
    return {
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "count": len(candles[:limit]),
        "candles": candles[:limit],
    }


@router.get("/options/chain/{underlying}")
def get_options_chain(underlying: str):
    """
    Returns option chain snapshot. Truthfully reports UNAVAILABLE if live options feed unverified.
    """
    chain = _options_provider.get_option_chain(underlying, expiry=date.today())
    if not chain:
        return {
            "underlying": underlying.upper(),
            "status": DataStatus.UNAVAILABLE.value,
            "reason": "Live options provider feed unverified. Zero synthetic chains generated.",
            "rows": [],
        }
    return chain.model_dump()


@router.get("/options/coverage/{underlying}")
def get_options_coverage(underlying: str):
    """Audits historical and live options coverage for underlying."""
    audit = _bhavcopy_provider.audit_dataset_quality(underlying, date(2025, 1, 1), date.today())
    return {
        "underlying": underlying.upper(),
        "historical_coverage": audit,
        "live_options_status": "BLOCKED — LIVE OPTIONS DATA NOT VERIFIED",
        "executable_bid_ask_coverage_pct": 0.0,
    }


@router.get("/data/status")
def get_data_infrastructure_status():
    """Comprehensive readiness and capability gate evaluation."""
    is_market_open, market_state = NSEMarketCalendar.is_fill_eligible()
    evaluations = DataSufficiencyGate.evaluate_all(
        symbol="NIFTY",
        trading_sessions_count=60,
        option_quotes_count=50,
        bid_ask_coverage_pct=0.0,
        iv_coverage_pct=0.0,
        is_live_options_verified=False,
        is_live_bid_ask_available=False,
    )

    return {
        "market_state": market_state,
        "is_market_open": is_market_open,
        "safety_guard": {
            "ALLOW_LIVE_EXECUTION": False,
            "BROKER_CONNECTIONS": "NONE",
            "OPTIONS_PAPER_TRADING": "BLOCKED",
            "AUTO_PAPER_ORDER_SUBMISSION": False,
        },
        "capability_gates": {k: {"status": v.status, "reasons": v.reasons} for k, v in evaluations.items()},
    }


@router.get("/data/datasets")
def list_datasets():
    """Lists registered immutable dataset snapshots."""
    return {
        "datasets": [
            {
                "dataset_id": "NSE_NIFTY_DAILY_EOD",
                "version": "v1.0",
                "provider": "YFINANCE",
                "description": "Historical NIFTY 50 Daily OHLCV bars.",
                "quality_status": "PARTIALLY_VALIDATED",
            },
            {
                "dataset_id": "NSE_BHAVCOPY_OPTIONS_EOD",
                "version": "v1.0",
                "provider": "NSE_BHAVCOPY_ARCHIVE",
                "description": "Historical NSE Options EOD Settlement archives (LTP/OI/Volume, 0% Bid/Ask).",
                "quality_status": "PARTIALLY_VALIDATED",
            }
        ]
    }
