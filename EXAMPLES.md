# kirkaio - Examples

This file provides practical examples of how to use `kirkaio` in your projects.

---

## 1. Monitoring Clan Member Activity

A script to identify the most active members of a clan.

```python
import asyncio
from kirkaio import KirkaClient

async def monitor_clan(clan_name: str):
    async with KirkaClient("YOUR_API_KEY") as client:
        clan = await client.get_clan(clan_name)
        print(f"Clan: {clan.name}")
        print("-" * 20)
        
        # Sort by month scores
        top_members = sorted(clan.members, key=lambda x: x.month_scores, reverse=True)
        
        for m in top_members[:5]:
            print(f"{m.user_name} - {m.month_scores} monthly pts")

asyncio.run(monitor_clan("gaycats"))
```

---

## 2. Scheduled Caching

Using the cache to minimize API calls for a periodic task.

```python
import asyncio
from kirkaio import KirkaClient

async def periodic_check():
    # Cache profiles for 1 hour
    async with KirkaClient("YOUR_API_KEY", cache_ttl=3600) as client:
        while True:
            # This will hit the network on the first run, and the cache on the next run
            user = await client.get_user("BOTTOM")
            print(f"User level: {user.level}")
            
            # Wait for 10 minutes
            await asyncio.sleep(600)

asyncio.run(periodic_check())
```

---

## 3. Global Leaderboard Aggregator

Aggregating all ranked leaderboards to find the best players across all modes.

```python
import asyncio
from kirkaio import KirkaClient

async def get_all_ranked():
    async with KirkaClient("YOUR_API_KEY") as client:
        # Run requests concurrently
        tasks = [
            client.get_ranked_sad_leaderboard(),
            client.get_ranked_1v1_leaderboard(),
            client.get_ranked_2v2_leaderboard()
        ]
        results = await asyncio.gather(*tasks)
        
        sad_lb, v1_lb, v2_lb = results
        
        # Combine all names to find top players in multiple modes
        all_players = {}
        for lb in results:
            for entry in lb.results:
                all_players[entry.name] = all_players.get(entry.name, 0) + 1
        
        multi_mode = [name for name, count in all_players.items() if count >= 2]
        print(f"Players ranked in multiple modes: {', '.join(multi_mode)}")

asyncio.run(get_all_ranked())
```

---

## 4. Custom Error Reporting

Handle specific cases like players that don't exist.

```python
import asyncio
from kirkaio import KirkaClient, NotFoundError

async def lookup_safely(short_id: str):
    async with KirkaClient("YOUR_API_KEY") as client:
        try:
            user = await client.get_user(short_id)
            print(f"Found {user.name} (UUID: {user.id})")
        except NotFoundError:
            print(f"Player '{short_id}' could not be found.")

asyncio.run(lookup_safely("NON_EXISTENT_PLAYER"))
```

---

## 5. Global Chat Bot (Experimental)

This script demonstrates how to connect to the global chat and listen for a `=stats <username>` command. It uses the standard `KirkaClient` to quickly fetch and reply with a player's statistics.

> [!WARNING]
> This is an experimental feature and violates the Kirka Terms of Service, which could result in an account ban. We do not condone the use of this feature, use it at your own risk.

```python
import asyncio
from kirkaio import KirkaClient, KirkaChatBot, NotFoundError

async def start_chatbot():
    # You can supply either an explicit access 'token' or a 'refresh_token'.
    # If creds.json exists, the tokens inside it will override these automatically.
    bot = KirkaChatBot(token="YOUR_ACCESS_TOKEN", refresh_token="")
    
    # We will share the standard KirkaClient to fetch data concurrently
    client = KirkaClient(api_key="YOUR_API_KEY")

    # Hook triggered when the bot successfully connects
    async def on_connect(ws):
        print("Connected to chat!")
        await ws.send_str("Bot connected and ready... Hello global chat!")
        
    bot.set_on_connect(on_connect)
    
    # Asynchronous command handler for "=" commands
    async def stats_command(packet):
        msg = packet.get("message", "")
        parts = msg[1:].split(maxsplit=1)
        
        if len(parts) < 2:
            return "Provide a username: =stats <user>"
            
        username = parts[1]
        try:
            # Query the user profile on demand and respond in chat
            user = await client.get_user(username)
            return f"{user.name} - Lvl {user.level} (K/D: {user.stats.kd_ratio})"
        except NotFoundError:
            return f"User '{username}' not found."
        except Exception:
            return "API Error occurred while fetching user."
            
    bot.add_command("stats", stats_command)
    
    # Run the listener
    listen_task = asyncio.create_task(bot.listen())
    
    try:
        await listen_task
    except asyncio.CancelledError:
        pass
    finally:
        await client.close()

asyncio.run(start_chatbot())
```

---

## 6. Fetching Active Quests

Retrieve all current quests and display their rewards. You can also filter by type (e.g. `"event"`) to focus on a specific category.

```python
import asyncio
from kirkaio import KirkaClient

async def show_quests():
    async with KirkaClient("YOUR_API_KEY") as client:
        # Fetch all active quests
        quests = await client.get_quests()

        if not quests:
            print("No active quests right now.")
            return

        print(f"Active quests ({len(quests)}):")
        print("-" * 40)
        for q in quests:
            reward_summary = ", ".join(
                f"{r.amount}x {r.type}" for r in q.rewards
            ) or "No rewards"
            weapon_note = f" [{q.weapon}]" if q.weapon else ""
            print(f"[{q.rarity.upper()}] {q.name}{weapon_note}")
            print(f"  Goal: {q.amount} | Expires: {q.ended_at.strftime('%Y-%m-%d')}")
            print(f"  Rewards: {reward_summary}")

asyncio.run(show_quests())
```

### Filtering by quest type

```python
import asyncio
from kirkaio import KirkaClient

async def show_event_quests():
    async with KirkaClient("YOUR_API_KEY") as client:
        event_quests = await client.get_quests(type="event")
        print(f"Event quests: {len(event_quests)}")
        for q in event_quests:
            print(f"  • {q.name} — {q.rarity} (ends {q.ended_at.date()})")

asyncio.run(show_event_quests())
```
