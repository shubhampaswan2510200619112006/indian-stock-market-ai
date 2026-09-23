"""
Abstract cache interface.

Designed so the backing store can be swapped from in-memory to Redis (or any
other store) without changing any analysis code. The analysis engine depends
on CacheProvider, never on a concrete implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheProvider(ABC):
    """
    Abstract cache interface.

    Phase 1: backed by in-memory dict with TTL.
    Future: can be backed by Redis, Memcached, etc.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        Returns None if key is missing or expired.
        """
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Store a value in the cache.
        ttl_seconds: Time-to-live. If None, uses the default TTL.
        """
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear the entire cache."""
        ...

    @abstractmethod
    def has(self, key: str) -> bool:
        """Check if a non-expired key exists."""
        ...
