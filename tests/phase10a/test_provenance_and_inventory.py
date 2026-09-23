"""
Tests for Phase 10A Provenance, Versioning & Data Inventory Engine.
"""

import json
from pathlib import Path
import pytest

from src.research.phase10a.provenance.provenance_engine import Phase10AProvenanceEngine


def test_provenance_engine_execution():
    """Verify provenance engine tracks datasets across all three quality tiers."""
    res = Phase10AProvenanceEngine.generate_inventory_and_provenance()
    inv = res["inventory"]
    prov = res["provenance"]

    assert inv["total_datasets_tracked"] >= 15
    assert inv["tier_summary"]["TIER_1_AUTHORITATIVE"] >= 2
    assert inv["tier_summary"]["TIER_2_RESEARCH_GRADE"] >= 10
    assert inv["tier_summary"]["TIER_3_EXPLORATORY_ONLY"] >= 2

    assert prov["governance_invariants"]["ALLOW_LIVE_EXECUTION"] is False
    assert prov["governance_invariants"]["OPTIONS_EXECUTION"] == "BLOCKED"


def test_persisted_inventory_artifacts():
    """Verify data_inventory.json and provenance.json artifacts exist with valid hashes."""
    inv_path = Path("data/phase10a/data_inventory.json")
    prov_path = Path("data/phase10a/provenance.json")

    assert inv_path.exists()
    assert prov_path.exists()

    with open(inv_path, "r", encoding="utf-8") as f:
        inv_data = json.load(f)
    for ds in inv_data["datasets"]:
        assert len(ds["sha256"]) == 64
        assert ds["tier"] in ["TIER_1_AUTHORITATIVE", "TIER_2_RESEARCH_GRADE", "TIER_3_EXPLORATORY_ONLY"]
