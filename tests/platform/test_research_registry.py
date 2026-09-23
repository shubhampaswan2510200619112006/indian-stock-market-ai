"""
Test Canonical Research Registry.
"""

import pytest
from src.platform.research_registry.registry import ResearchRegistry


def test_research_registry_contents():
    reg = ResearchRegistry()
    items = reg.all_items()
    assert len(items) >= 9

    # Verify P98-H001 through H008
    h001 = reg.get_item("P98-H001")
    assert h001 is not None
    assert h001.status == "INSUFFICIENT_DATA"
    assert h001.required_data == "intraday_5m"

    h003 = reg.get_item("P98-H003")
    assert h003 is not None
    assert h003.status == "REJECTED"

    h006 = reg.get_item("P98-H006")
    assert h006 is not None
    assert h006.status == "REJECTED"
    assert "Survivorship bias risk" in h006.reason_if_blocked

    h008 = reg.get_item("P98-H008")
    assert h008 is not None
    assert h008.status == "INSUFFICIENT_DATA"
    assert "execution backtest BLOCKED" in h008.reason_if_blocked

    # Verify cross-sectional template
    cs = reg.get_item("TMPL-CS-001")
    assert cs is not None
    assert cs.status == "READY"


def test_registry_serialization():
    reg = ResearchRegistry()
    d = reg.to_dict()
    assert "P98-H001" in d
    assert d["P98-H001"]["confirmation_status"] == "INSUFFICIENT_DATA"
