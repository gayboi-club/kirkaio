from __future__ import annotations
import time
import asyncio
from typing import Any, Optional


class CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: float):
        self.value = value
        self.expires_at = time.monotonic() + ttl


class Cache:
    """
    Simple async-safe TTL cache.

    Usage::

        cache = Cache(default_ttl=60)
        await cache.set("key", value)
        value = await cache.get("key")   # None if expired or missing
        await cache.delete("key")
        await cache.clear()
    """

    def __init__(self, default_ttl: float = 60.0):
        self._default_ttl = default_ttl
        self._store: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.monotonic() > entry.expires_at:
                del self._store[key]
                return None
            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        async with self._lock:
            self._store[key] = CacheEntry(value, ttl if ttl is not None else self._default_ttl)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    async def purge_expired(self) -> int:
        """Remove all expired entries. Returns the number of entries removed."""
        now = time.monotonic()
        async with self._lock:
            expired = [k for k, v in self._store.items() if now > v.expires_at]
            for k in expired:
                del self._store[k]
            return len(expired)

    def __len__(self) -> int:
        return len(self._store)