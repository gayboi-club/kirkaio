from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


# ─── Shared ───────────────────────────────────────────────────────────────────

@dataclass
class RewardItem:
    id: str
    type: str
    rarity: str
    name: str
    parent: Optional[dict] = None


@dataclass
class Reward:
    id: str
    type: str
    amount: int
    item: Optional[RewardItem] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Reward":
        item = RewardItem(**data["item"]) if data.get("item") else None
        return cls(id=data["id"], type=data["type"], amount=data["amount"], item=item)


# ─── User ─────────────────────────────────────────────────────────────────────

@dataclass
class WeaponSkin:
    id: str
    type: str
    rarity: str
    name: str
    parent: Optional[dict] = None

    @classmethod
    def from_dict(cls, data: dict) -> "WeaponSkin":
        return cls(
            id=data["id"],
            type=data["type"],
            rarity=data["rarity"],
            name=data["name"],
            parent=data.get("parent"),
        )


@dataclass
class BodySkin:
    id: str
    type: str
    rarity: str
    name: str

    @classmethod
    def from_dict(cls, data: dict) -> "BodySkin":
        return cls(id=data["id"], type=data["type"], rarity=data["rarity"], name=data["name"])


@dataclass
class UserStats:
    """
    Performance statistics for a Kirka player.
    """
    games: int
    wins: int
    kills: int
    deaths: int
    headshots: int
    scores: int

    @property
    def kd_ratio(self) -> float:
        """The ratio of kills to deaths. Returns kills as a float if deaths is 0."""
        return round(self.kills / self.deaths, 2) if self.deaths else float(self.kills)

    @property
    def win_rate(self) -> float:
        """The percentage of games won."""
        return round(self.wins / self.games * 100, 1) if self.games else 0.0

    @property
    def headshot_rate(self) -> float:
        """The percentage of kills that were headshots."""
        return round(self.headshots / self.kills * 100, 1) if self.kills else 0.0

    @classmethod
    def from_dict(cls, data: dict) -> "UserStats":
        return cls(**data)


@dataclass
class User:
    """
    Represents a full Kirka public user profile.
    """
    id: str
    short_id: str
    name: str
    bio: Optional[str]
    role: str
    klo: float
    klo_ranked: float
    klo_sad: float
    klo_1v1: float
    klo_2v2: float
    level: int
    total_xp: int
    xp_since_last_level: int
    xp_until_next_level: int
    coins: int
    diamonds: int
    created_at: datetime
    clan: Optional[str]
    active_weapon_skin: Optional[WeaponSkin]
    active_body_skin: Optional[BodySkin]
    stats: UserStats

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            id=data["id"],
            short_id=data["shortId"],
            name=data["name"],
            bio=data.get("bio"),
            role=data["role"],
            klo=data["klo"],
            klo_ranked=data["kloRanked"],
            klo_sad=data["kloSAD"],
            klo_1v1=data["klo1V1"],
            klo_2v2=data["klo2V2"],
            level=data["level"],
            total_xp=data["totalXp"],
            xp_since_last_level=data["xpSinceLastLevel"],
            xp_until_next_level=data["xpUntilNextLevel"],
            coins=data["coins"],
            diamonds=data["diamonds"],
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
            clan=data.get("clan"),
            active_weapon_skin=WeaponSkin.from_dict(data["activeWeapon1Skin"]) if data.get("activeWeapon1Skin") else None,
            active_body_skin=BodySkin.from_dict(data["activeBodySkin"]) if data.get("activeBodySkin") else None,
            stats=UserStats.from_dict(data["stats"]),
        )


# ─── Inventory ────────────────────────────────────────────────────────────────

@dataclass
class InventoryItem:
    id: str
    type: str
    rarity: str
    name: str
    unique: bool
    published: bool
    created_at: datetime
    total_owned: int
    texture_url: Optional[str]
    render_url: Optional[str]
    amount: int
    market: int
    is_selected: bool
    acquired_at: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "InventoryItem":
        item = data["item"]
        return cls(
            id=item["id"],
            type=item["type"],
            rarity=item["rarity"],
            name=item["name"],
            unique=item["unique"],
            published=item["published"],
            created_at=datetime.fromisoformat(item["createdAt"].replace("Z", "+00:00")),
            total_owned=item["totalOwned"],
            texture_url=item.get("textureUrl"),
            render_url=item.get("renderUrl"),
            amount=data["amount"],
            market=data["market"],
            is_selected=data["isSelected"],
            acquired_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
        )


