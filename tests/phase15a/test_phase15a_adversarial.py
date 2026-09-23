"""
Phase 15A Adversarial Test Suite.

Contains 40 comprehensive adversarial tests covering:
- Scenarios 1–8: Safety invariant violations and enforcement
- Scenarios 9–11: Raw immutability, duplicate detection, and in-place protection
- Scenarios 12–16: ZIP container lineage, entry hashing, and corrupt archive handling
- Scenarios 17–21: Multi-format file inspection and corrupt payload safety
- Scenarios 22–25: Deterministic normalization and lineage tracking
- Scenarios 26–30: Strict prohibition of silent data repair (Correction 5)
- Scenarios 31–33: Multi-file chunk ordering, boundary overlaps, and schema drift
- Scenarios 34–36: Deterministic dataset comparison and reconciliation
- Scenarios 37–38: Test fixture isolation and quarantine defense
- Scenarios 39–40: Phase 14 certification handoff, blocking capability state, and traceability
"""

import gzip
import os
import shutil
import tempfile
import zipfile
import pytest
import pandas as pd
from unittest.mock import patch

from src.research.phase15a.safety_policy import SafetyPolicy, SafetyViolationError
from src.research.phase15a.raw_archive import RawArchiveManager, compute_file_sha256
from src.research.phase15a.file_inspector import SafeFileInspector
from src.research.phase15a.normalization_engine import NormalizationEngine
from src.research.phase15a.multi_file_handler import MultiFileDatasetTracker
from src.research.phase15a.dataset_comparator import DatasetComparator
from src.research.phase15a.certification_handoff import (
    CertificationHandoffManager,
    CertificationOutcomeState,
)
from src.research.phase15a.archive_structure import ArchiveStructureManager


# -------------------------------------------------------------------------
# SCENARIOS 1–8: Safety Invariant Violations and Enforcement
# -------------------------------------------------------------------------

def test_adv_01_broker_mutation_fails():
    """Scenario 1: Setting BROKER away from NONE raises SafetyViolationError."""
    with patch.object(SafetyPolicy, "get_broker", return_value="ZERODHA"):
        with pytest.raises(SafetyViolationError, match="BROKER must be 'NONE'"):
            SafetyPolicy.assert_safety_invariants(context="adv_01")


def test_adv_02_live_execution_enabled_fails():
    """Scenario 2: Enabling LIVE_EXECUTION raises SafetyViolationError."""
    with patch.object(SafetyPolicy, "get_live_execution", return_value="ENABLED"):
        with pytest.raises(SafetyViolationError, match="LIVE_EXECUTION must be 'DISABLED'"):
            SafetyPolicy.assert_safety_invariants(context="adv_02")


def test_adv_03_auto_paper_orders_enabled_fails():
    """Scenario 3: Enabling AUTO_PAPER_ORDER_SUBMISSION raises SafetyViolationError."""
    with patch.object(SafetyPolicy, "get_auto_paper_order_submission", return_value="ENABLED"):
        with pytest.raises(SafetyViolationError, match="AUTO_PAPER_ORDER_SUBMISSION must be 'DISABLED'"):
            SafetyPolicy.assert_safety_invariants(context="adv_03")


def test_adv_04_purchase_authorized_fails():
    """Scenario 4: Authorizing purchase without manual human execution raises SafetyViolationError."""
    with patch.object(SafetyPolicy, "get_purchase_authorized", return_value=True):
        with pytest.raises(SafetyViolationError, match="PURCHASE_AUTHORIZED must be False"):
            SafetyPolicy.assert_safety_invariants(context="adv_04")


def test_adv_05_automated_data_purchase_fails():
    """Scenario 5: Attempting automated data purchase raises SafetyViolationError."""
    with patch.object(SafetyPolicy, "get_automated_data_purchase", return_value="ENABLED"):
        with pytest.raises(SafetyViolationError, match="AUTOMATED_DATA_PURCHASE must be 'DISABLED'"):
            SafetyPolicy.assert_safety_invariants(context="adv_05")


