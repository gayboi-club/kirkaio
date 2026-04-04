"""
Tests for kirkaio — uses aioresponses to mock HTTP calls.
Run with: pytest tests/
"""

import pytest
from aioresponses import aioresponses

from kirkaio import AuthenticationError, KirkaClient, NotFoundError, RateLimitError
from kirkaio.models import Clan, Leaderboard, Quest, User

API_KEY = "test-key"
BASE = "https://api.kirka.io"

# ─── Fixtures ─────────────────────────────────────────────────────────────────

USER_PAYLOAD = {
    "id": "9b1e9617-fb0c-48e6-8be0-c49720ad1e7a",
    "shortId": "BOTTOM",
    "name": "BOTTOM",
    "bio": "Co-Developer",
    "role": "ADMIN",
    "klo": 1200.0,
    "kloRanked": 1100.0,
    "kloSAD": 1050.0,
    "klo1V1": 1000.0,
    "klo2V2": 1000.0,
    "level": 25,
    "totalXp": 225140,
    "xpSinceLastLevel": 8740,
    "xpUntilNextLevel": 13250,
    "coins": 521690,
    "diamonds": 19255,
    "createdAt": "2021-07-25T06:48:42.617Z",
    "clan": "Meowers",
    "activeWeapon1Skin": None,
    "activeBodySkin": None,
    "stats": {
        "games": 1444,
        "wins": 838,
        "kills": 27864,
        "deaths": 19248,
        "headshots": 18355,
        "scores": 964356,
    },
}

CLAN_PAYLOAD = {
    "id": "c51c5633-1714-48aa-a0b3-94750e948844",
    "name": "Meowers",
    "description": "sam",
    "discordLink": None,
    "allScores": 0,
    "currentClanWarPosition": 7,
    "monthScores": 128450,
    "createdAt": "2025-07-16T15:46:48.795Z",
    "members": [
        {
            "user": {
                "id": "9b1e9617-fb0c-48e6-8be0-c49720ad1e7a",
                "name": "GlitchysBottom",
                "shortId": "BOTTOM",
                "level": 20,
            },
            "role": "LEADER",
            "allScores": 0,
            "monthScores": 4210,
            "createdAt": "2025-07-16T15:46:48.796Z",
        }
    ],
}

SOLO_LB_PAYLOAD = {
    "results": [{"userId": "abc", "name": "Player1", "scores": 9999}],
    "remainingTime": 3600,
    "rewards": {},
}

QUEST_PAYLOAD = [
    {
        "id": "f7a03a22-64aa-4af0-8725-579fd4224fa7",
        "type": "event",
        "name": "KILLS_WITH_GUN",
        "weapon": "shark",
        "amount": 10,
        "endedAt": "2026-04-01T00:00:00.000Z",
        "rarity": "legendary",
        "rewards": [{"id": "c5bbd04c", "type": "COINS", "amount": 500, "item": None}],
        "progress": {
            "amount": 0,
            "completed": False,
            "completedDone": False,
            "rewardTaken": False,
        },
    }
]

# ─── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user_success():
    with aioresponses() as m:
        m.post(f"{BASE}/api/user/getProfile", payload=USER_PAYLOAD, status=201)
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            user = await client.get_user("BOTTOM")

    assert isinstance(user, User)
    assert user.name == "BOTTOM"
    assert user.short_id == "BOTTOM"
    assert user.level == 25
    assert user.stats.kd_ratio == round(27864 / 19248, 2)
    assert user.stats.win_rate == round(838 / 1444 * 100, 1)


@pytest.mark.asyncio
async def test_get_user_not_found():
    with aioresponses() as m:
        m.post(
            f"{BASE}/api/user/getProfile",
            payload={"statusCode": 404, "code": 102},
            status=404,
        )
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            with pytest.raises(NotFoundError):
                await client.get_user("NOBODY")


@pytest.mark.asyncio
async def test_get_user_auth_error():
    with aioresponses() as m:
        m.post(
            f"{BASE}/api/user/getProfile",
            payload={"statusCode": 401, "message": "Missing ApiKey header"},
            status=401,
        )
        async with KirkaClient("bad-key", cache_ttl=0) as client:
            with pytest.raises(AuthenticationError):
                await client.get_user("BOTTOM")


@pytest.mark.asyncio
async def test_get_clan():
    with aioresponses() as m:
        m.get(f"{BASE}/api/clan/Meowers", payload=CLAN_PAYLOAD, status=200)
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            clan = await client.get_clan("Meowers")

    assert isinstance(clan, Clan)
    assert clan.name == "Meowers"
    assert clan.member_count == 1
    assert clan.leader is not None
    assert clan.leader.user_name == "BOTTOM"


