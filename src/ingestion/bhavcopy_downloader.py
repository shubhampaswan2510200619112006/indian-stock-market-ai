"""
Phase 16 — NSE F&O Bhavcopy Archive Downloader and Ingestion Pipeline.

DATA INTEGRITY RULES (non-negotiable):
1. Raw downloaded archives are preserved UNCHANGED in bhavcopy_raw_dir.
2. Every raw file is SHA256-hashed. Hash is recorded in provenance table.
3. Source URL, retrieval timestamp, file size, and SHA256 are all stored.
4. Normalization is deterministic — same input always produces same output.
5. Ingestion is idempotent — re-running never produces duplicate records.
6. Bid/Ask values are NEVER fabricated. EOD settlement files have no bid/ask.
   All options records from Bhavcopy are tagged as SETTLEMENT_PRICE_ONLY.
7. Records tagged SETTLEMENT_PRICE_ONLY MUST NOT be treated as executable
   bid/ask data by downstream systems.
8. Missing values remain NULL — no silent repair.

Bhavcopy source: NSE India public archives (free, no login required).
URL pattern: https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_YYYYMMDD_F_0000.csv.zip
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple
from zoneinfo import ZoneInfo

import requests

from src.utils.config import get_config
from src.utils.logging_config import get_logger
from src.utils.time_utils import now_ist

logger = get_logger(__name__)

IST = ZoneInfo("Asia/Kolkata")

# NSE FO Bhavcopy URL template (public archive)
_BHAVCOPY_FO_URL_TEMPLATE = (
    "https://nsearchives.nseindia.com/content/fo/"
    "BhavCopy_NSE_FO_0_0_0_{date}_F_0000.csv.zip"
)

# Data status tag for all Bhavcopy-derived records
SETTLEMENT_PRICE_ONLY = "SETTLEMENT_PRICE_ONLY"

# Expected CSV columns in NSE FO Bhavcopy (as of 2024-format)
# Column names may vary; we map by position/name defensively.
_EXPECTED_COLUMNS = [
    "TradDt", "BizDt", "Sgmt", "Src", "FinInstrmTp", "FinInstrmId",
    "ISIN", "TckrSymb", "Undrlng", "UndrlygPric", "OptnTp", "XpryDt",
    "StrkPric", "OpnIntrst", "ChngInOpnIntrst", "TtlTradVol",
    "TtlTrfVal", "SttlmntPric", "New52wkHghs", "New52wkLows",
    "UndrlygOpnIntrst", "ChngInUndrlygOpnIntrst",
]


# =============================================================================
# Provenance record
# =============================================================================

@dataclass
class BhavcopyStagingRecord:
    """
    Provenance record for a single downloaded Bhavcopy archive.
    Stored BEFORE any parsing to ensure raw artifact integrity is recorded first.
    """
    trade_date: date
    source_url: str
    retrieval_timestamp: datetime
    file_size_bytes: int
    sha256_hash: str
    local_raw_path: str
    download_status: str          # "SUCCESS", "NOT_FOUND", "ERROR"
    error_message: str = ""
    parse_status: str = "PENDING" # "PENDING", "SUCCESS", "PARTIAL", "ERROR"
    records_inserted: int = 0
    records_skipped: int = 0


# =============================================================================
# Parsed candle/quote record from Bhavcopy CSV
# =============================================================================

@dataclass
class BhavcopyCandleRecord:
    """
    A single options EOD record parsed from NSE Bhavcopy CSV.

    IMPORTANT:
    - bid_price and ask_price are ALWAYS None (NSE EOD settlement files don't have bid/ask).
    - data_status is SETTLEMENT_PRICE_ONLY.
    - This record MUST NOT be treated as representing an executable bid/ask price.
    """
    trade_date: date
    underlying: str
    expiry_date: Optional[date]
    strike_price: Optional[float]
    option_type: Optional[str]        # "CE" or "PE"
    open_interest: Optional[int]
    change_in_oi: Optional[int]
    volume: Optional[int]
    settlement_price: Optional[float]
    # These are ALWAYS None — do not invent bid/ask
    bid_price: None = field(default=None, init=False)
    ask_price: None = field(default=None, init=False)
    # Provenance
    source: str = "NSE_FO_BHAVCOPY"
    data_status: str = SETTLEMENT_PRICE_ONLY
    data_quality: str = "GOOD"
    underlying_price: Optional[float] = None


# =============================================================================
# SHA256 helpers
# =============================================================================

def sha256_bytes(content: bytes) -> str:
    """Compute SHA256 hex digest of raw bytes."""
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    """Compute SHA256 hex digest of a file on disk."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# =============================================================================
# CSV parser
# =============================================================================

def _parse_date(s: str) -> Optional[date]:
    """Parse a date string from Bhavcopy (YYYY-MM-DD or DD-Mon-YYYY)."""
    if not s or s.strip() == "":
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d-%B-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _safe_float(s: str) -> Optional[float]:
    if s is None or s.strip() in ("", "-", "NA", "N/A"):
        return None
    try:
        return float(s.strip())
    except ValueError:
        return None


def _safe_int(s: str) -> Optional[int]:
    if s is None or s.strip() in ("", "-", "NA", "N/A"):
        return None
    try:
        return int(float(s.strip()))
    except ValueError:
        return None


def parse_bhavcopy_csv(csv_content: str, trade_date: date) -> List[BhavcopyCandleRecord]:
    """
    Parse NSE FO Bhavcopy CSV content into BhavcopyCandleRecord list.

    - Only processes rows where FinInstrmTp is an options type (OPT/CE/PE suffix).
    - bid/ask fields are NEVER populated — they don't exist in EOD data.
    - Missing/invalid values remain None.
    - Rows with no settlement price are retained (None value, not filtered out).

    Args:
        csv_content: Raw CSV string content from the Bhavcopy file.
        trade_date: The trading date this Bhavcopy pertains to.

    Returns:
        List of BhavcopyCandleRecord (may be empty if file has no options rows).
    """
    records: List[BhavcopyCandleRecord] = []
    try:
        reader = csv.DictReader(io.StringIO(csv_content))
        headers = reader.fieldnames or []
        # Normalise header names: strip whitespace
        norm_headers = [h.strip() for h in headers]

        for row in reader:
            # Normalise keys
            norm_row: Dict[str, str] = {k.strip(): v.strip() for k, v in row.items() if k}

            # Only process options rows
            fin_instr_tp = norm_row.get("FinInstrmTp", "").upper()
            segment = norm_row.get("Sgmt", "").upper()
            if fin_instr_tp not in ("OPT", "CE", "PE"):
                # Fallback: check FinInstrmId suffix for FO-segment rows ONLY.
                # CRITICAL: must also require digits in the ID (contract encoding).
                # Without this, stock names like "RELIANCE" match endswith("CE")
                # because RELIAN-CE ends in "CE". We guard with:
                # 1. Must be FO/NFO segment (not CM cash market)
                # 2. FinInstrmId must contain at least one digit (expiry/strike encoding)
                fin_instr_id = norm_row.get("FinInstrmId", "").upper()
                is_fo_segment = segment in ("FO", "NFO", "F&O")
                id_looks_like_option = (
                    any(c.isdigit() for c in fin_instr_id)
                    and (fin_instr_id.endswith("CE") or fin_instr_id.endswith("PE"))
                )
                if not (is_fo_segment and id_looks_like_option):
                    continue


            # Option type: from OptnTp or from FinInstrmId suffix
            opt_tp = norm_row.get("OptnTp", "").strip().upper()
            if opt_tp not in ("CE", "PE"):
                fin_instr_id = norm_row.get("FinInstrmId", "")
                if fin_instr_id.upper().endswith("CE"):
                    opt_tp = "CE"
                elif fin_instr_id.upper().endswith("PE"):
                    opt_tp = "PE"
                else:
                    opt_tp = None

            # Underlying symbol
            underlying = norm_row.get("TckrSymb") or norm_row.get("Undrlng") or ""
            underlying = underlying.strip().upper()

            # Expiry date
            expiry_str = norm_row.get("XpryDt", "")
            expiry = _parse_date(expiry_str)

            # Strike price
            strike = _safe_float(norm_row.get("StrkPric", ""))

            # OI, change in OI, volume
            oi = _safe_int(norm_row.get("OpnIntrst", ""))
            chng_oi = _safe_int(norm_row.get("ChngInOpnIntrst", ""))
            vol = _safe_int(norm_row.get("TtlTradVol", ""))

            # Settlement price (NO bid/ask in EOD data — field stays None always)
            sttl_price = _safe_float(norm_row.get("SttlmntPric", ""))

            # Underlying price
            undrlng_price = _safe_float(norm_row.get("UndrlygPric", ""))

            # Data quality: PARTIAL if key fields missing
            missing = sum(
                1 for v in [expiry, strike, opt_tp, sttl_price]
                if v is None
            )
            quality = "GOOD" if missing == 0 else "PARTIAL"

            records.append(BhavcopyCandleRecord(
                trade_date=trade_date,
                underlying=underlying,
                expiry_date=expiry,
                strike_price=strike,
                option_type=opt_tp,
                open_interest=oi,
                change_in_oi=chng_oi,
                volume=vol,
                settlement_price=sttl_price,
                underlying_price=undrlng_price,
                data_quality=quality,
            ))
    except Exception as exc:
        logger.error(f"Bhavcopy CSV parse error: {exc}")
    return records


# =============================================================================
# Downloader
# =============================================================================

class BhavcopyStagingResult:
    """Result of attempting to download and stage a single day's Bhavcopy."""

    def __init__(self, record: BhavcopyStagingRecord, candles: List[BhavcopyCandleRecord]):
        self.staging_record = record
        self.candles = candles


class NSEBhavcopyCandleDownloader:
    """
    Downloads NSE FO Bhavcopy archives, verifies integrity, and parses options data.

    Architecture:
    1. Download → raw bytes (unchanged)
    2. SHA256 hash raw bytes
    3. Save raw archive to disk (UNCHANGED)
    4. Record provenance (URL, timestamp, size, hash)
    5. Parse CSV → BhavcopyCandleRecord list
    6. Return (provenance, candles) for caller to persist

    The downloader does NOT write to the options_quotes database table itself —
    that is done by the caller / ingestion pipeline, which decides idempotency.
    """

    def __init__(
        self,
        raw_dir: Optional[str] = None,
        url_template: str = _BHAVCOPY_FO_URL_TEMPLATE,
    ) -> None:
        config = get_config()
        self._raw_dir = Path(raw_dir or config.env.bhavcopy_raw_dir)
        self._raw_dir.mkdir(parents=True, exist_ok=True)
        self._url_template = url_template
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (compatible; NSE-Bhavcopy-Ingestion-Bot/1.0; "
                "Research-Data-Only; +https://nsearchives.nseindia.com)"
            ),
            "Accept": "application/zip, application/octet-stream",
        })

    def _make_url(self, trade_date: date) -> str:
        return self._url_template.format(date=trade_date.strftime("%Y%m%d"))

    def _local_path(self, trade_date: date) -> Path:
        """Deterministic local path for the raw archive."""
        return self._raw_dir / f"BhavCopy_FO_{trade_date.strftime('%Y%m%d')}.csv.zip"

    def download_day(self, trade_date: date) -> BhavcopyStagingResult:
        """
        Download, hash, and parse Bhavcopy for one trading date.

        Returns BhavcopyStagingResult with provenance record + parsed candles.
        If the file already exists locally (same path), the local file is reused
        (its hash is verified against the on-disk copy — not re-downloaded).
        If NSE returns 404, staging_record.download_status = 'NOT_FOUND'.
        """
        url = self._make_url(trade_date)
        local_path = self._local_path(trade_date)
        retrieval_ts = now_ist()

        staging = BhavcopyStagingRecord(
            trade_date=trade_date,
            source_url=url,
            retrieval_timestamp=retrieval_ts,
            file_size_bytes=0,
            sha256_hash="",
            local_raw_path=str(local_path),
            download_status="PENDING",
        )

        # If already downloaded locally, use it (idempotent)
        if local_path.exists():
            raw_bytes = local_path.read_bytes()
            staging.file_size_bytes = len(raw_bytes)
            staging.sha256_hash = sha256_bytes(raw_bytes)
            staging.download_status = "SUCCESS (CACHED)"
            logger.info(f"Bhavcopy {trade_date} found locally: {local_path} (SHA256: {staging.sha256_hash[:16]}…)")
        else:
            try:
                resp = self._session.get(url, timeout=30)
                if resp.status_code == 404:
                    staging.download_status = "NOT_FOUND"
                    staging.error_message = f"NSE returned 404 for {url}"
                    logger.info(f"Bhavcopy {trade_date}: NOT_FOUND (404) — may be holiday or not yet published")
                    return BhavcopyStagingResult(staging, [])

                resp.raise_for_status()
                raw_bytes = resp.content

                # Record before saving
                staging.file_size_bytes = len(raw_bytes)
                staging.sha256_hash = sha256_bytes(raw_bytes)

                # Save raw bytes UNCHANGED
                local_path.write_bytes(raw_bytes)
                staging.download_status = "SUCCESS"
                logger.info(
                    f"Bhavcopy {trade_date} downloaded: {staging.file_size_bytes} bytes "
                    f"SHA256={staging.sha256_hash[:16]}…"
                )
            except requests.exceptions.HTTPError as exc:
                staging.download_status = "ERROR"
                staging.error_message = str(exc)
                logger.warning(f"Bhavcopy {trade_date}: HTTP error: {exc}")
                return BhavcopyStagingResult(staging, [])
            except requests.exceptions.RequestException as exc:
                staging.download_status = "ERROR"
                staging.error_message = str(exc)
                logger.warning(f"Bhavcopy {trade_date}: Download error: {exc}")
                return BhavcopyStagingResult(staging, [])

        # Parse the zip
        candles = self._parse_zip(raw_bytes if 'raw_bytes' in dir() else local_path.read_bytes(), trade_date)
        staging.parse_status = "SUCCESS" if candles else "PARTIAL"
        staging.records_inserted = len(candles)

        return BhavcopyStagingResult(staging, candles)

    def _parse_zip(self, raw_bytes: bytes, trade_date: date) -> List[BhavcopyCandleRecord]:
        """Extract CSV from zip and parse it. Returns empty list on any error."""
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                if not csv_names:
                    logger.warning(f"Bhavcopy {trade_date}: no CSV file found inside zip")
                    return []
                csv_content = zf.read(csv_names[0]).decode("utf-8", errors="replace")
            return parse_bhavcopy_csv(csv_content, trade_date)
        except zipfile.BadZipFile as exc:
            logger.error(f"Bhavcopy {trade_date}: bad zip file: {exc}")
            return []
        except Exception as exc:
            logger.error(f"Bhavcopy {trade_date}: parse error: {exc}")
            return []

    def download_range(
        self,
        start_date: date,
        end_date: date,
        skip_weekends: bool = True,
    ) -> List[BhavcopyStagingResult]:
        """
        Download Bhavcopy archives for a date range.

        Args:
            start_date: First date to download (inclusive).
            end_date: Last date to download (inclusive).
            skip_weekends: If True, skip Saturday and Sunday.

        Returns:
            List of BhavcopyStagingResult, one per attempted date.
        """
        results = []
        current = start_date
        while current <= end_date:
            if skip_weekends and current.weekday() >= 5:
                current += timedelta(days=1)
                continue
            result = self.download_day(current)
            results.append(result)
            current += timedelta(days=1)
        return results

    def backfill(self, days: int) -> List[BhavcopyStagingResult]:
        """
        Download the last `days` trading days of Bhavcopy data.

        Args:
            days: Number of past trading days to backfill. Capped by settings.

        Returns:
            List of BhavcopyStagingResult.
        """
        config = get_config()
        bhavcopy_cfg = config.yaml.get("bhavcopy", {})
        max_days = int(bhavcopy_cfg.get("max_backfill_days", 365))
        days = min(days, max_days)

        today = now_ist().date()
        # Go back `days` calendar days (weekends will be skipped in download_range)
        start = today - timedelta(days=days * 2)  # Generous buffer for weekends
        return self.download_range(start, today - timedelta(days=1))
