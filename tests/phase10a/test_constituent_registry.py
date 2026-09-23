"""
Tests for Phase 10A Point-in-Time NIFTY 50 Constituent Registry.
"""

from datetime import date
import json
from pathlib import Path
import pytest

from src.research.phase10a.constituents.constituent_registry import NIFTYConstituentRegistry


def test_constituent_count_exact_fifty():
    """Verify NIFTY 50 constituent registry returns exactly 50 members across historical dates."""
    test_dates = [
        date(2024, 1, 15),
        date(2024, 4, 15),
        date(2024, 10, 15),
        date(2025, 4, 15),
        date(2025, 10, 15),
        date(2026, 4, 15),
    ]
    for d in test_dates:
        members, status = NIFTYConstituentRegistry.get_constituents_as_of(d)
        assert status == "RESOLVED"
        assert len(members) == 50, f"Expected 50 constituents on {d}, got {len(members)}"


def test_reconstitution_event_transitions():
    """Verify additions and deletions take effect on exact effective dates."""
    # Before March 28, 2024: UPL is in, SHRIRAMFIN is out
    pre_mar_24, _ = NIFTYConstituentRegistry.get_constituents_as_of(date(2024, 3, 27))
    assert "UPL" in pre_mar_24
    assert "SHRIRAMFIN" not in pre_mar_24

    # On / after March 28, 2024: SHRIRAMFIN is in, UPL is out
    post_mar_24, _ = NIFTYConstituentRegistry.get_constituents_as_of(date(2024, 3, 28))
    assert "SHRIRAMFIN" in post_mar_24
    assert "UPL" not in post_mar_24

    # Before Sept 27, 2024: DIVISLAB and LTIM are in; BEL and TRENT are out
    pre_sep_24, _ = NIFTYConstituentRegistry.get_constituents_as_of(date(2024, 9, 26))
    assert "DIVISLAB" in pre_sep_24
    assert "LTIM" in pre_sep_24
    assert "BEL" not in pre_sep_24
    assert "TRENT" not in pre_sep_24

    # On / after Sept 27, 2024: BEL and TRENT are in; DIVISLAB and LTIM are out
    post_sep_24, _ = NIFTYConstituentRegistry.get_constituents_as_of(date(2024, 9, 27))
    assert "BEL" in post_sep_24
    assert "TRENT" in post_sep_24
    assert "DIVISLAB" not in post_sep_24
    assert "LTIM" not in post_sep_24


def test_pre_baseline_history_flagged_unresolved():
    """Verify dates prior to audited baseline (2024-01-01) are flagged UNRESOLVED rather than guessed."""
    members, status = NIFTYConstituentRegistry.get_constituents_as_of(date(2023, 12, 1))
    assert status == "UNRESOLVED_PRE_BASELINE_HISTORY"
    assert len(members) == 0


def test_constituent_registry_audit_artifact():
    """Verify data/phase10a/constituent_integrity.json confirms zero unresolved events."""
    path = Path("data/phase10a/constituent_integrity.json")
    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["POINT_IN_TIME_REGISTRY_STATUS"] == "VERIFIED_POINT_IN_TIME"
    assert data["UNRESOLVED_EVENTS"] == 0
    assert data["CONSTITUENT_EVENTS_FOUND"] >= 7