@pytest.mark.asyncio
async def test_get_user_inventory():
    payload = [
        {
            "amount": 1,
            "market": 500,
            "isSelected": True,
            "createdAt": "2024-03-30T10:00:00Z",
            "item": {
                "id": "item-1",
                "type": "WEAPON",
                "rarity": "epic",
                "name": "Cool Gun",
                "unique": False,
                "published": True,
                "createdAt": "2024-01-01T00:00:00Z",
                "totalOwned": 100,
            },
        }
    ]
    with aioresponses() as m:
        m.post(f"{BASE}/api/inventory/user", payload=payload, status=201)
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            inv = await client.get_user_inventory("BOTTOM")

    assert len(inv) == 1
    assert inv[0].name == "Cool Gun"
    assert inv[0].amount == 1


@pytest.mark.asyncio
async def test_get_all_items():
    payload = [
        {
            "id": "item-1",
            "type": "WEAPON",
            "rarity": "epic",
            "name": "Cool Gun",
            "unique": False,
            "published": True,
            "createdAt": "2024-01-01T00:00:00Z",
            "totalOwned": 100,
        }
    ]
    with aioresponses() as m:
        m.get(f"{BASE}/api/inventory/items", payload=payload, status=200)
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            items = await client.get_all_items()

    assert len(items) == 1
    assert items[0].name == "Cool Gun"


@pytest.mark.asyncio
async def test_get_clan_leaderboard():
    payload = {
        "results": [
            {"clanId": "c1", "name": "Clan1", "membersCount": 10, "scores": 5000}
        ],
        "remainingTime": 3600,
        "rewards": {},
    }
    with aioresponses() as m:
        m.get(f"{BASE}/api/leaderboard/clan", payload=payload, status=200)
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            lb = await client.get_clan_leaderboard()

    assert len(lb.results) == 1
    assert lb.results[0].name == "Clan1"


@pytest.mark.asyncio
async def test_ranked_leaderboards():
    sad_payload = {
        "results": [
            {"id": "u1", "shortId": "S1", "role": "USER", "name": "N1", "kloSAD": 1500}
        ],
        "season": "1",
    }
    v1_payload = {
        "results": [
            {"id": "u2", "shortId": "S2", "role": "USER", "name": "N2", "klo1V1": 1600}
        ],
        "season": "1",
    }
    v2_payload = {
        "results": [
            {"id": "u3", "shortId": "S3", "role": "USER", "name": "N3", "klo2V2": 1700}
        ],
        "season": "1",
    }

    with aioresponses() as m:
        m.get(f"{BASE}/api/leaderboard/rankedSAD", payload=sad_payload, status=200)
        m.get(f"{BASE}/api/leaderboard/ranked1V1", payload=v1_payload, status=200)
        m.get(f"{BASE}/api/leaderboard/ranked2V2", payload=v2_payload, status=200)

        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            sad = await client.get_ranked_sad_leaderboard()
            v1 = await client.get_ranked_1v1_leaderboard()
            v2 = await client.get_ranked_2v2_leaderboard()

    assert sad.results[0].klo == 1500
    assert v1.results[0].klo == 1600
    assert v2.results[0].klo == 1700
    assert sad.season == "1"


@pytest.mark.asyncio
async def test_get_user_uuid():
    with aioresponses() as m:
        m.post(f"{BASE}/api/user/getProfile", payload=USER_PAYLOAD, status=201)
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            user = await client.get_user(
                "9b1e9617-fb0c-48e6-8be0-c49720ad1e7a", is_short_id=False
            )
    assert user.id == "9b1e9617-fb0c-48e6-8be0-c49720ad1e7a"


@pytest.mark.asyncio
async def test_get_solo_leaderboard():
    with aioresponses() as m:
        m.get(f"{BASE}/api/leaderboard/solo", payload=SOLO_LB_PAYLOAD, status=200)
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            lb = await client.get_solo_leaderboard()

    assert isinstance(lb, Leaderboard)
    assert len(lb.results) == 1
    assert lb.results[0].name == "Player1"
    assert lb.remaining_time == 3600


@pytest.mark.asyncio
async def test_get_quests():
    with aioresponses() as m:
        m.post(f"{BASE}/api/quests", payload=QUEST_PAYLOAD, status=201)
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            quests = await client.get_quests()

    assert len(quests) == 1
    assert isinstance(quests[0], Quest)
    assert quests[0].name == "KILLS_WITH_GUN"
    assert quests[0].rarity == "legendary"


