"""
Phase 16 — FII/DII Participant Flow Data Fetcher.

DATA INFRASTRUCTURE ONLY.
This module fetches and stores FII/DII daily flow data.
It does NOT:
- Make alpha claims or research conclusions from this data
- Add new hypotheses
- Unlock Phase 15 research
- Run any strategy searches

Source: NSE India participant-wise trading data (public, free).
URL: https://www.nseindia.com/api/fiidiiTradeReact

Freshness: EOD data — typically available after 17:00 IST on trading days.
Provenance: Every record carries retrieval_timestamp, source, and raw_payload.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import requests

from src.utils.config import get_config
from src.utils.logging_config import get_logger
from src.utils.time_utils import now_ist

logger = get_logger(__name__)

# NSE participant-wise trading data endpoint (public, no auth required)
_FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"

# NSE web app user-agent (required to avoid bot detection)
_NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}


# =============================================================================
# Data model
# =============================================================================

@dataclass
class FIIDIIRecord:
    """
    Parsed FII/DII participant flow record for one trading date.

    All monetary values are in INR crores (as published by NSE).
    net = buy_value - sell_value.
    Missing segments remain None.
    """
    trade_date: date
    retrieval_timestamp: datetime

    # FII
    fii_net_buy_sell: Optional[float] = None
    fii_index_futures_net: Optional[float] = None
    fii_index_options_net: Optional[float] = None
    fii_stock_futures_net: Optional[float] = None
    fii_stock_options_net: Optional[float] = None
    fii_equity_net: Optional[float] = None

    # DII
    dii_net_buy_sell: Optional[float] = None
    dii_equity_net: Optional[float] = None

    source: str = "NSE_PARTICIPANT_DATA"
    freshness_level: str = "END_OF_DAY"
    data_quality: str = "GOOD"
    raw_payload: Optional[Dict[str, Any]] = field(default=None)


# =============================================================================
# Parser
# =============================================================================

def _safe_float(val: Any) -> Optional[float]:
    if val is None or val in ("", "-", "NA", "N/A"):
        return None
    try:
        # NSE uses commas for thousands: "12,345.67"
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return None


def _parse_date(s: str) -> Optional[date]:
    """Parse NSE date strings like '20-Sep-2024' or '2024-09-20'."""
    if not s:
        return None
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d-%B-%Y"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_fii_dii_response(data: Any, retrieval_ts: datetime) -> List[FIIDIIRecord]:
    """
    Parse NSE FII/DII API response into FIIDIIRecord list.

    NSE returns a list of records. Each record has 'category', 'buySell', 'netBuySell' etc.
    The exact schema may vary; we parse defensively.

    Args:
        data: Parsed JSON from NSE API.
        retrieval_ts: When the request was made.

    Returns:
        List of FIIDIIRecord (one per trading date × category combination merged into daily record).
    """
    if not data:
        return []

    # NSE API typically returns a list of daily records
    # Each item may contain 'date', 'fiiNet', 'diiNet' etc. or a more granular format.
    # We handle both formats defensively.

    records_by_date: Dict[str, FIIDIIRecord] = {}

    def _get_or_create(d: date) -> FIIDIIRecord:
        key = d.isoformat()
        if key not in records_by_date:
            records_by_date[key] = FIIDIIRecord(
                trade_date=d,
                retrieval_timestamp=retrieval_ts,
            )
        return records_by_date[key]

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue

            # Try to extract date
            raw_date = item.get("date") or item.get("Date") or item.get("tradeDate")
            if not raw_date:
                continue
            trade_date = _parse_date(str(raw_date))
            if trade_date is None:
                continue

            rec = _get_or_create(trade_date)
            rec.raw_payload = item  # Store raw for audit

            # Try standard field names
            category = str(item.get("category", item.get("Category", ""))).upper()

            net_val = _safe_float(
                item.get("netBuySell") or item.get("net") or item.get("netBuyOrSell")
                or item.get("NET") or item.get("NetBuySell")
            )

            if "FII" in category or "FPI" in category:
                if rec.fii_net_buy_sell is None:
                    rec.fii_net_buy_sell = net_val
                else:
                    rec.fii_net_buy_sell = (rec.fii_net_buy_sell or 0.0) + (net_val or 0.0)

                # Segment-level breakdown (if available)
                if "INDEX FUT" in category or "IDX FUT" in category:
                    rec.fii_index_futures_net = net_val
                elif "INDEX OPT" in category or "IDX OPT" in category:
                    rec.fii_index_options_net = net_val
                elif "STOCK FUT" in category or "STK FUT" in category:
                    rec.fii_stock_futures_net = net_val
                elif "STOCK OPT" in category or "STK OPT" in category:
                    rec.fii_stock_options_net = net_val
                elif "EQUITY" in category or "CASH" in category:
                    rec.fii_equity_net = net_val

            elif "DII" in category or "DOMESTIC" in category:
                if rec.dii_net_buy_sell is None:
                    rec.dii_net_buy_sell = net_val
                else:
                    rec.dii_net_buy_sell = (rec.dii_net_buy_sell or 0.0) + (net_val or 0.0)
                if "EQUITY" in category or "CASH" in category:
                    rec.dii_equity_net = net_val

    elif isinstance(data, dict):
        # Some NSE endpoints return a single-date record as dict
        trade_date = _parse_date(str(data.get("date") or data.get("Date") or ""))
        if trade_date:
            rec = _get_or_create(trade_date)
            rec.fii_net_buy_sell = _safe_float(data.get("fiiNet") or data.get("FIINet"))
            rec.dii_net_buy_sell = _safe_float(data.get("diiNet") or data.get("DIINet"))
            rec.raw_payload = data

    return list(records_by_date.values())


# =============================================================================
# Fetcher
# =============================================================================

class FIIDIIFetcher:
    """
    Fetches FII/DII participant flow data from NSE.

    Returns parsed FIIDIIRecord list.
    Stores raw_payload for audit trail.
    Fails safely: if NSE is unreachable, logs warning and returns empty list.
    """

    def __init__(self, timeout: int = 15) -> None:
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(_NSE_HEADERS)

    def fetch_latest(self) -> List[FIIDIIRecord]:
        """
        Fetch the most recent FII/DII data available from NSE.

        Returns:
            List of FIIDIIRecord (may be empty if NSE is unreachable).
        """
        retrieval_ts = now_ist()
        try:
            # NSE requires a prior request to / to get cookies
            self._session.get("https://www.nseindia.com/", timeout=self._timeout)
            resp = self._session.get(_FII_DII_URL, timeout=self._timeout)
            if resp.status_code != 200:
                logger.warning(f"FII/DII fetch: NSE returned HTTP {resp.status_code}")
                return []
            data = resp.json()
            records = parse_fii_dii_response(data, retrieval_ts)
            logger.info(f"FII/DII fetch: {len(records)} date records retrieved")
            return records
        except requests.exceptions.ConnectionError as exc:
            logger.warning(f"FII/DII fetch: connection error: {exc}")
            return []
        except requests.exceptions.Timeout:
            logger.warning("FII/DII fetch: request timed out")
            return []
        except ValueError as exc:
            logger.warning(f"FII/DII fetch: JSON parse error: {exc}")
            return []
        except Exception as exc:
            logger.warning(f"FII/DII fetch: unexpected error: {exc}")
            return []

    def fetch_for_date(self, trade_date: date) -> List[FIIDIIRecord]:
        """
        Attempt to fetch FII/DII data for a specific date.
        NSE's API may not support arbitrary historical dates via this endpoint;
        in that case the response is filtered by date if available.

        Returns empty list if the date's data is not in the response.
        """
        all_records = self.fetch_latest()
        return [r for r in all_records if r.trade_date == trade_date]
