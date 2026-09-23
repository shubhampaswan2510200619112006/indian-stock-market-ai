"""
News Article Deduplication Engine (Phase 7).
Deduplicates incoming articles by canonical URL and title fingerprinting.
"""

import hashlib
import re
from typing import Dict, List


class NewsDeduplicator:
    """Deduplicates articles across multiple news feeds while preserving source authority."""

    def __init__(self):
        self._seen_urls: set = set()
        self._seen_fingerprints: set = set()

    def _normalize_title(self, title: str) -> str:
        cleaned = re.sub(r"[^\w\s]", "", title.lower())
        return " ".join(cleaned.split())

    def is_duplicate(self, url: str, title: str) -> bool:
        if url and url in self._seen_urls:
            return True
        norm_title = self._normalize_title(title)
        fingerprint = hashlib.md5(norm_title.encode("utf-8")).hexdigest()
        if fingerprint in self._seen_fingerprints:
            return True

        # Record new items
        if url:
            self._seen_urls.add(url)
        self._seen_fingerprints.add(fingerprint)
        return False
