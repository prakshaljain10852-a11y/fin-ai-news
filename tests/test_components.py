"""Test script to verify all components work locally."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config import settings
from src.fetcher import TelegramNewsletterFetcher
from src.pdf_extractor import PDFExtractor
from src.analyzer import LLMAnalyzer
from src.bot import TelegramBot


async def test_config():
    """Test configuration loading."""
    print("Testing config...")
    print(f"  API ID: {settings.telegram_api_id}")
    print(f"  Channel: {settings.target_channel}")
    print(f"  Bot Token: {settings.bot_token[:10]}...")
    print(f"  Chat ID: {settings.report_chat_id}")
    print(f"  LLM URL: {settings.llm_base_url}")
    print(f"  Model: {settings.llm_model}")
    print("✅ Config loaded")
    return True


async def test_fetcher():
    """Test Telegram connection (without fetching)."""
    print("\nTesting Telegram fetcher...")
    fetcher = TelegramNewsletterFetcher()
    try:
        await fetcher.start()
        me = await fetcher.client.get_me()
        print(f"  Connected as: {me.first_name} (@{me.username})")
        await fetcher.stop()
        print("✅ Telegram connection works")
        return True
    except Exception as e:
        print(f"❌ Fetcher test failed: {e}")
        return False


async def test_pdf_extractor():
    """Test PDF extraction with a sample."""
    print("\nTesting PDF extractor...")
    extractor = PDFExtractor()
    # Just verify it imports and initializes
    print("✅ PDF extractor initialized")
    return True


async def test_analyzer():
    """Test LLM analyzer connection."""
    print("\nTesting LLM analyzer...")
    analyzer = LLMAnalyzer()
    try:
        # Simple test call
        result = analyzer._call_llm(
            "You are a test assistant.",
            "Reply with just 'OK'",
            {"type": "json_object"}
        )
        print(f"  LLM Response: {result[:50]}...")
        print("✅ LLM connection works")
        return True
    except Exception as e:
        print(f"❌ Analyzer test failed: {e}")
        return False


async def test_bot():
    """Test Telegram bot delivery."""
    print("\nTesting Telegram bot...")
    bot = TelegramBot()
    try:
        success = bot.send_test_message()
        if success:
            print("✅ Bot test message sent")
            return True
        else:
            print("❌ Bot test failed")
            return False
    except Exception as e:
        print(f"❌ Bot test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 50)
    print("🧪 NEWSLETTER BOT - COMPONENT TESTS")
    print("=" * 50)

    tests = [
        ("Config", test_config),
        ("Telegram Fetcher", test_fetcher),
        ("PDF Extractor", test_pdf_extractor),
        ("LLM Analyzer", test_analyzer),
        ("Telegram Bot", test_bot),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = await test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append((name, False))

    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 All tests passed! Ready to deploy.")
    else:
        print("\n⚠️  Some tests failed. Fix before deploying.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())