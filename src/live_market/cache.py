"""
Controlled TTL Cache for Live Market Engine (Phase 7).
Tracks created_at, expires_at, and source. Expired entries are tagged STALE.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    source: str

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at


class LiveDataCache:
    """In-memory TTL Cache with strict freshness tracking."""

    def __init__(self, default_ttl_seconds: int = 30):
        self.default_ttl = default_ttl_seconds
        self._store: Dict[str, CacheEntry] = {}

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, source: str = "CACHE") -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = datetime.now(timezone.utc)
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl),
            source=source,
        )
        self._store[key] = entry

    def get(self, key: str) -> Tuple[Optional[Any], bool]:
        """Returns (value, is_expired)."""
        entry = self._store.get(key)
        if not entry:
            return None, True
        return entry.value, entry.is_expired()

    def clear(self) -> None:
        self._store.clear()
