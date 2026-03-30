"""
kirkaio - async Python client for the Kirka Public API.
"""

from .client import KirkaClient
from .exceptions import (
    AuthenticationError,
    KirkaError,
    NotFoundError,
    RateLimitError,
    RouteDisabledError,
    ServerError,
    ValidationError,
)
from .models import (
    BodySkin,
    Clan,
    ClanLeaderboardEntry,
    ClanMember,
    InventoryItem,
    Leaderboard,
    PublicItem,
    Quest,
    QuestProgress,
    RankedLeaderboardEntry,
    Reward,
    RewardItem,
    SoloLeaderboardEntry,
    User,
    UserStats,
    WeaponSkin,
)

__version__ = "0.1.0"
__all__ = [
    "KirkaClient",
    # Exceptions
    "KirkaError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "RouteDisabledError",
    "ServerError",
    "ValidationError",
    # Models
    "User",
    "UserStats",
    "WeaponSkin",
    "BodySkin",
    "Clan",
    "ClanMember",
    "InventoryItem",
    "PublicItem",
    "Quest",
    "QuestProgress",
    "Reward",
    "RewardItem",
    "Leaderboard",
    "SoloLeaderboardEntry",
    "ClanLeaderboardEntry",
    "RankedLeaderboardEntry",
]