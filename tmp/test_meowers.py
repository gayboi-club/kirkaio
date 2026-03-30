import asyncio
import os
from dotenv import load_dotenv
from kirkaio import KirkaClient

async def main():
    load_dotenv()
    api_key = os.getenv("KIRKA_API_KEY")
    if not api_key:
        print("Error: KIRKA_API_KEY not found in .env")
        return

    async with KirkaClient(api_key) as client:
        print("--- Fetching Clan: Meowers ---")
        try:
            clan = await client.get_clan("Meowers")
            print(f"Name: {clan.name}")
            print(f"Member Count: {clan.member_count}")
            print(f"War Position: #{clan.current_war_position}")
            print(f"Leader: {clan.leader.user_name if clan.leader else 'None'}")
            print("\nMembers:")
            for m in sorted(clan.members, key=lambda x: x.month_scores, reverse=True):
                role_tag = f"[{m.role}]" if m.role != "MEMBER" else ""
                print(f"  - {m.user_name:<20} {role_tag:<10} {m.month_scores:>8} pts")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
