# kirkaio - Library Handbook

Welcome to the `kirkaio` library handbook. This guide provides detailed information on how to use the library's classes, models, and methods to interact with the Kirka Public API.

## Core Concepts

### client.KirkaClient

The central entry point for the library. It handles the underlying HTTP session, authentication, caching, and rate limit management.

#### Parameters
*   `api_key` (str): Your Kirka API key.
*   `cache_ttl` (float, optional): Duration in seconds to cache API responses. Set to 0 to disable. Defaults to 60.0.
*   `retry_on_rate_limit` (bool, optional): If True, automatically retries requests once when a 429 error occurs. Defaults to True.
*   `session` (aiohttp.ClientSession, optional): Provide an existing session to reuse.

#### Usage
```python
from kirkaio import KirkaClient

async with KirkaClient("YOUR_API_KEY") as client:
    # Use client here
    pass
```

### chatbot.KirkaChatBot

An experimental feature that connects to the Kirka global chat via websockets.

> [!WARNING]
> Using an automated bot in the Kirka global chat is against Kirka's Terms of Service and could result in an account ban. We do not condone the use of this feature, use it at your own risk.

#### Parameters
*   `token` (str): Your Kirka authentication token (JWT access token or blank if using refresh token).
*   `refresh_token` (str): Your Kirka refresh token to pull a new session (can be blank if using a raw access token).
*   `commands` (dict, optional): A dictionary mapping command strings (invoked via `=command`) to handlers.
*   `creds_file` (str, optional): The path to the file to persist token refresh updates. Defaults to "creds.json".

#### Methods
*   `add_command(name, handler)`: Registers a command. Handlers can be sync or async and receive a dictionary of the packet data.
*   `set_raw_handler(handler)`: Registers a handler that receives **every** parsed JSON message from the websocket. The handler receives `(data, ws)` — the parsed JSON payload and the active `aiohttp.ClientWebSocketResponse`. Can be sync or async.
*   `send_message(message)`: Asynchronously sends a text message directly to the global chat.
*   `listen()`: Coroutine that starts the websocket connection and blocks while listening for events.

#### Raw Message Handler

The raw handler is called for every JSON message received over the websocket, **before** commands are processed. This is useful for logging, analytics, or handling custom packet types beyond type 2 (chat messages).

```python
async def my_raw_handler(data, ws):
    """
    data: the parsed JSON object (dict, list, etc.)
    ws:   the active aiohttp.ClientWebSocketResponse
    """
    print(f"Packet type: {data.get('type')}")

bot.set_raw_handler(my_raw_handler)
```

> **Note:** Exceptions inside the raw handler are caught and logged, they will not crash the bot or disconnect the websocket.

---

## Data Models

All API responses are parsed into Python dataclasses for typed access.

### User

Represents a public user profile.

*   `id` (str): The persistent UUID of the player.
*   `short_id` (str): The visible short ID (e.g. "BOTTOM").
*   `name` (str): Display name.
*   `level` (int): Player's level.
*   `stats` (UserStats): Computed statistics (K/D, Win Rate, etc).

### Clan

Represents a clan and its members.

*   `name` (str): The clan's name.
*   `members` (list[ClanMember]): A list of all members currently in the clan.
*   `leader` (property): Returns the member with the "LEADER" role.
*   `current_war_position` (int): Position in the current clan championship.

### Leaderboard

A unified model for various rankings.

*   `results` (list): The ranking entries.
*   `remaining_time` (int): Seconds until the current leaderboard cycle ends.
*   `rewards` (dict): Configured rewards for the cycle.

---

## Error Handling

`kirkaio` defines several exceptions to help you handle failures graciously.

*   `KirkaError`: Generic base class for all library exceptions.
*   `AuthenticationError`: Raised when the API key is missing or invalid (401).
*   `ValidationError`: Raised when the request payload is malformed (400).
*   `NotFoundError`: Raised when a user, clan, or resource doesn't exist (404).
*   `RateLimitError`: Raised when the rate limit is exceeded and all retries are exhausted (429).
*   `RouteDisabledError`: Raised when a route is restricted by the developers (403).
*   `ServerError`: Raised for unexpected upstream issues (500).

---

## Caching Control

You can manually control the cache if needed.

```python
# Clear everything
await client.clear_cache()

# Invalidate a specific entry
await client.invalidate("user:BOTTOM")
```

---

## Other Use Cases

### Reusing a Session

If you are using `kirkaio` inside another async application (like a Discord bot), you may want to share an `aiohttp.ClientSession`.

```python
import aiohttp
from kirkaio import KirkaClient

async with aiohttp.ClientSession() as session:
    async with KirkaClient("...", session=session) as client:
        # Client will use the provided session and NOT close it on exit
        pass
```

### Direct Model Access

You can manually instantiate models if you have the raw data.

```python
from kirkaio.models import User

raw_data = { ... }
user = User.from_dict(raw_data)
```
