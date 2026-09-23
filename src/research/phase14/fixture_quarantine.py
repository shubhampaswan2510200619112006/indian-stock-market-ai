"""
Phase 14 Test Fixture Quarantine Manager.

Enforces strict isolation between production data and test fixtures.
Quarantines any dataset containing fixture indicators (MOCK, FIXTURE, TEST_CSV, SYNTHETIC, PIT_LEAK_TEST)
across filenames, dataset identifiers, vendor metadata, or internal attributes.
Quarantined datasets are completely barred from contributing to production session counts,
historical coverage, readiness gates, or research certification.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class FixtureQuarantineManager:
    """
    Evaluates datasets for test fixture contamination and enforces quarantine.
    """

    FIXTURE_INDICATORS = [
        "MOCK",
        "FIXTURE",
        "TEST_CSV",
        "SYNTHETIC",
        "PIT_LEAK_TEST",
        "TEST_FIXTURE",
        "DUMMY",
    ]

    @classmethod
    def check_quarantine(
        cls,
        dataset_id: str,
        source_file: str,
        product_name: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Returns (is_quarantined, quarantine_reason).
        """
        meta = metadata or {}

        # 1. Explicit metadata / tag checks
        if meta.get("is_fixture") is True or meta.get("is_synthetic") is True or meta.get("is_mock") is True:
            return True, "EXPLICIT_FIXTURE_FLAG: Dataset metadata declares fixture/synthetic status."

        # 2. Textual indicators check across ID, path, and product
        text_fields = [dataset_id.upper(), source_file.upper(), product_name.upper()]
        for text in text_fields:
            for ind in cls.FIXTURE_INDICATORS:
                if ind in text:
                    return True, f"CONTAMINATION_VIOLATION: Found fixture indicator '{ind}' in dataset identity/source."

        # 3. Source path directory check
        source_norm = source_file.replace("\\", "/").lower()
        if "/tests/" in source_norm or "/fixtures/" in source_norm or "scratch" in source_norm:
            return True, f"PATH_CONTAMINATION_VIOLATION: Source file '{source_file}' resides in test/fixture directory."

        return False, None