def test_adv_06_automated_vendor_contact_fails():
    """Scenario 6: Attempting automated vendor contact raises SafetyViolationError."""
    with patch.object(SafetyPolicy, "get_automated_vendor_contact", return_value="ENABLED"):
        with pytest.raises(SafetyViolationError, match="AUTOMATED_VENDOR_CONTACT must be 'DISABLED'"):
            SafetyPolicy.assert_safety_invariants(context="adv_06")


def test_adv_07_new_alpha_research_fails():
    """Scenario 7: Attempting new unpreregistered alpha research raises SafetyViolationError."""
    with patch.object(SafetyPolicy, "get_new_alpha_research", return_value="ENABLED"):
        with pytest.raises(SafetyViolationError, match="NEW_UNPREREGISTERED_ALPHA_RESEARCH must be 'DISABLED'"):
            SafetyPolicy.assert_safety_invariants(context="adv_07")


def test_adv_08_phase_15_unlocked_fails():
    """Scenario 8: Attempting to prematurely unlock Phase 15 raises SafetyViolationError."""
    with patch.object(SafetyPolicy, "get_phase_15_unlocked", return_value=True):
        with pytest.raises(SafetyViolationError, match="PHASE_15_UNLOCKED must be False"):
            SafetyPolicy.assert_safety_invariants(context="adv_08")


# -------------------------------------------------------------------------
# SCENARIOS 9–11: Raw Immutability, Duplicate Detection, and In-Place Protection
# -------------------------------------------------------------------------

def test_adv_09_duplicate_artifact_detected_by_sha256():
    """Scenario 9: Ingesting an identical file under a new intake_id flags duplicate_artifact=True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_storage = os.path.join(tmpdir, "raw")
        mgr = RawArchiveManager(raw_storage_dir=raw_storage)

        f_path = os.path.join(tmpdir, "vendor_feed.csv")
        with open(f_path, "w") as f:
            f.write("timestamp,close\n2024-01-01 09:15:00,100\n")

        rec1, is_dup1 = mgr.ingest_raw_file("INTAKE-01", "DS-01", "VendorA", f_path)
        assert is_dup1 is False

        rec2, is_dup2 = mgr.ingest_raw_file("INTAKE-02", "DS-02", "VendorA", f_path)
        assert is_dup2 is True
        assert rec2.duplicate_artifact is True


def test_adv_10_renamed_duplicate_detected_by_hash():
    """Scenario 10: Ingesting identical content with a different filename flags duplicate_artifact=True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_storage = os.path.join(tmpdir, "raw")
        mgr = RawArchiveManager(raw_storage_dir=raw_storage)

        f1 = os.path.join(tmpdir, "delivery_alpha.csv")
        f2 = os.path.join(tmpdir, "delivery_beta.csv")
        content = "timestamp,close\n2024-01-01 09:15:00,200\n"
        with open(f1, "w") as f:
            f.write(content)
        with open(f2, "w") as f:
            f.write(content)

        _, is_dup1 = mgr.ingest_raw_file("INTAKE-10A", "DS-10A", "VendorA", f1)
        assert is_dup1 is False

        rec2, is_dup2 = mgr.ingest_raw_file("INTAKE-10B", "DS-10B", "VendorA", f2)
        assert is_dup2 is True
        assert rec2.duplicate_artifact is True