@pytest.mark.asyncio
async def test_get_quests_with_type_filter():
    """Passing a type string sends it as the JSON body and returns filtered quests."""
    with aioresponses() as m:
        m.post(f"{BASE}/api/quests", payload=QUEST_PAYLOAD, status=201)
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            quests = await client.get_quests(type="event")

    assert len(quests) == 1
    assert quests[0].type == "event"


@pytest.mark.asyncio
async def test_get_quests_empty_list():
    """API may return an empty list when there are no active quests."""
    with aioresponses() as m:
        m.post(f"{BASE}/api/quests", payload=[], status=201)
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            quests = await client.get_quests()

    assert quests == []


@pytest.mark.asyncio
async def test_get_quests_no_weapon():
    """Quests without a weapon field should parse correctly with weapon=None."""
    payload = [
        {
            "id": "aabbccdd-0000-0000-0000-000000000001",
            "type": "daily",
            "name": "PLAY_GAMES",
            "amount": 5,
            "endedAt": "2026-04-10T00:00:00.000Z",
            "rarity": "common",
            "rewards": [],
            "progress": {
                "amount": 2,
                "completed": False,
                "completedDone": False,
                "rewardTaken": False,
            },
        }
    ]
    with aioresponses() as m:
        m.post(f"{BASE}/api/quests", payload=payload, status=201)
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            quests = await client.get_quests()

    assert quests[0].weapon is None
    assert quests[0].name == "PLAY_GAMES"
    assert quests[0].rewards == []
    assert quests[0].progress.amount == 2


@pytest.mark.asyncio
async def test_get_quests_coin_reward():
    """Quest rewards with type COINS are parsed correctly."""
    quest = QUEST_PAYLOAD[0]
    with aioresponses() as m:
        m.post(f"{BASE}/api/quests", payload=[quest], status=201)
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            quests = await client.get_quests()

    reward = quests[0].rewards[0]
    assert reward.type == "COINS"
    assert reward.amount == 500
    assert reward.item is None


@pytest.mark.asyncio
async def test_get_quests_auth_error():
    """401 from the quests endpoint should raise AuthenticationError."""
    with aioresponses() as m:
        m.post(
            f"{BASE}/api/quests",
            payload={"statusCode": 401, "message": "Missing ApiKey header"},
            status=401,
        )
        async with KirkaClient("bad-key", cache_ttl=0) as client:
            with pytest.raises(AuthenticationError):
                await client.get_quests()


@pytest.mark.asyncio
async def test_get_quests_validation_error():
    """400 from the quests endpoint should raise ValidationError."""
    from kirkaio import ValidationError

    with aioresponses() as m:
        m.post(
            f"{BASE}/api/quests",
            payload={"message": "Invalid quest type"},
            status=400,
        )
        async with KirkaClient(API_KEY, cache_ttl=0) as client:
            with pytest.raises(ValidationError):
                await client.get_quests(type="__bad__")


@pytest.mark.asyncio
async def test_get_quests_cache_key_segregation():
    """Typed and untyped quest calls should use separate cache keys."""
    with aioresponses() as m:
        # Two distinct HTTP calls, each cached independently
        m.post(f"{BASE}/api/quests", payload=QUEST_PAYLOAD, status=201)
        m.post(f"{BASE}/api/quests", payload=[], status=201)
        async with KirkaClient(API_KEY, cache_ttl=60) as client:
            all_quests = await client.get_quests()
            event_quests = await client.get_quests(type="daily")

    # Different cache keys — different results
    assert len(all_quests) == 1
    assert len(event_quests) == 0


@pytest.mark.asyncio
async def test_caching():
    with aioresponses() as m:
        # Mock the request once, but set repeat=True to avoid potential mock-exhausted errors
        m.post(
            f"{BASE}/api/user/getProfile", payload=USER_PAYLOAD, status=201, repeat=True
        )
        async with KirkaClient(API_KEY, cache_ttl=60) as client:
            user1 = await client.get_user("BOTTOM")
            assert len(client._cache._store) == 1
            # Second call — should come from cache
            user2 = await client.get_user("BOTTOM")

    assert user1.id == user2.id


@pytest.mark.asyncio
async def test_rate_limit_raises():
    with aioresponses() as m:
        m.post(f"{BASE}/api/user/getProfile", status=429)
        m.post(f"{BASE}/api/user/getProfile", status=429)
        async with KirkaClient(
            API_KEY, cache_ttl=0, retry_on_rate_limit=False
        ) as client:
            with pytest.raises(RateLimitError):
                await client.get_user("BOTTOM")
