"""
Phase 16 — Data Ingestion Scheduler.

CRITICAL CONSTRAINTS:
1. This scheduler handles DATA INGESTION ONLY.
2. It MUST NOT and CANNOT schedule:
   - Order placement, modification, or cancellation
   - Execution of trading strategies
   - Paper order submission (AUTO_PAPER_ORDER_SUBMISSION is hardcoded False)
   - Live trading (ALLOW_LIVE_EXECUTION is hardcoded False)
3. scheduler.enabled defaults to False in config/settings.yaml.
   The scheduler will NOT start unless explicitly enabled.
4. Each job function is restricted to data fetching and storage only.
5. Any attempt to call execution endpoints from a job will be blocked
   by the provider-level execution guard.

Implementation uses APScheduler (already in requirements.txt).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from zoneinfo import ZoneInfo

from src.utils.config import get_config
from src.utils.logging_config import get_logger
from src.utils.time_utils import is_market_open, is_trading_day, now_ist

logger = get_logger(__name__)

IST = ZoneInfo("Asia/Kolkata")

# =============================================================================
# Safety guard — any job that attempts trading raises immediately
# =============================================================================

_FORBIDDEN_JOB_KEYWORDS = [
    "order", "execute", "trade", "paper_order", "live_order",
    "buy", "sell", "submit_order",
]


def _validate_job_name(name: str) -> None:
    """Raise if job name contains execution-related keywords."""
    lower = name.lower()
    for keyword in _FORBIDDEN_JOB_KEYWORDS:
        if keyword in lower:
            raise ValueError(
                f"BLOCKED: Attempted to schedule a job with execution-related name: '{name}'. "
                f"The scheduler is for DATA INGESTION ONLY. "
                f"Forbidden keyword: '{keyword}'"
            )


# =============================================================================
# Job wrapper — logs job execution, catches all exceptions safely
# =============================================================================

def _safe_job_wrapper(job_fn: Callable, job_name: str) -> Callable:
    """Wrap a job function with logging and exception safety."""
    def wrapped() -> None:
        start = now_ist()
        logger.info(f"[Scheduler] Starting job: {job_name} at {start.isoformat()}")
        try:
            job_fn()
            duration = (now_ist() - start).total_seconds()
            logger.info(f"[Scheduler] Job '{job_name}' completed in {duration:.1f}s")
        except Exception as exc:
            logger.error(f"[Scheduler] Job '{job_name}' failed: {exc}", exc_info=True)
    wrapped.__name__ = job_name
    return wrapped


# =============================================================================
# Ingestion job functions (data only)
# =============================================================================

def _job_intraday_candles() -> None:
    """
    Intraday candle ingestion job.
    DATA INGESTION ONLY — no trading, no orders.
    """
    if not is_market_open():
        logger.debug("[Scheduler] Intraday job: market closed, skipping")
        return

    config = get_config()
    scheduler_cfg = config.yaml.get("scheduler", {})
    intraday_cfg = scheduler_cfg.get("intraday", {})
    symbols: List[str] = intraday_cfg.get("symbols", ["NIFTY", "BANKNIFTY", "FINNIFTY"])
    provider_name: str = config.env.market_data_provider.lower()

    logger.info(f"[Scheduler] Intraday candle fetch: symbols={symbols}, provider={provider_name}")

    try:
        from src.ingestion.provider_factory import get_intraday_provider
        provider = get_intraday_provider(preferred=provider_name if provider_name in ("kite", "upstox") else "kite")
        report = getattr(provider, "capability_report", None)
        if report and not report.any_ready():
            logger.warning(f"[Scheduler] Intraday provider '{provider_name}' has no READY capabilities — skipping fetch")
            return

        today = now_ist().date()
        for symbol in symbols:
            try:
                df = provider.get_ohlcv(symbol, today, today, interval="1m")
                if not df.empty:
                    logger.info(f"[Scheduler] Intraday: {symbol} — {len(df)} candles fetched")
                    # Note: persisting to DB is handled by repository layer (not implemented here)
                    # This job is responsible only for triggering the fetch.
            except Exception as exc:
                logger.warning(f"[Scheduler] Intraday fetch failed for {symbol}: {exc}")
    except ImportError as exc:
        logger.error(f"[Scheduler] Cannot import intraday provider: {exc}")


def _job_fii_dii() -> None:
    """
    FII/DII flow data ingestion job.
    DATA INGESTION ONLY.
    """
    logger.info("[Scheduler] FII/DII flow fetch started")
    try:
        from src.ingestion.fii_dii_fetcher import FIIDIIFetcher
        fetcher = FIIDIIFetcher()
        records = fetcher.fetch_latest()
        logger.info(f"[Scheduler] FII/DII: {len(records)} records fetched")
        # Persistence: caller / job framework handles DB write via repository
    except ImportError as exc:
        logger.error(f"[Scheduler] FII/DII import error: {exc}")
    except Exception as exc:
        logger.error(f"[Scheduler] FII/DII job error: {exc}")


def _job_bhavcopy() -> None:
    """
    NSE Bhavcopy EOD options data ingestion.
    DATA INGESTION ONLY — no bid/ask fabrication.
    """
    logger.info("[Scheduler] Bhavcopy ingestion job started")
    try:
        from src.ingestion.bhavcopy_downloader import NSEBhavcopyCandleDownloader
        downloader = NSEBhavcopyCandleDownloader()
        yesterday = now_ist().date()
        import datetime as dt
        yesterday = yesterday - dt.timedelta(days=1)
        result = downloader.download_day(yesterday)
        staging = result.staging_record
        logger.info(
            f"[Scheduler] Bhavcopy {yesterday}: status={staging.download_status}, "
            f"records={staging.records_inserted}, sha256={staging.sha256_hash[:16]}…"
        )
    except ImportError as exc:
        logger.error(f"[Scheduler] Bhavcopy import error: {exc}")
    except Exception as exc:
        logger.error(f"[Scheduler] Bhavcopy job error: {exc}")


def _job_macro_features() -> None:
    """
    Macro features ingestion job (India VIX, USD/INR, crude, GIFT Nifty).
    DATA INGESTION ONLY.
    """
    logger.info("[Scheduler] Macro features fetch started")
    try:
        from src.ingestion.macro_features_fetcher import MacroFeaturesFetcher
        fetcher = MacroFeaturesFetcher()
        snapshot = fetcher.fetch()
        logger.info(
            f"[Scheduler] Macro: VIX={snapshot.india_vix}, "
            f"USD/INR={snapshot.usd_inr}, WTI={snapshot.crude_wti}, "
            f"quality={snapshot.data_quality}"
        )
    except ImportError as exc:
        logger.error(f"[Scheduler] Macro import error: {exc}")
    except Exception as exc:
        logger.error(f"[Scheduler] Macro job error: {exc}")


# =============================================================================
# Scheduler class
# =============================================================================

class IngestionScheduler:
    """
    Data ingestion scheduler using APScheduler.

    Master on/off switch: scheduler.enabled in config/settings.yaml.
    Default: DISABLED. Must be explicitly set to true to start.

    This scheduler ONLY handles:
    - Intraday candle fetching
    - FII/DII flow fetching
    - NSE Bhavcopy EOD ingestion
    - Macro features fetching

    It MUST NOT schedule any trading, order, or execution jobs.
    """

    def __init__(self) -> None:
        self._scheduler = None
        self._is_started = False
        self._config_loaded = False
        self._scheduler_cfg: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        config = get_config()
        self._scheduler_cfg = config.yaml.get("scheduler", {})
        self._config_loaded = True

    @property
    def is_enabled(self) -> bool:
        """True only if scheduler.enabled is explicitly true in config."""
        return bool(self._scheduler_cfg.get("enabled", False))

    @property
    def is_running(self) -> bool:
        return self._is_started and self._scheduler is not None

    def start(self) -> None:
        """
        Start the scheduler if enabled in config.
        Does nothing if scheduler.enabled = false (the default).
        Raises RuntimeError if already running.
        """
        if not self.is_enabled:
            logger.info(
                "[Scheduler] Not started: scheduler.enabled = false in config/settings.yaml. "
                "Set to true to enable automated data ingestion."
            )
            return

        if self._is_started:
            raise RuntimeError("IngestionScheduler is already running. Call stop() first.")

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            from apscheduler.triggers.interval import IntervalTrigger
        except ImportError:
            raise ImportError(
                "APScheduler not installed. Run: pip install apscheduler>=3.10.0"
            )

        tz = self._scheduler_cfg.get("timezone", "Asia/Kolkata")
        self._scheduler = BackgroundScheduler(timezone=tz)

        # Register jobs according to config
        self._register_jobs(tz)

        self._scheduler.start()
        self._is_started = True
        logger.info("[Scheduler] Ingestion scheduler started (DATA INGESTION ONLY)")

    def _register_jobs(self, tz: str) -> None:
        """Register all enabled data ingestion jobs."""
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.interval import IntervalTrigger

        cfg = self._scheduler_cfg

        # Intraday candle job
        intraday_cfg = cfg.get("intraday", {})
        if intraday_cfg.get("enabled", False):
            _validate_job_name("intraday_candle_fetch")
            interval_min = int(intraday_cfg.get("interval_minutes", 5))
            self._scheduler.add_job(
                _safe_job_wrapper(_job_intraday_candles, "intraday_candle_fetch"),
                trigger=IntervalTrigger(minutes=interval_min, timezone=tz),
                id="intraday_candle_fetch",
                name="Intraday Candle Fetch (DATA ONLY)",
                replace_existing=True,
                misfire_grace_time=60,
            )
            logger.info(f"[Scheduler] Registered: intraday_candle_fetch every {interval_min}m")

        # FII/DII job
        fii_cfg = cfg.get("fii_dii", {})
        if fii_cfg.get("enabled", False):
            _validate_job_name("fii_dii_fetch")
            time_ist = fii_cfg.get("time_ist", "17:30")
            h, m = map(int, time_ist.split(":"))
            self._scheduler.add_job(
                _safe_job_wrapper(_job_fii_dii, "fii_dii_fetch"),
                trigger=CronTrigger(hour=h, minute=m, day_of_week="mon-fri", timezone=tz),
                id="fii_dii_fetch",
                name="FII/DII Flow Fetch (DATA ONLY)",
                replace_existing=True,
            )
            logger.info(f"[Scheduler] Registered: fii_dii_fetch at {time_ist} IST (Mon-Fri)")

        # Bhavcopy job
        bhavcopy_cfg = cfg.get("bhavcopy", {})
        if bhavcopy_cfg.get("enabled", False):
            _validate_job_name("bhavcopy_ingest")
            time_ist = bhavcopy_cfg.get("time_ist", "20:00")
            h, m = map(int, time_ist.split(":"))
            self._scheduler.add_job(
                _safe_job_wrapper(_job_bhavcopy, "bhavcopy_ingest"),
                trigger=CronTrigger(hour=h, minute=m, day_of_week="mon-fri", timezone=tz),
                id="bhavcopy_ingest",
                name="Bhavcopy EOD Ingest (DATA ONLY)",
                replace_existing=True,
            )
            logger.info(f"[Scheduler] Registered: bhavcopy_ingest at {time_ist} IST (Mon-Fri)")

        # Macro features job
        macro_cfg = cfg.get("macro", {})
        if macro_cfg.get("enabled", False):
            _validate_job_name("macro_features_fetch")
            time_ist = macro_cfg.get("time_ist", "09:00")
            h, m = map(int, time_ist.split(":"))
            self._scheduler.add_job(
                _safe_job_wrapper(_job_macro_features, "macro_features_fetch"),
                trigger=CronTrigger(hour=h, minute=m, day_of_week="mon-fri", timezone=tz),
                id="macro_features_fetch",
                name="Macro Features Fetch (DATA ONLY)",
                replace_existing=True,
            )
            # Also schedule intraday macro refresh if configured
            intraday_macro_interval = int(macro_cfg.get("intraday_interval_minutes", 60))
            self._scheduler.add_job(
                _safe_job_wrapper(_job_macro_features, "macro_features_intraday"),
                trigger=IntervalTrigger(minutes=intraday_macro_interval, timezone=tz),
                id="macro_features_intraday",
                name="Macro Features Intraday Refresh (DATA ONLY)",
                replace_existing=True,
            )
            logger.info(f"[Scheduler] Registered: macro_features_fetch at {time_ist} IST + every {intraday_macro_interval}m")

    def stop(self) -> None:
        """Stop the scheduler if running."""
        if self._scheduler is not None and self._is_started:
            self._scheduler.shutdown(wait=False)
            self._is_started = False
            logger.info("[Scheduler] Ingestion scheduler stopped")

    def get_job_ids(self) -> List[str]:
        """Return list of registered job IDs."""
        if self._scheduler is None:
            return []
        return [job.id for job in self._scheduler.get_jobs()]

    def status(self) -> Dict[str, Any]:
        """Return scheduler status summary."""
        return {
            "enabled_in_config": self.is_enabled,
            "is_running": self.is_running,
            "job_count": len(self.get_job_ids()),
            "job_ids": self.get_job_ids(),
            "note": (
                "DATA INGESTION ONLY. "
                "ALLOW_LIVE_EXECUTION and AUTO_PAPER_ORDER_SUBMISSION are hardcoded False."
            ),
        }


# =============================================================================
# Singleton accessor
# =============================================================================

_scheduler_instance: Optional[IngestionScheduler] = None


def get_ingestion_scheduler() -> IngestionScheduler:
    """
    Return the singleton IngestionScheduler instance.
    Does NOT start the scheduler — call .start() explicitly.
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = IngestionScheduler()
    return _scheduler_instance