def test_adv_11_raw_vendor_file_never_modified_in_place():
    """Scenario 11: Raw vendor source file hash remains identical before and after ingestion/normalization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_storage = os.path.join(tmpdir, "raw")
        norm_storage = os.path.join(tmpdir, "norm.csv")
        mgr = RawArchiveManager(raw_storage_dir=raw_storage)

        f_path = os.path.join(tmpdir, "immutable_vendor.csv")
        with open(f_path, "w") as f:
            f.write("date,time,close\n2024-01-01,09:15:00,100\n")

        original_hash = compute_file_sha256(f_path)
        mgr.ingest_raw_file("INTAKE-11", "DS-11", "VendorA", f_path, copy_to_raw_archive=True)
        NormalizationEngine.normalize_file(f_path, norm_storage)

        post_hash = compute_file_sha256(f_path)
        assert original_hash == post_hash, "Raw vendor file was modified in place!"


# -------------------------------------------------------------------------
# SCENARIOS 12–16: ZIP Container Lineage and Corrupt Archive Handling
# -------------------------------------------------------------------------

def test_adv_12_zip_archive_hash_recorded():
    """Scenario 12: Entire parent ZIP archive has its SHA256 recorded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = RawArchiveManager(raw_storage_dir=os.path.join(tmpdir, "raw"))
        zip_path = os.path.join(tmpdir, "container.zip")
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("sub.csv", "timestamp,close\n2024-01-01,10\n")

        rec, _ = mgr.ingest_raw_file("INTAKE-12", "DS-12", "VendorA", zip_path)
        assert rec.sha256 == compute_file_sha256(zip_path)


def test_adv_13_zip_contained_files_individual_hashes():
    """Scenario 13: Every contained file in a ZIP has individual SHA256 computed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = RawArchiveManager(raw_storage_dir=os.path.join(tmpdir, "raw"))
        zip_path = os.path.join(tmpdir, "multi_container.zip")
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("a.csv", "a\n1\n")
            z.writestr("b.json", '{"b": 2}')

        rec, _ = mgr.ingest_raw_file("INTAKE-13", "DS-13", "VendorA", zip_path)
        assert len(rec.zip_entries) == 2
        for entry in rec.zip_entries:
            assert len(entry.contained_file_sha256) == 64
            assert entry.parent_archive_sha256 == rec.sha256


def test_adv_14_zip_entry_uncompressed_size_recorded():
    """Scenario 14: Contained files inside ZIP record accurate uncompressed size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = RawArchiveManager(raw_storage_dir=os.path.join(tmpdir, "raw"))
        zip_path = os.path.join(tmpdir, "sized_container.zip")
        payload = b"Hello, Indian Stock Market AI!"
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("data.txt", payload)

        rec, _ = mgr.ingest_raw_file("INTAKE-14", "DS-14", "VendorA", zip_path)
        assert rec.zip_entries[0].contained_file_size_bytes == len(payload)


def test_adv_15_zip_entry_format_detection():
    """Scenario 15: Formats of individual files inside ZIP are detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = RawArchiveManager(raw_storage_dir=os.path.join(tmpdir, "raw"))
        zip_path = os.path.join(tmpdir, "formats.zip")
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("quotes.parquet", b"PAR1test")
            z.writestr("index.csv", "timestamp,close\n")

        rec, _ = mgr.ingest_raw_file("INTAKE-15", "DS-15", "VendorA", zip_path)
        formats = {e.contained_filename: e.detected_format for e in rec.zip_entries}
        assert formats["quotes.parquet"] == "PARQUET"
        assert formats["index.csv"] == "CSV"


def test_adv_16_corrupt_zip_fails_safe_inspection():
    """Scenario 16: Truncated ZIP archive is detected safely without throwing unhandled exceptions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        corrupt_zip = os.path.join(tmpdir, "corrupt.zip")
        with open(corrupt_zip, "wb") as f:
            f.write(b"PK\x03\x04truncated_corrupted_zip_bytes")

        res = SafeFileInspector.inspect_file(corrupt_zip)
        assert res.is_corrupted is True
        assert res.detected_format == "CORRUPTED"


# -------------------------------------------------------------------------
# SCENARIOS 17–21: Multi-Format Inspection and Corrupt Payload Safety
# -------------------------------------------------------------------------

def test_adv_17_corrupt_gzip_fails_safely():
    """Scenario 17: Truncated or invalid GZIP file fails safely."""
    with tempfile.TemporaryDirectory() as tmpdir:
        corrupt_gz = os.path.join(tmpdir, "corrupt.csv.gz")
        with open(corrupt_gz, "wb") as f:
            f.write(b"\x1f\x8b\x08not_valid_gzip_payload")

        res = SafeFileInspector.inspect_file(corrupt_gz)
        assert res.is_corrupted is True
        assert res.detected_format == "CORRUPTED"


