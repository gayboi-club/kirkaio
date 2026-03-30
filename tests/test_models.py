from datetime import datetime, timezone
import pytest
from kirkapy.models import User, UserStats, Clan, ClanMember, Quest, InventoryItem, PublicItem

def test_user_stats_properties():
    stats = UserStats(games=100, wins=50, kills=200, deaths=100, headshots=50, scores=1000)
    assert stats.kd_ratio == 2.0
    assert stats.win_rate == 50.0
    assert stats.headshot_rate == 25.0

def test_user_stats_zero_division():
    stats = UserStats(games=0, wins=0, kills=0, deaths=0, headshots=0, scores=0)
    assert stats.kd_ratio == 0.0
    assert stats.win_rate == 0.0
    assert stats.headshot_rate == 0.0

def test_user_from_dict():
    data = {
        "id": "u1",
        "shortId": "S1",
        "name": "User 1",
        "bio": "Bio",
        "role": "USER",
        "klo": 1000,
        "kloRanked": 1000,
        "kloSAD": 1000,
        "klo1V1": 1000,
        "klo2V2": 1000,
        "level": 10,
        "totalXp": 1000,
        "xpSinceLastLevel": 100,
        "xpUntilNextLevel": 900,
        "coins": 100,
        "diamonds": 10,
        "createdAt": "2024-03-30T12:00:00Z",
        "clan": "Clan1",
        "activeWeapon1Skin": None,
        "activeBodySkin": None,
        "stats": {"games": 10, "wins": 5, "kills": 50, "deaths": 25, "headshots": 10, "scores": 500}
    }
    user = User.from_dict(data)
    assert user.name == "User 1"
    assert user.created_at == datetime(2024, 3, 30, 12, 0, tzinfo=timezone.utc)
    assert user.stats.kd_ratio == 2.0

def test_clan_properties():
    member1 = ClanMember(user_id="u1", user_name="Leader", role="LEADER", all_scores=100, month_scores=10, joined_at=datetime.now())
    member2 = ClanMember(user_id="u2", user_name="Member", role="MEMBER", all_scores=50, month_scores=5, joined_at=datetime.now())
    clan = Clan(
        id="c1",
        name="Clan1",
        description="Desc",
        discord_link=None,
        all_scores=150,
        current_war_position=1,
        month_scores=15,
        created_at=datetime.now(),
        members=[member1, member2]
    )
    assert clan.member_count == 2
    assert clan.leader == member1

def test_inventory_item_from_dict():
    data = {
        "amount": 5,
        "market": 100,
        "isSelected": False,
        "createdAt": "2024-03-30T12:00:00Z",
        "item": {
            "id": "i1",
            "type": "WEAPON",
            "rarity": "rare",
            "name": "Gun",
            "unique": False,
            "published": True,
            "createdAt": "2024-01-01T00:00:00Z",
            "totalOwned": 1000
        }
    }
    item = InventoryItem.from_dict(data)
    assert item.name == "Gun"
    assert item.amount == 5
    assert item.acquired_at == datetime(2024, 3, 30, 12, 0, tzinfo=timezone.utc)
