"""
Test Provenance Records for Phase 10C.
"""

import os
import json
import pytest
from src.research.phase10c.vendor_catalog import get_provenance_records

REQUIRED_PROVENANCE_FIELDS = [
    "claim",
    "source",
    "source_url",
    "verification_timestamp",
    "verification_method",
    "confidence",
]


def test_provenance_records_completeness():
    """Verify all provenance records have required metadata."""
    records = get_provenance_records()
    assert len(records) >= 8

    for rec in records:
        for f in REQUIRED_PROVENANCE_FIELDS:
            assert f in rec, f"Missing provenance field {f} in record: {rec}"
            assert len(str(rec[f])) > 0
        assert rec["confidence"] in ["HIGH", "MEDIUM", "LOW"]
        assert rec["verification_method"] in [
            "TECHNICAL_DOCUMENTATION_INSPECTION",
            "OFFICIAL_API_REFERENCE_INSPECTION",
            "EMPIRICAL_AUDIT",
            "OFFICIAL_EXCHANGE_SPECIFICATION_INSPECTION",
        ]


def test_provenance_json_file():
    """Verify data/phase10c/provenance.json exists and conforms."""
    path = os.path.join("data", "phase10c", "provenance.json")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) >= 8
