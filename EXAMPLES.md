# kirkaio - Examples

This file provides advanced examples for using `kirkaio` in common development scenarios.

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

asyncio.run(monitor_clan("awesomesam"))
```

---

## 2. Advanced Caching Strategy

Using the cache to minimize API calls for a periodic task.

```python
import asyncio
from kirkaio import KirkaClient

async def periodic_check():
    # Cache profiles for 1 hour
    async with KirkaClient("YOUR_API_KEY", cache_ttl=3600) as client:
        while True:
            # This will hit the network on the first run, and the cache on the next run
            user = await client.get_user("AWSOME")
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
