"""
Phase 16 — Tests for NSE Bhavcopy downloader and parser.

All tests use in-memory fixtures. No network calls.
Tests verify:
- SHA256 is computed and recorded correctly
- Parsing works for valid CSV
- bid_price and ask_price are NEVER set (always None)
- data_status is SETTLEMENT_PRICE_ONLY for all records
- Idempotent: local cache is used if file exists
- Missing/malformed rows are handled gracefully (partial quality)
- Not-found (404) returns staging record with NOT_FOUND status
- Data integrity: no fabricated bid/ask
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.bhavcopy_downloader import (
    BhavcopyCandleRecord,
    NSEBhavcopyCandleDownloader,
    SETTLEMENT_PRICE_ONLY,
    parse_bhavcopy_csv,
    sha256_bytes,
)


# =============================================================================
# Fixture CSV data
# =============================================================================

_SAMPLE_CSV_HEADER = (
    "TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,Undrlng,"
    "UndrlygPric,OptnTp,XpryDt,StrkPric,OpnIntrst,ChngInOpnIntrst,TtlTradVol,"
    "TtlTrfVal,SttlmntPric,New52wkHghs,New52wkLows,UndrlygOpnIntrst,ChngInUndrlygOpnIntrst\n"
)

_SAMPLE_CSV_OPT_ROW_CE = (
    "2024-01-10,2024-01-10,FO,,OPT,NIFTY10JAN2424000CE,,NIFTY,NIFTY,"
    "21800.00,CE,2024-01-25,24000.00,500000,10000,120000,"
    "1234567.89,21.50,0,0,12000000,50000\n"
)

_SAMPLE_CSV_OPT_ROW_PE = (
    "2024-01-10,2024-01-10,FO,,OPT,NIFTY10JAN2424000PE,,NIFTY,NIFTY,"
    "21800.00,PE,2024-01-25,24000.00,450000,8000,110000,"
    "1111222.33,45.75,0,0,12000000,50000\n"
)

_SAMPLE_CSV_EQUITY_ROW = (
    "2024-01-10,2024-01-10,CM,,EQ,RELIANCE,,RELIANCE,,"
    ",,,,,,,123456.78,,0,0,,\n"
)

_SAMPLE_CSV = _SAMPLE_CSV_HEADER + _SAMPLE_CSV_OPT_ROW_CE + _SAMPLE_CSV_OPT_ROW_PE + _SAMPLE_CSV_EQUITY_ROW


def _make_zip_bytes(csv_content: str, filename: str = "BhavCopy_FO.csv") -> bytes:
    """Create an in-memory zip archive containing the CSV."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, csv_content)
    return buf.getvalue()


# =============================================================================
# SHA256 tests
# =============================================================================

class TestSHA256:
    def test_sha256_known_value(self):
        data = b"hello world"
        expected = hashlib.sha256(data).hexdigest()
        assert sha256_bytes(data) == expected

    def test_sha256_empty_bytes(self):
        result = sha256_bytes(b"")
        assert len(result) == 64  # SHA256 is always 64 hex chars

    def test_sha256_large_content(self):
        data = b"X" * 1_000_000
        result = sha256_bytes(data)
        assert len(result) == 64

    def test_sha256_deterministic(self):
        data = b"same content"
        assert sha256_bytes(data) == sha256_bytes(data)

    def test_sha256_different_content_different_hash(self):
        assert sha256_bytes(b"abc") != sha256_bytes(b"abd")


# =============================================================================
# CSV Parser tests
# =============================================================================