@dataclass
class PublicItem:
    id: str
    type: str
    rarity: str
    name: str
    unique: bool
    published: bool
    created_at: datetime
    total_owned: int
    texture_url: Optional[str]
    render_url: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "PublicItem":
        return cls(
            id=data["id"],
            type=data["type"],
            rarity=data["rarity"],
            name=data["name"],
            unique=data["unique"],
            published=data["published"],
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
            total_owned=data["totalOwned"],
            texture_url=data.get("textureUrl"),
            render_url=data.get("renderUrl"),
        )


# ─── Quests ───────────────────────────────────────────────────────────────────

@dataclass
class QuestProgress:
    amount: int
    completed: bool
    completed_done: bool
    reward_taken: bool

    @classmethod
    def from_dict(cls, data: dict) -> "QuestProgress":
        return cls(
            amount=data["amount"],
            completed=data["completed"],
            completed_done=data["completedDone"],
            reward_taken=data["rewardTaken"],
        )


@dataclass
class Quest:
    id: str
    type: str
    name: str
    weapon: Optional[str]
    amount: int
    ended_at: datetime
    rarity: str
    rewards: list[Reward]
    progress: QuestProgress

    @classmethod
    def from_dict(cls, data: dict) -> "Quest":
        return cls(
            id=data["id"],
            type=data["type"],
            name=data["name"],
            weapon=data.get("weapon"),
            amount=data["amount"],
            ended_at=datetime.fromisoformat(data["endedAt"].replace("Z", "+00:00")),
            rarity=data["rarity"],
            rewards=[Reward.from_dict(r) for r in data.get("rewards", [])],
            progress=QuestProgress.from_dict(data["progress"]),
        )


# ─── Leaderboard ──────────────────────────────────────────────────────────────

@dataclass
class SoloLeaderboardEntry:
    user_id: str
    name: str
    scores: int

    @classmethod
    def from_dict(cls, data: dict) -> "SoloLeaderboardEntry":
        return cls(user_id=data["userId"], name=data["name"], scores=data["scores"])


@dataclass
class ClanLeaderboardEntry:
    clan_id: str
    name: str
    members_count: int
    scores: int

    @classmethod
    def from_dict(cls, data: dict) -> "ClanLeaderboardEntry":
        return cls(
            clan_id=data["clanId"],
            name=data["name"],
            members_count=data["membersCount"],
            scores=data["scores"],
        )


@dataclass
class RankedLeaderboardEntry:
    id: str
    short_id: str
    role: str
    name: str
    klo: float

    @classmethod
    def from_sad(cls, data: dict) -> "RankedLeaderboardEntry":
        return cls(id=data["id"], short_id=data["shortId"], role=data["role"], name=data["name"], klo=data["kloSAD"])

    @classmethod
    def from_1v1(cls, data: dict) -> "RankedLeaderboardEntry":
        return cls(id=data["id"], short_id=data["shortId"], role=data["role"], name=data["name"], klo=data["klo1V1"])

    @classmethod
    def from_2v2(cls, data: dict) -> "RankedLeaderboardEntry":
        return cls(id=data["id"], short_id=data["shortId"], role=data["role"], name=data["name"], klo=data["klo2V2"])


@dataclass
class Leaderboard:
    results: list
    remaining_time: int
    rewards: dict
    season: Optional[str] = None


# ─── Clan ─────────────────────────────────────────────────────────────────────

@dataclass
class ClanMember:
    user_id: str
    user_name: str
    role: str
    all_scores: int
    month_scores: int
    joined_at: datetime

    @classmethod
    def from_dict(cls, data: dict) -> "ClanMember":
        return cls(
            user_id=data["user"]["id"],
            user_name=data["user"]["name"],
            role=data["role"],
            all_scores=data["allScores"],
            month_scores=data["monthScores"],
            joined_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
        )


@dataclass
class Clan:
    """
    Represents a Kirka clan and its members.
    """
    id: str
    name: str
    description: Optional[str]
    discord_link: Optional[str]
    all_scores: int
    current_war_position: int
    month_scores: int
    created_at: datetime
    members: list[ClanMember]

    @property
    def member_count(self) -> int:
        """Number of members currently in the clan."""
        return len(self.members)

    @property
    def leader(self) -> Optional[ClanMember]:
        """The clan leader, if present in the member list."""
        return next((m for m in self.members if m.role == "LEADER"), None)

    @classmethod
    def from_dict(cls, data: dict) -> "Clan":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            discord_link=data.get("discordLink"),
            all_scores=data["allScores"],
            current_war_position=data["currentClanWarPosition"],
            month_scores=data["monthScores"],
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
            members=[ClanMember.from_dict(m) for m in data.get("members", [])],
        )