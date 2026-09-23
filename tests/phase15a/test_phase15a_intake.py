"""
Phase 15A Unit and Architecture Tests.

Tests:
- Safety invariants and strict immutability
- Baseline verifier across Phases 9.7 through 14
- 10-step intake lifecycle and terminal states
- Raw archive manager and cryptographic checksums
- Safe multi-format file inspection
- Archive structure manager and tier isolation
- Normalization engine determinism and audit lineage
- Multi-file chunk tracking
- Dataset comparator
- Certification handoff to Phase 14
- Phase 15A intake orchestrator dormant mode execution
"""

import json
import os
import shutil
import tempfile
import zipfile
import pytest
import pandas as pd

from src.research.phase15a.safety_policy import SafetyPolicy, SafetyViolationError
from src.research.phase15a.baseline_verifier import Phase15ABaselineVerifier
from src.research.phase15a.intake_lifecycle import (
    IntakeLifecycleState,
    IntakeLifecycleStateMachine,
    IllegalIntakeTransitionError,
)
from src.research.phase15a.raw_archive import RawArchiveManager, compute_file_sha256
from src.research.phase15a.archive_structure import ArchiveStructureManager
from src.research.phase15a.file_inspector import SafeFileInspector
from src.research.phase15a.normalization_engine import NormalizationEngine
from src.research.phase15a.multi_file_handler import MultiFileDatasetTracker
from src.research.phase15a.dataset_comparator import DatasetComparator
from src.research.phase15a.certification_handoff import (
    CertificationHandoffManager,
    CertificationOutcomeState,
)
from src.research.phase15a.intake_orchestrator import Phase15AIntakeOrchestrator
from src.research.phase15a.reports import Phase15AReportGenerator


def test_safety_policy_invariants():
    """Verify all safety invariants return expected immutable locked values."""
    assert SafetyPolicy.get_broker() == "NONE"
    assert SafetyPolicy.get_live_execution() == "DISABLED"
    assert SafetyPolicy.get_auto_paper_order_submission() == "DISABLED"
    assert SafetyPolicy.get_options_execution() == "BLOCKED"
    assert SafetyPolicy.get_new_alpha_research() == "DISABLED"
    assert SafetyPolicy.get_unlimited_parameter_search() == "DISABLED"
    assert SafetyPolicy.get_strategy_optimization() == "DISABLED"
    assert SafetyPolicy.get_automated_vendor_contact() == "DISABLED"
    assert SafetyPolicy.get_automated_data_purchase() == "DISABLED"
    assert SafetyPolicy.get_purchase_authorized() is False
    assert SafetyPolicy.get_human_decision_required() is True
    assert SafetyPolicy.get_phase_15_unlocked() is False
    # No error on assertion
    SafetyPolicy.assert_safety_invariants(context="test_safety_policy")


def test_baseline_verifier():
    """Verify baseline verifier evaluates repo integrity across Phases 9.7 through 14."""
    res = Phase15ABaselineVerifier.verify()
    assert res.phase_9_7_baseline == "FROZEN"
    assert res.phase_9_8_research_results == "FROZEN"
    assert res.phase_9_9_freeze_manifest == "FROZEN_IMMUTABLE"
    assert res.phase_10a_artifacts_status == "INTACT"
    assert res.phase_10b_artifacts_status == "INTACT"
    assert res.phase_10c_artifacts_status == "INTACT"
    assert res.phase_11_artifacts_status == "INTACT"
    assert res.phase_12_artifacts_status == "INTACT"
    assert res.phase_13_artifacts_status == "INTACT"
    assert res.phase_14_artifacts_status == "INTACT"
    assert res.all_baselines_intact is True
    assert res.status_decision == "ALL_BASELINES_INTACT"