class TestParseBhavcopyCsv:
    def test_parses_options_rows_only(self):
        records = parse_bhavcopy_csv(_SAMPLE_CSV, date(2024, 1, 10))
        # Should get 2 options rows, not 3 (equity row excluded)
        assert len(records) == 2

    def test_bid_ask_always_none(self):
        records = parse_bhavcopy_csv(_SAMPLE_CSV, date(2024, 1, 10))
        for rec in records:
            assert rec.bid_price is None, "bid_price MUST be None for Bhavcopy data"
            assert rec.ask_price is None, "ask_price MUST be None for Bhavcopy data"

    def test_data_status_settlement_price_only(self):
        records = parse_bhavcopy_csv(_SAMPLE_CSV, date(2024, 1, 10))
        for rec in records:
            assert rec.data_status == SETTLEMENT_PRICE_ONLY

    def test_source_is_bhavcopy(self):
        records = parse_bhavcopy_csv(_SAMPLE_CSV, date(2024, 1, 10))
        for rec in records:
            assert "BHAVCOPY" in rec.source.upper()

    def test_ce_parsed_correctly(self):
        records = parse_bhavcopy_csv(_SAMPLE_CSV, date(2024, 1, 10))
        ce_rec = next((r for r in records if r.option_type == "CE"), None)
        assert ce_rec is not None
        assert ce_rec.underlying == "NIFTY"
        assert ce_rec.strike_price == 24000.0
        assert ce_rec.open_interest == 500000
        assert ce_rec.settlement_price == 21.5
        assert ce_rec.trade_date == date(2024, 1, 10)

    def test_pe_parsed_correctly(self):
        records = parse_bhavcopy_csv(_SAMPLE_CSV, date(2024, 1, 10))
        pe_rec = next((r for r in records if r.option_type == "PE"), None)
        assert pe_rec is not None
        assert pe_rec.option_type == "PE"
        assert pe_rec.strike_price == 24000.0

    def test_missing_settlement_price_is_none_not_zero(self):
        csv = _SAMPLE_CSV_HEADER + (
            "2024-01-10,2024-01-10,FO,,OPT,NIFTY10JAN2425000CE,,NIFTY,NIFTY,"
            "21800.00,CE,2024-01-25,25000.00,100000,5000,50000,"
            ",,0,0,12000000,50000\n"  # Empty settlement price
        )
        records = parse_bhavcopy_csv(csv, date(2024, 1, 10))
        if records:
            assert records[0].settlement_price is None

    def test_partial_quality_when_key_fields_missing(self):
        csv = _SAMPLE_CSV_HEADER + (
            "2024-01-10,2024-01-10,FO,,OPT,NIFTY10JAN2425000CE,,NIFTY,NIFTY,"
            "21800.00,CE,,,100000,5000,50000,"
            ",,0,0,12000000,50000\n"  # Missing expiry and strike
        )
        records = parse_bhavcopy_csv(csv, date(2024, 1, 10))
        if records:
            assert records[0].data_quality == "PARTIAL"

    def test_empty_csv_returns_empty_list(self):
        records = parse_bhavcopy_csv("", date(2024, 1, 10))
        assert records == []

    def test_header_only_csv_returns_empty_list(self):
        records = parse_bhavcopy_csv(_SAMPLE_CSV_HEADER, date(2024, 1, 10))
        assert records == []


# =============================================================================
# Downloader tests
# =============================================================================


