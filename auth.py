"""One-time authentication script to create session file.
Run this in a regular terminal (cmd, PowerShell, or Git Bash) where you can enter the OTP code."""
import asyncio
import sys
sys.path.insert(0, "src")

from src.config import settings
from telethon import TelegramClient


async def main():
    print("=" * 50)
    print("Telegram Authentication")
    print("=" * 50)
    print(f"Phone: {settings.telegram_phone}")
    print(f"API ID: {settings.telegram_api_id}")
    print(f"Session file: {settings.session_name}.session")
    print()

    client = TelegramClient(
        settings.session_name,
        settings.telegram_api_id,
        settings.telegram_api_hash
    )

    try:
        print("Connecting...")
        await client.start(phone=settings.telegram_phone)
        
        me = await client.get_me()
        print(f"\n✅ Successfully logged in as: {me.first_name} (@{me.username})")
        print(f"Session saved to: {settings.session_name}.session")
        
        # Test channel access
        print(f"\nTesting channel access: {settings.target_channel}")
        entity = await client.get_entity(settings.target_channel)
        print(f"Channel: {entity.title} (@{entity.username})")
        
        # Fetch latest message
        async for msg in client.iter_messages(entity, limit=1):
            print(f"Latest message ID: {msg.id}, Date: {msg.date}")
            if msg.document:
                print(f"  Has document: Yes (mime: {msg.file.mime_type if msg.file else 'unknown'})")
            else:
                print(f"  Has document: No")
        
        print("\n✅ Authentication complete! Session file is ready.")
        print("You can now deploy to GitHub Actions.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())