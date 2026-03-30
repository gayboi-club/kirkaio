import asyncio
import pytest
from kirkapy.cache import Cache

@pytest.mark.asyncio
async def test_cache_set_get():
    cache = Cache(default_ttl=1.0)
    await cache.set("key", {"data": "value"})
    assert await cache.get("key") == {"data": "value"}

@pytest.mark.asyncio
async def test_cache_expiration():
    cache = Cache(default_ttl=0.1)
    await cache.set("key", {"data": "value"})
    assert await cache.get("key") == {"data": "value"}
    await asyncio.sleep(0.2)
    assert await cache.get("key") is None

@pytest.mark.asyncio
async def test_cache_clear():
    cache = Cache(default_ttl=10.0)
    await cache.set("key1", "val1")
    await cache.set("key2", "val2")
    await cache.clear()
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None

@pytest.mark.asyncio
async def test_cache_delete():
    cache = Cache(default_ttl=10.0)
    await cache.set("key1", "val1")
    await cache.delete("key1")
    assert await cache.get("key1") is None