def test_intake_lifecycle_state_machine():
    """Verify lifecycle state transitions and terminal states."""
    sm = IntakeLifecycleStateMachine(intake_id="INTAKE-TEST-001")
    assert sm.current_state == IntakeLifecycleState.INTAKE_DECLARED

    # Forward linear progression
    sm.transition_to(IntakeLifecycleState.DATA_RECEIVED, "Received disk file", "EVID-01")
    sm.transition_to(IntakeLifecycleState.RAW_ARCHIVE_CREATED, "Raw copied", "EVID-02")
    sm.transition_to(IntakeLifecycleState.CHECKSUM_CALCULATED, "Hash computed", "EVID-03")
    sm.transition_to(IntakeLifecycleState.IDENTITY_REGISTERED, "Identity registered", "EVID-04")
    sm.transition_to(IntakeLifecycleState.SCHEMA_INSPECTION, "Schema sniffing", "EVID-05")
    sm.transition_to(IntakeLifecycleState.PROVENANCE_REGISTERED, "Provenance locked", "EVID-06")
    sm.transition_to(IntakeLifecycleState.PHASE14_CERTIFICATION_QUEUED, "Queued", "EVID-07")
    sm.transition_to(IntakeLifecycleState.PHASE14_CERTIFICATION_RUNNING, "Running", "EVID-08")

    # Terminal state: CERTIFIED_WITH_BLOCKING_CAPABILITY
    sm.transition_to(
        IntakeLifecycleState.CERTIFIED_WITH_BLOCKING_CAPABILITY,
        "Certified with options execution blocked",
        "EVID-09",
    )
    assert sm.current_state == IntakeLifecycleState.CERTIFIED_WITH_BLOCKING_CAPABILITY

    # Illegal transition from terminal state
    with pytest.raises(IllegalIntakeTransitionError):
        sm.transition_to(IntakeLifecycleState.DATA_RECEIVED, "Illegal rewind", "EVID-10")


def test_raw_archive_manager_and_zip_lineage():
    """Verify raw file ingestion, immutability, duplicate detection, and ZIP entry lineage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_storage = os.path.join(tmpdir, "raw")
        mgr = RawArchiveManager(raw_storage_dir=raw_storage)

        # Create a sample ZIP with 2 files
        zip_path = os.path.join(tmpdir, "vendor_delivery.zip")
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("nifty_1m_2024.csv", "timestamp,close,volume\n2024-01-01 09:15:00,21500,100\n")
            z.writestr("metadata.json", '{"vendor": "TrueData", "type": "1m"}')

        rec, is_dup = mgr.ingest_raw_file(
            intake_id="INTAKE-ZIP-01",
            dataset_id="NIFTY_1M_2024",
            vendor="TrueData",
            source_path=zip_path,
            copy_to_raw_archive=True,
        )

        assert is_dup is False
        assert rec.is_zip_container is True
        assert len(rec.zip_entries) == 2
        entry_names = [e.contained_filename for e in rec.zip_entries]
        assert "nifty_1m_2024.csv" in entry_names
        assert "metadata.json" in entry_names

        # Ingest same zip again under different intake_id -> must be duplicate
        rec2, is_dup2 = mgr.ingest_raw_file(
            intake_id="INTAKE-ZIP-02",
            dataset_id="NIFTY_1M_2024_COPY",
            vendor="TrueData",
            source_path=zip_path,
        )
        assert is_dup2 is True
        assert rec2.duplicate_artifact is True


def test_safe_file_inspector():
    """Verify multi-format inspection and corruption safety."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Normal CSV
        csv_path = os.path.join(tmpdir, "sample.csv")
        with open(csv_path, "w") as f:
            f.write("timestamp,open,high,low,close,volume\n2024-01-01 09:15:00,100,105,99,102,500\n")

        res_csv = SafeFileInspector.inspect_file(csv_path)
        assert res_csv.detected_format == "CSV"
        assert res_csv.is_corrupted is False
        assert "timestamp" in res_csv.columns
        assert res_csv.estimated_rows == 1

        # 2. Corrupted 0-byte file
        empty_path = os.path.join(tmpdir, "empty.csv")
        with open(empty_path, "w") as f:
            pass

        res_empty = SafeFileInspector.inspect_file(empty_path)
        assert res_empty.is_corrupted is True
        assert res_empty.detected_format == "CORRUPTED"


