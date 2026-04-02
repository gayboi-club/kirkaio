# kirkaio

Async Python client for the [Kirka](https://kirka.io) Public API.

Made by gayboi.club for the kirka.io community :3

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/fags-inc/kirkaio/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://pyproject.toml)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/fags-inc/kirkaio/releases)

## Installation

```bash
pip install kirkaio
```

Requires Python 3.11+.

## Quickstart :3

```python
import asyncio
from kirkaio import KirkaClient

async def main():
    async with KirkaClient("YOUR_API_KEY") as client:
        # Look up a player
        user = await client.get_user("BOTTOM")
        print(f"{user.name} - Level {user.level}")
        print(f"K/D: {user.stats.kd_ratio}  Win Rate: {user.stats.win_rate}%")

        # Clan info
        clan = await client.get_clan("Meowers")
        print(f"{clan.name} - War Position #{clan.current_war_position}")

        # Leaderboard
        lb = await client.get_solo_leaderboard()
        for i, entry in enumerate(lb.results[:5], 1):
            print(f"#{i} {entry.name} - {entry.scores} pts")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Key

Get your API key by joining the [Kirka Discord](https://discord.gg/kirka) :3
Set it as an environment variable for the CLI:

```bash
export KIRKA_API_KEY="your_key_here"
```

## Features

- Fully async - built on aiohttp.
- Typed models - all responses deserialize into Python dataclasses.
- TTL caching - avoid redundant requests (configurable, default 60s).
- Rate limit handling - auto-retry with Retry-After back-off.
- CLI tool - quick lookups straight from your terminal :3
- **Global Chat Bot** - experimental websocket listener for the global chat.

## Client Options

```python
KirkaClient(
    api_key="...",
    cache_ttl=60.0,           # seconds; set 0 to disable
    retry_on_rate_limit=True,  # auto-retry on 429
)
```

## CLI Usage

```bash
# Player profile
kirkaio user BOTTOM

# Clan details
kirkaio clan Meowers

# Leaderboards: solo | clan | sad | 1v1 | 2v2
kirkaio leaderboard solo

# Active quests
kirkaio quests
kirkaio quests --type event
```

## Available Methods :3

| Method | Description |
|---|---|
| `get_user(id, is_short_id=True)` | Player profile by shortId or UUID |
| `get_quests(type=None)` | Active quests |
| `get_user_inventory(id, is_short_id=True)` | User's inventory |
| `get_all_items()` | All public game items |
| `get_solo_leaderboard()` | Solo scores leaderboard |
| `get_clan_leaderboard()` | Clan championship leaderboard |
| `get_ranked_sad_leaderboard()` | Ranked SAD leaderboard |
| `get_ranked_1v1_leaderboard()` | Ranked 1v1 leaderboard |
| `get_ranked_2v2_leaderboard()` | Ranked 2v2 leaderboard |
| `get_clan(name)` | Clan details + members |

## Global Chat Bot (Experimental)

> [!WARNING]
> Using an automated bot in the Kirka global chat **is against Kirka's Terms of Service and could result in an account ban**. We do not condone the use of this feature, use it at your own risk.

```python
import asyncio
from kirkaio import KirkaChatBot

async def main():
    def ping_handler(packet):
        return "Pong!"
        
    bot = KirkaChatBot("your_token", "your_refresh_token")
    bot.add_command("ping", ping_handler)
    
    await bot.listen()

if __name__ == "__main__":
    asyncio.run(main())
```

### Raw Message Handler

You can also hook into **every** raw websocket message for logging, analytics, or custom packet handling:

```python
import asyncio
from kirkaio import KirkaChatBot

async def on_raw_message(data, ws):
    print(f"Received packet type: {data.get('type')}")

async def main():
    bot = KirkaChatBot("your_token", "your_refresh_token")
    bot.set_raw_handler(on_raw_message)
    await bot.listen()

if __name__ == "__main__":
    asyncio.run(main())
```

## Error Handling

```python
from kirkaio import KirkaClient, NotFoundError, RateLimitError, AuthenticationError

async with KirkaClient("...") as client:
    try:
        user = await client.get_user("SOMEONE")
    except NotFoundError:
        print("Player not found")
    except RateLimitError:
        print("Slow down!")
    except AuthenticationError:
        print("Bad API key")
```

## License

This project is licensed under the MIT License :3
See the [LICENSE](LICENSE) file for details :P
