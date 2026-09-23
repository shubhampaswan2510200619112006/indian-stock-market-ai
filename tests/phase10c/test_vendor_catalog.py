"""
Test Vendor Catalog Structure and Schema Conformance for Phase 10C.
"""

import pytest
from src.research.phase10c.vendor_catalog import get_vendor_catalog

REQUIRED_FIELDS = [
    "provider_name",
    "product_name",
    "official_source",
    "verification_timestamp",
    "verification_status",
    "nifty_1m",
    "banknifty_1m",
    "nifty_5m",
    "banknifty_5m",
    "intraday_history",
    "options_history",
    "historical_bid",
    "historical_ask",
    "historical_bid_ask_level",
    "order_book_depth",
    "expired_contracts",
    "timestamp_quality",
    "access_method",
    "credentials_required",
    "subscription_required",
    "pricing",
    "licensing",
    "confidence",
    "notes",
]

EXPECTED_VENDORS = [
    "NSE Data & Analytics",
    "TrueData",
    "GlobalDataFeeds / GDFL",
    "Zerodha Kite Connect",
    "Upstox",
    "Angel One SmartAPI",
    "FYERS",
    "Yahoo Finance",
    "NSE Public Bhavcopy",
]


def test_catalog_vendor_count():
    """Verify exactly 9 evaluated vendors."""
    catalog = get_vendor_catalog()
    assert len(catalog) == 9
    names = [v["provider_name"] for v in catalog]
    for expected in EXPECTED_VENDORS:
        assert expected in names


def test_catalog_schema_conformance():
    """Verify all 24 required fields exist in every vendor record."""
    catalog = get_vendor_catalog()
    for v in catalog:
        for field in REQUIRED_FIELDS:
            assert field in v, f"Field {field} missing in vendor {v.get('provider_name')}"
            assert v[field] is not None
            assert len(str(v[field])) > 0


def test_broker_independent_evaluation():
    """Verify all brokers (Zerodha, Upstox, Angel One, FYERS) are evaluated separately."""
    catalog = get_vendor_catalog()
    broker_names = ["Zerodha Kite Connect", "Upstox", "Angel One SmartAPI", "FYERS"]
    brokers = [v for v in catalog if v["provider_name"] in broker_names]
    assert len(brokers) == 4
    # Ensure distinct product names and endpoints
    products = set(b["product_name"] for b in brokers)
    assert len(products) == 4