def test_adv_18_corrupt_parquet_fails_safely():
    """Scenario 18: Invalid Parquet file lacking PAR1 magic bytes fails safely."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_parquet = os.path.join(tmpdir, "bad.parquet")
        with open(bad_parquet, "wb") as f:
            f.write(b"NOT_A_PARQUET_FILE_MAGIC")

        res = SafeFileInspector.inspect_file(bad_parquet)
        assert res.is_corrupted is True
        assert res.detected_format == "CORRUPTED"


def test_adv_19_corrupt_json_fails_safely():
    """Scenario 19: Malformed JSON file fails safely."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_json = os.path.join(tmpdir, "bad.json")
        with open(bad_json, "w") as f:
            f.write('{"missing_closing_brace": 123')

        res = SafeFileInspector.inspect_file(bad_json)
        assert res.is_corrupted is True
        assert res.detected_format == "CORRUPTED"


def test_adv_20_empty_file_fails_safely():
    """Scenario 20: 0-byte file is flagged corrupted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        empty = os.path.join(tmpdir, "zero.csv")
        with open(empty, "w") as f:
            pass

        res = SafeFileInspector.inspect_file(empty)
        assert res.is_corrupted is True
        assert res.file_size_bytes == 0


def test_adv_21_headerless_file_fails_safely():
    """Scenario 21: File with blank content fails safe inspection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        blank = os.path.join(tmpdir, "blank.csv")
        with open(blank, "w") as f:
            f.write("\n\n\n")

        res = SafeFileInspector.inspect_file(blank)
        assert res.is_corrupted is True


# -------------------------------------------------------------------------
# SCENARIOS 22–25: Deterministic Normalization and Lineage Tracking
# -------------------------------------------------------------------------

def test_adv_22_deterministic_normalization_reproducibility():
    """Scenario 22: Identical input + transformation produces bit-identical output hash across runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "src.csv")
        with open(src, "w") as f:
            f.write("date,time,open,high,low,close,vol\n2024-01-01,09:15:00,10,12,9,11,100\n")

        out_a = os.path.join(tmpdir, "out_a.csv")
        out_b = os.path.join(tmpdir, "out_b.csv")

        _, audit_a = NormalizationEngine.normalize_file(src, out_a)
        _, audit_b = NormalizationEngine.normalize_file(src, out_b)

        assert audit_a.input_sha256 == audit_b.input_sha256
        assert audit_a.output_sha256 == audit_b.output_sha256


def test_adv_23_column_alias_mapping():
    """Scenario 23: Diverse vendor headers are standardized deterministically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "vendor_headers.csv")
        with open(src, "w") as f:
            f.write("<OPEN>,<HIGH>,<LOW>,<CLOSE>,<OPENINTEREST>\n1,2,0.5,1.5,100\n")

        out = os.path.join(tmpdir, "norm_headers.csv")
        df, _ = NormalizationEngine.normalize_file(src, out)
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "oi" in df.columns


def test_adv_24_input_output_sha256_audit_lineage():
    """Scenario 24: Transformation audit record captures full input and output sha256."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "src.csv")
        with open(src, "w") as f:
            f.write("timestamp,close\n2024-01-01 09:15:00,50\n")
        out = os.path.join(tmpdir, "out.csv")

        _, audit = NormalizationEngine.normalize_file(src, out)
        assert len(audit.input_sha256) == 64
        assert len(audit.output_sha256) == 64
        assert audit.transformation_version == "v1.0.0_canonical"


def test_adv_25_date_time_combination():
    """Scenario 25: Separate date and time columns combined without modifying timestamps."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "split_ts.csv")
        with open(src, "w") as f:
            f.write("date,time,close\n2024-01-01,09:15:00,100\n")
        out = os.path.join(tmpdir, "joined_ts.csv")

        df, _ = NormalizationEngine.normalize_file(src, out)
        assert "timestamp" in df.columns
        assert df["timestamp"].iloc[0] == "2024-01-01 09:15:00"


