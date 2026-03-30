import asyncio
import os
from dotenv import load_dotenv
from kirkaio import KirkaClient, NotFoundError

async def test_live():
    load_dotenv()
    api_key = os.getenv("KIRKA_API_KEY")
    if not api_key:
        print("Error: KIRKA_API_KEY not found in .env")
        return

    user_ids = ["#BOTTOM", "BOTTOM"]
    clan_name = "Meowers"

    async with KirkaClient(api_key) as client:
        for user_id in user_ids:
            print(f"\n--- Testing User: {user_id} ---")
            try:
                user = await client.get_user(user_id)
                print(f"Success! Found user: {user.name} ({user.short_id})")
                print(f"Level: {user.level} | K/D: {user.stats.kd_ratio}")
                
                print(f"\n--- Testing Inventory: {user_id} ---")
                inv = await client.get_user_inventory(user_id)
                print(f"Success! Found {len(inv)} items in inventory.")
                break
            except NotFoundError:
                print(f"User {user_id} not found.")
            except Exception as e:
                print(f"Error fetching user {user_id}: {e}")
        else:
            print("\nCould not find user #BOTTOM or BOTTOM.")

        print(f"\n--- Testing Clan: {clan_name} ---")
        try:
            clan = await client.get_clan(clan_name)
            print(f"Success! Found clan: {clan.name}")
            print(f"Members: {len(clan.members)} | Leader: {clan.leader.user_name if clan.leader else 'None'}")
            print("Top 3 members:")
            for m in sorted(clan.members, key=lambda x: x.month_scores, reverse=True)[:3]:
                print(f"  - {m.user_name} ({m.month_scores} pts)")
        except NotFoundError:
            print(f"Clan {clan_name} not found.")
        except Exception as e:
            print(f"Error fetching clan: {e}")

        print("\n--- Testing Leaderboards ---")
        try:
            lb = await client.get_solo_leaderboard()
            print(f"Success! Solo leaderboard has {len(lb.results)} results.")
            
            cl_lb = await client.get_clan_leaderboard()
            print(f"Success! Clan leaderboard has {len(cl_lb.results)} results.")
        except Exception as e:
            print(f"Error fetching leaderboards: {e}")

if __name__ == "__main__":
    asyncio.run(test_live())
