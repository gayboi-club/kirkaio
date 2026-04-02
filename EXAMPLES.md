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

asyncio.run(monitor_clan("Meowers"))
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

async def greet_when_ready(bot):
    # Wait until the websocket is populated and open
    while not bot.ws or bot.ws.closed:
        await asyncio.sleep(0.5)
        
    await bot.send_message("Bot connected and ready... Hello global chat!")

async def start_chatbot():
    # You can supply either an explicit access 'token' or a 'refresh_token'
    bot = KirkaChatBot(token="YOUR_ACCESS_TOKEN", refresh_token="")
    
    # We will share the standard KirkaClient to fetch data concurrently
    client = KirkaClient(api_key="YOUR_API_KEY")
    
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
    
    # Run the listener and the greeting task concurrently
    await asyncio.gather(
        bot.listen(),
        greet_when_ready(bot)
    )
    
    await client.close()

asyncio.run(start_chatbot())
```