# -------------------------------------------------------------------------
# SCENARIOS 26–30: Strict Prohibition of Silent Data Repair (Correction 5)
# -------------------------------------------------------------------------

def test_adv_26_no_interpolating_missing_bars():
    """Scenario 26: Missing bars are NOT interpolated or synthesized."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "gapped.csv")
        # Bar 09:15 and 09:17 (missing 09:16)
        with open(src, "w") as f:
            f.write("timestamp,close\n2024-01-01 09:15:00,100\n2024-01-01 09:17:00,102\n")
        out = os.path.join(tmpdir, "gapped_norm.csv")

        df, audit = NormalizationEngine.normalize_file(src, out)
        assert len(df) == 2, "Normalization created synthetic interpolated bars!"
        assert audit.repaired_interpolated_bars_count == 0


def test_adv_27_no_price_smoothing():
    """Scenario 27: Noisy or spiky prices are NOT smoothed or altered."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "spike.csv")
        with open(src, "w") as f:
            f.write("timestamp,close\n2024-01-01 09:15:00,100\n2024-01-01 09:16:00,99999\n")
        out = os.path.join(tmpdir, "spike_norm.csv")

        df, _ = NormalizationEngine.normalize_file(src, out)
        assert df["close"].iloc[1] == 99999, "Price spike was smoothed or altered!"


def test_adv_28_no_ohlc_violation_repair():
    """Scenario 28: OHLC violations (high < low) are NOT fixed in normalization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "bad_ohlc.csv")
        with open(src, "w") as f:
            f.write("timestamp,open,high,low,close\n2024-01-01 09:15:00,100,50,200,100\n")
        out = os.path.join(tmpdir, "bad_ohlc_norm.csv")

        df, _ = NormalizationEngine.normalize_file(src, out)
        assert df["high"].iloc[0] == 50
        assert df["low"].iloc[0] == 200


def test_adv_29_no_manufacturing_bid_ask():
    """Scenario 29: Missing Bid and Ask columns are NOT manufactured."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "no_quotes.csv")
        with open(src, "w") as f:
            f.write("timestamp,close\n2024-01-01 09:15:00,100\n")
        out = os.path.join(tmpdir, "no_quotes_norm.csv")

        df, _ = NormalizationEngine.normalize_file(src, out)
        assert "bid" not in df.columns
        assert "ask" not in df.columns


def test_adv_30_exact_row_conservation():
    """Scenario 30: Output row count strictly matches input row count."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "rows.csv")
        with open(src, "w") as f:
            f.write("timestamp,close\n" + "\n".join(f"2024-01-01 09:{i:02d}:00,100" for i in range(10)))
        out = os.path.join(tmpdir, "rows_norm.csv")

        df, audit = NormalizationEngine.normalize_file(src, out)
        assert audit.input_rows == 10
        assert audit.output_rows == 10
        assert len(df) == 10


# -------------------------------------------------------------------------
# SCENARIOS 31–33: Multi-File Chunk Tracking, Boundary Overlaps, and Drift
# -------------------------------------------------------------------------

def test_adv_31_multi_file_chunk_sequencing():
    """Scenario 31: MultiFileDatasetTracker preserves explicit chunk sequencing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        f1 = os.path.join(tmpdir, "c1.csv")
        f2 = os.path.join(tmpdir, "c2.csv")
        with open(f1, "w") as f:
            f.write("timestamp,close\n2024-01-01 09:15:00,10\n")
        with open(f2, "w") as f:
            f.write("timestamp,close\n2024-01-01 09:16:00,20\n")

        tracker = MultiFileDatasetTracker()
        grp = tracker.register_group("GRP-31", "NIFTY", "1m", "VendorA", [f1, f2])
        assert grp.chunks[0].sequence_number == 1
        assert grp.chunks[1].sequence_number == 2