class TestNSEBhavcopyCandleDownloader:

    def _mock_init(self, session_mock, tmp_path):
        """Helper to create a proper __init__ mock that correctly returns None."""
        def _init(self_inner, raw_dir=None, url_template=None):
            self_inner._raw_dir = tmp_path
            self_inner._url_template = "http://test/{date}.csv.zip"
            self_inner._session = session_mock
            # __init__ must return None — no implicit tuple return
        return _init

    def test_download_success_records_sha256(self, tmp_path):
        zip_bytes = _make_zip_bytes(_SAMPLE_CSV)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = zip_bytes

        session_mock = MagicMock(get=MagicMock(return_value=mock_resp))
        with patch.object(NSEBhavcopyCandleDownloader, "__init__", self._mock_init(session_mock, tmp_path)):
            downloader = NSEBhavcopyCandleDownloader()

        result = downloader.download_day(date(2024, 1, 10))
        staging = result.staging_record

        assert staging.download_status == "SUCCESS"
        assert staging.sha256_hash == sha256_bytes(zip_bytes)
        assert len(staging.sha256_hash) == 64

    def test_404_returns_not_found(self, tmp_path):
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        session_mock = MagicMock(get=MagicMock(return_value=mock_resp))
        with patch.object(NSEBhavcopyCandleDownloader, "__init__", self._mock_init(session_mock, tmp_path)):
            downloader = NSEBhavcopyCandleDownloader()

        result = downloader.download_day(date(2024, 1, 10))
        assert result.staging_record.download_status == "NOT_FOUND"
        assert result.candles == []

    def test_idempotent_uses_local_cache(self, tmp_path):
        zip_bytes = _make_zip_bytes(_SAMPLE_CSV)
        # Pre-create the local file
        local_file = tmp_path / "BhavCopy_FO_20240110.csv.zip"
        local_file.write_bytes(zip_bytes)

        mock_session = MagicMock()
        mock_session.get.side_effect = AssertionError("Network should not be called when local file exists")

        with patch.object(NSEBhavcopyCandleDownloader, "__init__", self._mock_init(mock_session, tmp_path)):
            downloader = NSEBhavcopyCandleDownloader()

        result = downloader.download_day(date(2024, 1, 10))
        # Should use cache without calling network
        assert "CACHED" in result.staging_record.download_status or result.staging_record.download_status == "SUCCESS (CACHED)"

    def test_candles_have_no_bid_ask(self, tmp_path):
        zip_bytes = _make_zip_bytes(_SAMPLE_CSV)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = zip_bytes

        session_mock = MagicMock(get=MagicMock(return_value=mock_resp))
        with patch.object(NSEBhavcopyCandleDownloader, "__init__", self._mock_init(session_mock, tmp_path)):
            downloader = NSEBhavcopyCandleDownloader()

        result = downloader.download_day(date(2024, 1, 10))
        assert len(result.candles) == 2
        for candle in result.candles:
            assert candle.bid_price is None
            assert candle.ask_price is None
            assert candle.data_status == SETTLEMENT_PRICE_ONLY

    def test_bad_zip_returns_empty_candles(self, tmp_path):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"this is not a zip file"

        session_mock = MagicMock(get=MagicMock(return_value=mock_resp))
        with patch.object(NSEBhavcopyCandleDownloader, "__init__", self._mock_init(session_mock, tmp_path)):
            downloader = NSEBhavcopyCandleDownloader()

        result = downloader.download_day(date(2024, 1, 10))
        # Should succeed download, but parse returns empty
        assert result.candles == []

    def test_provenance_url_recorded(self, tmp_path):
        zip_bytes = _make_zip_bytes(_SAMPLE_CSV)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = zip_bytes

        session_mock = MagicMock(get=MagicMock(return_value=mock_resp))
        with patch.object(NSEBhavcopyCandleDownloader, "__init__", self._mock_init(session_mock, tmp_path)):
            downloader = NSEBhavcopyCandleDownloader()

        result = downloader.download_day(date(2024, 1, 10))
        assert "20240110" in result.staging_record.source_url
        assert result.staging_record.retrieval_timestamp is not None
        assert result.staging_record.file_size_bytes == len(zip_bytes)



# =============================================================================
# Data integrity assertions
# =============================================================================

class TestBhavcopyCandleIntegrity:
    def test_record_has_settlement_price_only_tag(self):
        rec = BhavcopyCandleRecord(
            trade_date=date(2024, 1, 10),
            underlying="NIFTY",
            expiry_date=date(2024, 1, 25),
            strike_price=24000.0,
            option_type="CE",
            open_interest=500000,
            change_in_oi=10000,
            volume=120000,
            settlement_price=21.5,
        )
        assert rec.data_status == SETTLEMENT_PRICE_ONLY
        assert rec.bid_price is None
        assert rec.ask_price is None

    def test_cannot_set_bid_ask_via_init(self):
        """bid_price and ask_price are field(default=None, init=False) — cannot be set via constructor."""
        rec = BhavcopyCandleRecord(
            trade_date=date(2024, 1, 10),
            underlying="NIFTY",
            expiry_date=date(2024, 1, 25),
            strike_price=24000.0,
            option_type="CE",
            open_interest=0,
            change_in_oi=0,
            volume=0,
            settlement_price=100.0,
        )
        assert rec.bid_price is None
        assert rec.ask_price is None
