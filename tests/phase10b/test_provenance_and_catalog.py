"""
Tests for Phase 10B Data Catalog & Provenance.
"""

import json
from pathlib import Path
import pytest

from src.research.phase10b.provenance.data_catalog_engine import Phase10BDataCatalogEngine


def test_data_catalog_and_provenance_execution():
    """Verify data catalog engine indexes all Phase 10B datasets with SHA256 hashes."""
    res = Phase10BDataCatalogEngine.generate_catalog_and_provenance()
    cat = res["catalog"]
    prov = res["provenance"]

    assert cat["total_datasets"] >= 18
    assert prov["governance_invariants"]["ALLOW_LIVE_EXECUTION"] is False
    assert prov["governance_invariants"]["OPTIONS_EXECUTION"] == "BLOCKED"
    assert prov["governance_invariants"]["NO_ALPHA_RESEARCH"] is True


def test_persisted_catalog_and_provenance_files():
    """Verify data/phase10b/data_catalog.json and provenance.json exist on disk."""
    cat_path = Path("data/phase10b/data_catalog.json")
    prov_path = Path("data/phase10b/provenance.json")

    assert cat_path.exists()
    assert prov_path.exists()

    with open(cat_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for entry in data["datasets"]:
        assert len(entry["processed_file_hash"]) == 64
        assert "dataset_id" in entry
        assert "source" in entry
        assert "quality_status" in entry