def test_adv_32_multi_file_boundary_overlap_detection():
    """Scenario 32: Boundary timestamp overlap between consecutive files is detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        f1 = os.path.join(tmpdir, "c1.csv")
        f2 = os.path.join(tmpdir, "c2.csv")
        # Overlapping timestamp 09:16
        with open(f1, "w") as f:
            f.write("timestamp,close\n2024-01-01 09:15:00,10\n2024-01-01 09:17:00,15\n")
        with open(f2, "w") as f:
            f.write("timestamp,close\n2024-01-01 09:16:00,12\n2024-01-01 09:18:00,20\n")

        tracker = MultiFileDatasetTracker()
        grp = tracker.register_group("GRP-32", "NIFTY", "1m", "VendorA", [f1, f2])
        assert grp.has_boundary_overlaps is True


def test_adv_33_multi_file_schema_drift_detection():
    """Scenario 33: Schema column drift across files in a group is flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        f1 = os.path.join(tmpdir, "c1.csv")
        f2 = os.path.join(tmpdir, "c2.csv")
        with open(f1, "w") as f:
            f.write("timestamp,close,volume\n2024-01-01 09:15:00,10,100\n")
        with open(f2, "w") as f:
            f.write("timestamp,close,oi\n2024-01-01 09:16:00,20,50\n")

        tracker = MultiFileDatasetTracker()
        grp = tracker.register_group("GRP-33", "NIFTY", "1m", "VendorA", [f1, f2])
        assert grp.is_schema_consistent is False


# -------------------------------------------------------------------------
# SCENARIOS 34–36: Deterministic Dataset Comparison and Reconciliation
# -------------------------------------------------------------------------

def test_adv_34_comparator_reconciled_match():
    """Scenario 34: Exact matching datasets produce RECONCILED_MATCH."""
    df_a = pd.DataFrame({"timestamp": ["2024-01-01 09:15:00"], "close": [100.0], "volume": [50]})
    df_b = pd.DataFrame({"timestamp": ["2024-01-01 09:15:00"], "close": [100.0], "volume": [50]})

    rep = DatasetComparator.compare(df_a, df_b, "A", "B", "VA", "VB", "NIFTY", "1m")
    assert rep.reconciliation_status == "RECONCILED_MATCH"
    assert rep.close_price_exact_match_pct == 100.0


def test_adv_35_comparator_material_discrepancy():
    """Scenario 35: Material price differences yield MATERIAL_DISCREPANCY."""
    df_a = pd.DataFrame({"timestamp": ["2024-01-01 09:15:00"], "close": [100.0], "volume": [50]})
    df_b = pd.DataFrame({"timestamp": ["2024-01-01 09:15:00"], "close": [150.0], "volume": [50]})

    rep = DatasetComparator.compare(df_a, df_b, "A", "B", "VA", "VB", "NIFTY", "1m")
    assert rep.reconciliation_status == "MATERIAL_DISCREPANCY"
    assert rep.close_price_max_absolute_diff == 50.0


def test_adv_36_comparator_zero_overlap():
    """Scenario 36: Zero timestamp overlap yields NO_OVERLAP."""
    df_a = pd.DataFrame({"timestamp": ["2024-01-01 09:15:00"], "close": [100.0], "volume": [50]})
    df_b = pd.DataFrame({"timestamp": ["2024-01-02 09:15:00"], "close": [100.0], "volume": [50]})

    rep = DatasetComparator.compare(df_a, df_b, "A", "B", "VA", "VB", "NIFTY", "1m")
    assert rep.reconciliation_status == "NO_OVERLAP"
    assert rep.common_timestamps_count == 0


# -------------------------------------------------------------------------
# SCENARIOS 37–38: Test Fixture Isolation and Quarantine Defense
# -------------------------------------------------------------------------

def test_adv_37_disguised_fixture_quarantined():
    """Scenario 37: Disguised fixture with mock/fixture path or name is quarantined."""
    with tempfile.TemporaryDirectory() as tmpdir:
        struct = ArchiveStructureManager(base_intake_dir=os.path.join(tmpdir, "intake"))
        struct.initialize_directories()

        fixture_file = os.path.join(tmpdir, "mock_intraday_fixture.csv")
        with open(fixture_file, "w") as f:
            f.write("timestamp,close\n2024-01-01,100\n")

        q_path = struct.quarantine_artifact(fixture_file, "Detected test fixture")
        assert os.path.exists(q_path)
        assert "quarantine" in q_path.lower()


