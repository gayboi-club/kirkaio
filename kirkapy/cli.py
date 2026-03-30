"""
kirkapy CLI — quick lookups from your terminal.

Usage:
    kirkapy user <id> [--uuid]
    kirkapy clan <name>
    kirkapy leaderboard solo|clan|sad|1v1|2v2
    kirkapy quests [--type <type>]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Optional


def _get_api_key() -> str:
    key = os.environ.get("KIRKA_API_KEY", "")
    if not key:
        print("Error: KIRKA_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    return key


def _fmt_kv(label: str, value: object, width: int = 22) -> str:
    return f"  {label:<{width}} {value}"


# ─── Subcommand handlers ──────────────────────────────────────────────────────

async def cmd_user(args: argparse.Namespace) -> None:
    from kirkapy import KirkaClient

    async with KirkaClient(_get_api_key()) as client:
        user = await client.get_user(args.id, is_short_id=not args.uuid)

    print(f"\n{'─' * 40}")
    print(f"  {user.name}  [{user.short_id}]  — {user.role}")
    print(f"{'─' * 40}")
    print(_fmt_kv("Level:", user.level))
    print(_fmt_kv("Clan:", user.clan or "—"))
    print(_fmt_kv("KLO:", user.klo))
    print(_fmt_kv("KLO Ranked:", user.klo_ranked))
    print(_fmt_kv("KLO SAD:", user.klo_sad))
    print(_fmt_kv("KLO 1v1:", user.klo_1v1))
    print(_fmt_kv("KLO 2v2:", user.klo_2v2))
    print()
    print("  Stats")
    print(_fmt_kv("  Games:", user.stats.games))
    print(_fmt_kv("  Wins:", f"{user.stats.wins}  ({user.stats.win_rate}%)"))
    print(_fmt_kv("  K/D Ratio:", user.stats.kd_ratio))
    print(_fmt_kv("  Headshot Rate:", f"{user.stats.headshot_rate}%"))
    print(_fmt_kv("  Total Kills:", user.stats.kills))
    print(_fmt_kv("  Total Deaths:", user.stats.deaths))
    print(f"{'─' * 40}\n")


async def cmd_clan(args: argparse.Namespace) -> None:
    from kirkapy import KirkaClient

    async with KirkaClient(_get_api_key()) as client:
        clan = await client.get_clan(args.name)

    print(f"\n{'─' * 40}")
    print(f"  {clan.name}  ({clan.member_count} members)")
    print(f"{'─' * 40}")
    print(_fmt_kv("War Position:", clan.current_war_position))
    print(_fmt_kv("Month Scores:", clan.month_scores))
    if clan.description:
        print(_fmt_kv("Description:", clan.description))
    if clan.discord_link:
        print(_fmt_kv("Discord:", clan.discord_link))
    print()
    print("  Members")
    for m in sorted(clan.members, key=lambda x: x.month_scores, reverse=True)[:10]:
        role_tag = f"[{m.role}]" if m.role != "MEMBER" else ""
        print(f"    {m.user_name:<20} {role_tag:<10} {m.month_scores:>8} pts")
    if clan.member_count > 10:
        print(f"    … and {clan.member_count - 10} more")
    print(f"{'─' * 40}\n")


async def cmd_leaderboard(args: argparse.Namespace) -> None:
    from kirkapy import KirkaClient

    lb_map = {
        "solo": "get_solo_leaderboard",
        "clan": "get_clan_leaderboard",
        "sad": "get_ranked_sad_leaderboard",
        "1v1": "get_ranked_1v1_leaderboard",
        "2v2": "get_ranked_2v2_leaderboard",
    }

    method_name = lb_map.get(args.type)
    if not method_name:
        print(f"Unknown leaderboard type: {args.type}", file=sys.stderr)
        sys.exit(1)

    async with KirkaClient(_get_api_key()) as client:
        lb = await getattr(client, method_name)()

    print(f"\n  {'Rank':<6} {'Name':<24} Score")
    print(f"  {'─'*6} {'─'*24} {'─'*10}")
    for i, entry in enumerate(lb.results[:20], 1):
        name = getattr(entry, "name", "?")
        score = getattr(entry, "scores", getattr(entry, "klo", "?"))
        print(f"  {i:<6} {name:<24} {score}")
    print()


async def cmd_quests(args: argparse.Namespace) -> None:
    from kirkapy import KirkaClient

    async with KirkaClient(_get_api_key()) as client:
        quests = await client.get_quests(type=args.type)

    print(f"\n  Found {len(quests)} active quest(s)\n")
    for q in quests:
        print(f"  [{q.rarity.upper()}] {q.name}" + (f"  (weapon: {q.weapon})" if q.weapon else ""))
        print(f"    Goal: {q.amount}   Ends: {q.ended_at.strftime('%Y-%m-%d')}")
        for r in q.rewards:
            print(f"    Reward: {r.amount}x {r.type}")
        print()


# ─── Entry point ──────────────────────────────────────────────────────────────

async def run_cli(args: argparse.Namespace) -> None:
    handlers = {
        "user": cmd_user,
        "clan": cmd_clan,
        "leaderboard": cmd_leaderboard,
        "quests": cmd_quests,
    }
    await handlers[args.command](args)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="kirkapy",
        description="CLI tool for the Kirka Public API.",
        epilog="Set KIRKA_API_KEY environment variable to authenticate.",
    )
    sub = parser.add_subparsers(dest="command")

    # user
    p_user = sub.add_parser("user", help="Look up a player profile")
    p_user.add_argument("id", help="Player shortId or UUID")
    p_user.add_argument("--uuid", action="store_true", help="Treat <id> as a UUID")

    # clan
    p_clan = sub.add_parser("clan", help="Look up a clan")
    p_clan.add_argument("name", help="Clan name")

    # leaderboard
    p_lb = sub.add_parser("leaderboard", help="View leaderboards")
    p_lb.add_argument(
        "type",
        choices=["solo", "clan", "sad", "1v1", "2v2"],
        help="Leaderboard type",
    )

    # quests
    p_quests = sub.add_parser("quests", help="View active quests")
    p_quests.add_argument("--type", default=None, help="Filter by quest type")

    args = parser.parse_args()

    handlers = {
        "user": cmd_user,
        "clan": cmd_clan,
        "leaderboard": cmd_leaderboard,
        "quests": cmd_quests,
    }

    asyncio.run(handlers[args.command](args))


if __name__ == "__main__":
    main()