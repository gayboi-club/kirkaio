import asyncio
import logging
from typing import Any, Optional

import aiohttp

from .cache import Cache
from .exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    RouteDisabledError,
    ServerError,
    ValidationError,
)
from .models import (
    Clan,
    InventoryItem,
    Leaderboard,
    PublicItem,
    Quest,
    RankedLeaderboardEntry,
    ClanLeaderboardEntry,
    SoloLeaderboardEntry,
    User,
)

BASE_URL = "https://api.kirka.io"
MAX_ATTEMPTS = 2

logger = logging.getLogger(__name__)


class KirkaClient:
    """
    Async client for the Kirka Public API.

    Usage::

        async with KirkaClient(api_key="YOUR_KEY") as client:
            user = await client.get_user("BOTTOM")
            print(user.name, user.stats.kd_ratio)

    Parameters
    ----------
    api_key:
        Your Kirka API key.
    cache_ttl:
        Default TTL in seconds for cached responses. Set to 0 to disable caching.
    retry_on_rate_limit:
        If True, automatically wait and retry once when a 429 is returned.
    session:
        Optionally provide your own :class:`aiohttp.ClientSession`.
    """

    def __init__(
        self,
        api_key: str,
        *,
        cache_ttl: float = 60.0,
        retry_on_rate_limit: bool = True,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        self._api_key = api_key
        self._cache = Cache(default_ttl=cache_ttl) if cache_ttl > 0 else None
        self._retry_on_rate_limit = retry_on_rate_limit
        self._external_session = session
        self._session: Optional[aiohttp.ClientSession] = session

    # ─── Context manager ──────────────────────────────────────────────────────

    async def __aenter__(self) -> "KirkaClient":
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP session (only if created internally)."""
        if self._session and not self._external_session:
            await self._session.close()
            self._session = None

    # ─── Internal helpers ─────────────────────────────────────────────────────

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "ApiKey": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _make_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError(
                "No active session. Use `async with KirkaClient(...) as client:` "
                "or call `await client.__aenter__()` before making requests."
            )
        return self._session

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[dict] = None,
        cache_key: Optional[str] = None,
    ) -> Any:
        # Cache read
        if self._cache is not None and cache_key:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return cached

        session = self._make_session()
        url = f"{BASE_URL}{path}"

        data: Any = None
        for attempt in range(MAX_ATTEMPTS):
            async with session.request(method, url, headers=self._headers, json=json) as resp:
                if resp.status == 429 and self._retry_on_rate_limit and attempt == 0:
                    retry_after = float(resp.headers.get("Retry-After", 5))
                    logger.warning(
                        "Rate limit exceeded. Retrying in %.1f seconds... (Remaining: %s)",
                        retry_after,
                        resp.headers.get("X-RateLimit-Remaining", "unknown"),
                    )
                    await asyncio.sleep(retry_after)
                    continue
                data = await self._handle_response(resp)
                break
        else:
            # Exhausted retries without a successful response; re-raise will have already happened
            raise RateLimitError("Rate limit exceeded after retry")

        # Cache write
        if self._cache is not None and cache_key and data is not None:
            await self._cache.set(cache_key, data)
        
        return data

    @staticmethod
    async def _handle_response(resp: aiohttp.ClientResponse) -> Any:
        if resp.status in (200, 201):
            return await resp.json()
        
        body: dict = {}
        try:
            body = await resp.json()
        except Exception:
            pass

        match resp.status:
            case 400:
                raise ValidationError(body.get("message", "Validation failed"))
            case 401:
                raise AuthenticationError(body.get("message", "Missing or invalid API key"))
            case 403:
                raise RouteDisabledError("This route is disabled for public access")
            case 404:
                raise NotFoundError(f"Resource not found (code {body.get('code', '?')})")
            case 429:
                raise RateLimitError("Rate limit exceeded")
            case 500:
                raise ServerError("Unexpected server error")
            case _:
                raise ServerError(f"Unexpected status code: {resp.status}")

    # ─── User ─────────────────────────────────────────────────────────────────

    async def get_user(self, id: str, *, is_short_id: bool = True) -> User:
        """
        Fetch a public user profile.

        Parameters
        ----------
        id:
            The player's shortId (e.g. "BOTTOM") or UUID.
        is_short_id:
            Set to False if passing a UUID. Defaults to True.
        
        User:
            The user's profile data.
        """
        if is_short_id:
            id = id.lstrip("#").upper()

        data = await self._request(
            "POST",
            "/api/user/getProfile",
            json={"id": id, "isShortId": is_short_id},
            cache_key=f"user:{id}",
        )
        return User.from_dict(data)

    # ─── Quests ───────────────────────────────────────────────────────────────

    async def get_quests(self, type: Optional[str] = None) -> list[Quest]:
        """
        Fetch active quests.

        Parameters
        ----------
        type:
            Optional quest type filter (e.g. "event").
        
        Returns
        -------
        list[Quest]:
            A list of currently active quests.
        """
        payload = {"type": type} if type else {}
        data = await self._request(
            "POST",
            "/api/quests",
            json=payload,
            cache_key=f"quests:{type or 'all'}",
        )
        return [Quest.from_dict(q) for q in data]

    # ─── Inventory ────────────────────────────────────────────────────────────

    async def get_user_inventory(self, id: str, *, is_short_id: bool = True) -> list[InventoryItem]:
        """
        Fetch a user's inventory.

        Parameters
        ----------
        id:
            The player's shortId or UUID.
        is_short_id:
            Set to False if passing a UUID. Defaults to True.

        list[InventoryItem]:
            A list of items owned by the user.
        """
        if is_short_id:
            id = id.lstrip("#").upper()

        data = await self._request(
            "POST",
            "/api/inventory/user",
            json={"id": id, "isShortId": is_short_id},
            cache_key=f"inventory:{id}",
        )
        return [InventoryItem.from_dict(i) for i in data]

    async def get_all_items(self) -> list[PublicItem]:
        """
        Fetch all public items in the game.

        Returns
        -------
        list[PublicItem]:
            A list of every publicly listed item.
        """
        data = await self._request("GET", "/api/inventory/items", cache_key="items:all")
        return [PublicItem.from_dict(i) for i in data]

    # ─── Leaderboards ─────────────────────────────────────────────────────────

    async def get_solo_leaderboard(self) -> Leaderboard:
        """
        Fetch the current solo leaderboard.

        Returns
        -------
        Leaderboard:
            The solo scores leaderboard.
        """
        data = await self._request("GET", "/api/leaderboard/solo", cache_key="leaderboard:solo")
        return Leaderboard(
            results=[SoloLeaderboardEntry.from_dict(r) for r in data["results"]],
            remaining_time=data["remainingTime"],
            rewards=data["rewards"],
        )

    async def get_clan_leaderboard(self) -> Leaderboard:
        """
        Fetch the current clan championship leaderboard.

        Returns
        -------
        Leaderboard:
            The clan championship leaderboard.
        """
        data = await self._request("GET", "/api/leaderboard/clan", cache_key="leaderboard:clan")
        return Leaderboard(
            results=[ClanLeaderboardEntry.from_dict(r) for r in data["results"]],
            remaining_time=data["remainingTime"],
            rewards=data["rewards"],
        )

    async def get_ranked_sad_leaderboard(self) -> Leaderboard:
        """
        Fetch the ranked SAD leaderboard for the current season.

        Returns
        -------
        Leaderboard:
            The ranked Search and Destroy leaderboard.
        """
        data = await self._request("GET", "/api/leaderboard/rankedSAD", cache_key="leaderboard:rankedSAD")
        return Leaderboard(
            results=[RankedLeaderboardEntry.from_sad(r) for r in data["results"]],
            remaining_time=0,
            rewards={},
            season=data.get("season"),
        )

    async def get_ranked_1v1_leaderboard(self) -> Leaderboard:
        """Fetch the ranked 1v1 leaderboard for the current season."""
        data = await self._request("GET", "/api/leaderboard/ranked1V1", cache_key="leaderboard:ranked1V1")
        return Leaderboard(
            results=[RankedLeaderboardEntry.from_1v1(r) for r in data["results"]],
            remaining_time=0,
            rewards={},
            season=data.get("season"),
        )

    async def get_ranked_2v2_leaderboard(self) -> Leaderboard:
        """Fetch the ranked 2v2 leaderboard for the current season."""
        data = await self._request("GET", "/api/leaderboard/ranked2V2", cache_key="leaderboard:ranked2V2")
        return Leaderboard(
            results=[RankedLeaderboardEntry.from_2v2(r) for r in data["results"]],
            remaining_time=0,
            rewards={},
            season=data.get("season"),
        )

    # ─── Clan ─────────────────────────────────────────────────────────────────

    async def get_clan(self, name: str) -> Clan:
        """
        Fetch a clan by name.

        Parameters
        ----------
        name:
            The clan's name (e.g. "Meowers").

        Returns
        -------
        Clan:
            The clan's data, including member list.
        """
        data = await self._request("GET", f"/api/clan/{name}", cache_key=f"clan:{name}")
        return Clan.from_dict(data)

    # ─── Cache control ────────────────────────────────────────────────────────

    async def clear_cache(self) -> None:
        """Clear all cached responses."""
        if self._cache:
            await self._cache.clear()

    async def invalidate(self, key: str) -> None:
        """Manually invalidate a specific cache entry."""
        if self._cache:
            await self._cache.delete(key)