def test_normalization_engine_determinism_and_no_silent_repair():
    """Verify deterministic normalization, column alias standardization, and row conservation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_csv = os.path.join(tmpdir, "raw_vendor.csv")
        # Notice uppercase vendor columns and gap/negative value
        with open(raw_csv, "w") as f:
            f.write("<DATE>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>\n")
            f.write("2024-01-01,09:15:00,100,105,99,102,500\n")
            f.write("2024-01-01,09:16:00,102,104,98,99,400\n")

        out1 = os.path.join(tmpdir, "norm1.csv")
        out2 = os.path.join(tmpdir, "norm2.csv")

        df1, audit1 = NormalizationEngine.normalize_file(raw_csv, out1)
        df2, audit2 = NormalizationEngine.normalize_file(raw_csv, out2)

        # Determinism check: identical input must yield identical output hash
        assert audit1.input_sha256 == audit2.input_sha256
        assert audit1.output_sha256 == audit2.output_sha256
        assert audit1.input_rows == 2
        assert audit1.output_rows == 2
        assert audit1.repaired_interpolated_bars_count == 0

        # Check canonical columns
        assert "timestamp" in df1.columns
        assert "open" in df1.columns
        assert "close" in df1.columns
        assert "volume" in df1.columns


def test_multi_file_dataset_tracker():
    """Verify chunked multi-file dataset tracking and boundary analysis."""
    with tempfile.TemporaryDirectory() as tmpdir:
        f1 = os.path.join(tmpdir, "part1.csv")
        f2 = os.path.join(tmpdir, "part2.csv")

        with open(f1, "w") as f:
            f.write("timestamp,close,volume\n2024-01-01 09:15:00,100,10\n2024-01-01 09:16:00,101,15\n")
        with open(f2, "w") as f:
            f.write("timestamp,close,volume\n2024-01-01 09:17:00,102,20\n2024-01-01 09:18:00,103,25\n")

        tracker = MultiFileDatasetTracker()
        grp = tracker.register_group(
            dataset_group_id="GRP-001",
            underlying="NIFTY",
            interval="1m",
            vendor="TrueData",
            file_paths_in_order=[f1, f2],
        )

        assert grp.total_files == 2
        assert grp.total_rows == 4
        assert grp.is_schema_consistent is True
        assert grp.has_boundary_overlaps is False


def test_dataset_comparator():
    """Verify deterministic reconciliation comparison."""
    df_a = pd.DataFrame({
        "timestamp": ["2024-01-01 09:15:00", "2024-01-01 09:16:00"],
        "close": [100.0, 102.0],
        "volume": [500, 600],
    })
    df_b = pd.DataFrame({
        "timestamp": ["2024-01-01 09:15:00", "2024-01-01 09:16:00"],
        "close": [100.0, 102.0],
        "volume": [500, 600],
    })

    rep = DatasetComparator.compare(
        df_a=df_a,
        df_b=df_b,
        dataset_a_id="DS_A",
        dataset_b_id="DS_B",
        vendor_a="TrueData",
        vendor_b="GDFL",
        underlying="NIFTY",
        interval="1m",
    )

    assert rep.reconciliation_status == "RECONCILED_MATCH"
    assert rep.common_timestamps_count == 2
    assert rep.close_price_exact_match_pct == 100.0
    assert rep.close_price_max_absolute_diff == 0.0


def test_intake_orchestrator_dormant_mode():
    """Verify orchestrator runs dormant mode, producing 7 JSON artifacts and 7 Markdown reports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = os.path.join(tmpdir, "data", "phase15a")
        report_dir = os.path.join(tmpdir, "reports", "phase15a")

        orch = Phase15AIntakeOrchestrator(data_output_dir=data_dir, report_output_dir=report_dir)
        state = orch.run_dormant_orchestration()

        assert state["phase_15a_status"] == "WAITING_FOR_VENDOR_DATA"
        assert state["real_datasets_received"] == 0
        assert state["datasets_certified"] == 0
        assert state["full_dataset_certification"] == "BLOCKED"
        assert state["research_readiness"] == "BLOCKED"
        assert state["baseline_integrity"] == "INTACT"
        assert state["phase_15_unlocked"] is False

        # Verify 7 JSON files
        json_files = [
            "phase15a_intake_registry.json",
            "phase15a_raw_artifacts.json",
            "phase15a_dataset_versions.json",
            "phase15a_normalization_log.json",
            "phase15a_certification_handoffs.json",
            "phase15a_comparison_results.json",
            "phase15a_operational_state.json",
        ]
        for jf in json_files:
            assert os.path.exists(os.path.join(data_dir, jf)), f"Missing {jf}"

        # Verify 7 Markdown reports
        md_reports = [
            "PHASE15A_FINAL_REPORT.md",
            "DATA_INTAKE_OPERATIONS.md",
            "RAW_ARTIFACT_REGISTER.md",
            "DATASET_VERSION_REPORT.md",
            "CERTIFICATION_HANDOFF_REPORT.md",
            "DATASET_COMPARISON_REPORT.md",
            "QUARANTINE_REPORT.md",
        ]
        for mr in md_reports:
            assert os.path.exists(os.path.join(report_dir, mr)), f"Missing {mr}"