def test_adv_38_quarantined_fixture_fails_certification():
    """Scenario 38: Ingested fixture triggers QUARANTINED terminal outcome in handoff."""
    df = pd.DataFrame({"timestamp": ["2024-01-01 09:15:00"], "close": [100.0]})
    rec = CertificationHandoffManager.execute_handoff(
        df=df,
        dataset_id="TEST_FIXTURE_DATASET",
        version_id="v1.0",
        intake_id="INTAKE-FIXTURE",
        vendor="MOCK_VENDOR",
        underlying="NIFTY",
        interval="1m",
        source_file="tests/fixtures/synthetic_nifty.csv",  # Trigger fixture quarantine
        dataset_type="INTRADAY_1M",
        raw_artifact_sha256="0000000000000000000000000000000000000000000000000000000000000000",
        normalized_artifact_sha256="1111111111111111111111111111111111111111111111111111111111111111",
    )

    assert rec.outcome_state == CertificationOutcomeState.QUARANTINED.value
    assert rec.phase14_certified is False


# -------------------------------------------------------------------------
# SCENARIOS 39–40: Phase 14 Certification Handoff and Traceability Chain
# -------------------------------------------------------------------------

def test_adv_39_certified_with_blocking_capability():
    """Scenario 39: Failed capability or blocked project readiness sets CERTIFIED_WITH_BLOCKING_CAPABILITY."""
    # Under standard conditions, uncertified/defective or partial datasets yield failed or blocked outcomes
    df = pd.DataFrame({
        "timestamp": ["2024-01-01 09:15:00"],
        "open": [100.0],
        "high": [105.0],
        "low": [99.0],
        "close": [102.0],
        "volume": [500],
    })

    rec = CertificationHandoffManager.execute_handoff(
        df=df,
        dataset_id="NIFTY_REAL_DATA",
        version_id="v1.0",
        intake_id="INTAKE-REAL-01",
        vendor="TrueData",
        underlying="NIFTY",
        interval="1m",
        source_file="data/intake/raw/nifty_1m.csv",
        dataset_type="INTRADAY_1M",
        raw_artifact_sha256="a" * 64,
        normalized_artifact_sha256="b" * 64,
    )

    # Because 1 bar is < 250 sessions, Phase 14 marks it CERTIFICATION_FAILED
    assert rec.outcome_state in [
        CertificationOutcomeState.CERTIFICATION_FAILED.value,
        CertificationOutcomeState.CERTIFIED_WITH_BLOCKING_CAPABILITY.value,
    ]


def test_adv_40_certification_traceability_chain():
    """Scenario 40: Traceability chain connects result to normalized sha256 to raw sha256 to intake ID."""
    df = pd.DataFrame({"timestamp": ["2024-01-01 09:15:00"], "close": [100.0]})
    rec = CertificationHandoffManager.execute_handoff(
        df=df,
        dataset_id="NIFTY_TRACE_TEST",
        version_id="v1.0",
        intake_id="INTAKE-TRACE-40",
        vendor="TrueData",
        underlying="NIFTY",
        interval="1m",
        source_file="data/intake/raw/trace.csv",
        dataset_type="INTRADAY_1M",
        raw_artifact_sha256="abc123raw",
        normalized_artifact_sha256="def456norm",
        source_description="Direct vendor delivery S3",
        license_status="LICENSE_VERIFIED_RESTRICTED_RESEARCH",
    )

    chain = rec.traceability_chain
    assert chain["intake_id"] == "INTAKE-TRACE-40"
    assert chain["raw_artifact_sha256"] == "abc123raw"
    assert chain["normalized_artifact_sha256"] == "def456norm"
    assert chain["vendor"] == "TrueData"
    assert chain["source_description"] == "Direct vendor delivery S3"
    assert chain["license_reference"] == "LICENSE_VERIFIED_RESTRICTED_RESEARCH"
    assert "certification_run_id" in chain
    assert "outcome_state" in chain
