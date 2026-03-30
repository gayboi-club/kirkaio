import pytest
import asyncio
import aiohttp
from aioresponses import aioresponses
from kirkapy import KirkaClient, RateLimitError, AuthenticationError, ValidationError, RouteDisabledError, ServerError

BASE = "https://api.kirka.io"

@pytest.mark.asyncio
async def test_client_init_defaults():
    client = KirkaClient("test-api-key")
    assert client._api_key == "test-api-key"
    assert client._cache is not None
    assert client._retry_on_rate_limit is True
    assert client._session is None

@pytest.mark.asyncio
async def test_client_init_custom():
    client = KirkaClient("test-api-key", cache_ttl=0, retry_on_rate_limit=False)
    assert client._cache is None
    assert client._retry_on_rate_limit is False

@pytest.mark.asyncio
async def test_client_context_manager():
    async with KirkaClient("test-api-key") as client:
        assert isinstance(client._session, aiohttp.ClientSession)
        assert not client._session.closed
    assert client._session is None

@pytest.mark.asyncio
async def test_client_external_session():
    async with aiohttp.ClientSession() as session:
        client = KirkaClient("test-api-key", session=session)
        async with client:
            assert client._session is session
        assert not session.closed
    assert session.closed

@pytest.mark.asyncio
async def test_retry_on_rate_limit_success():
    with aioresponses() as m:
        # First call fails with 429
        m.post(f"{BASE}/api/user/getProfile", status=429, headers={"Retry-After": "0.1"})
        # Second call succeeds
        m.post(f"{BASE}/api/user/getProfile", status=201, payload={"id": "1", "shortId": "S", "name": "N", "role": "R", "klo": 1, "kloRanked": 1, "kloSAD": 1, "klo1V1": 1, "klo2V2": 1, "level": 1, "totalXp": 1, "xpSinceLastLevel": 1, "xpUntilNextLevel": 1, "coins": 1, "diamonds": 1, "createdAt": "2021-01-01T00:00:00Z", "stats": {"games": 1, "wins": 1, "kills": 1, "deaths": 1, "headshots": 1, "scores": 1}})
        
        async with KirkaClient("test-key") as client:
            user = await client.get_user("S")
            assert user.name == "N"

@pytest.mark.asyncio
async def test_retry_on_rate_limit_failure():
    with aioresponses() as m:
        m.post(f"{BASE}/api/user/getProfile", status=429, headers={"Retry-After": "0.1"})
        m.post(f"{BASE}/api/user/getProfile", status=429)
        
        async with KirkaClient("test-key") as client:
            with pytest.raises(RateLimitError):
                await client.get_user("S")

@pytest.mark.asyncio
async def test_handle_response_errors():
    with aioresponses() as m:
        m.get(f"{BASE}/api/clan/bad", status=400, payload={"message": "Invalid name"})
        m.get(f"{BASE}/api/clan/forbidden", status=403)
        m.get(f"{BASE}/api/clan/error", status=500)
        m.get(f"{BASE}/api/clan/unknown", status=418)

        async with KirkaClient("test-key", cache_ttl=0) as client:
            with pytest.raises(ValidationError, match="Invalid name"):
                await client.get_clan("bad")
            with pytest.raises(RouteDisabledError):
                await client.get_clan("forbidden")
            with pytest.raises(ServerError, match="Unexpected server error"):
                await client.get_clan("error")
            with pytest.raises(ServerError, match="Unexpected status code: 418"):
                await client.get_clan("unknown")

@pytest.mark.asyncio
async def test_cache_management():
    async with KirkaClient("test-key") as client:
        await client._cache.set("test-key", {"data": "value"})
        assert await client._cache.get("test-key") == {"data": "value"}
        
        await client.invalidate("test-key")
        assert await client._cache.get("test-key") is None
        
        await client._cache.set("test-key", {"data": "value"})
        await client.clear_cache()
        assert await client._cache.get("test-key") is None
