"""
In-memory cache with TTL support.

Phase 1 implementation of CacheProvider. Thread-safe via dict copy-on-read.
Suitable for single-process Streamlit / FastAPI usage.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from src.cache.base import CacheProvider


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl_seconds: Optional[int]) -> None:
        self.value = value
        self.expires_at = (time.monotonic() + ttl_seconds) if ttl_seconds else None

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.monotonic() > self.expires_at


class InMemoryCache(CacheProvider):
    """
    Simple in-memory cache with per-key TTL.

    Not suitable for multi-process deployments — use Redis for that.
    """

    def __init__(self, default_ttl_seconds: int = 60) -> None:
        self._store: dict[str, _CacheEntry] = {}
        self._default_ttl = default_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        self._store[key] = _CacheEntry(value, ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def has(self, key: str) -> bool:
        entry = self._store.get(key)
        if entry is None:
            return False
        if entry.is_expired():
            del self._store[key]
            return False
        return True

    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns number of entries removed."""
        expired_keys = [k for k, v in self._store.items() if v.is_expired()]
        for k in expired_keys:
            del self._store[k]
        return len(expired_keys)

    @property
    def size(self) -> int:
        """Number of entries (including possibly expired ones)."""
        return len(self._store)
