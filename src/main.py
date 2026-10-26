"""Main orchestrator: fetch → extract → analyze → deliver."""
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.fetcher import TelegramNewsletterFetcher
from src.pdf_extractor import PDFExtractor
from src.analyzer import LLMAnalyzer, DailyReport
from src.bot import TelegramBot


async def main():
    """Run the complete newsletter intelligence pipeline."""
    print("=" * 60)
    print("📰 TELEGRAM NEWSLETTER INTELLIGENCE BOT")
    print("=" * 60)
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    print(f"Target channel: {settings.target_channel}")
    print(f"Days back: {settings.days_back}")
    print()

    # Initialize components
    fetcher = TelegramNewsletterFetcher()
    extractor = PDFExtractor()
    analyzer = LLMAnalyzer()
    bot = TelegramBot()

    try:
        # 1. Connect to Telegram and fetch newsletters
        print("🔌 Connecting to Telegram...")
        await fetcher.start()

        print(f"📥 Fetching newsletters from last {settings.days_back} day(s)...")
        newsletters = await fetcher.fetch_recent_newsletters()
        print(f"Found {len(newsletters)} newsletter(s) with PDF attachments")

        if not newsletters:
            print("No newsletters found. Exiting.")
            await fetcher.stop()
            return

        # 2. Extract text from PDFs
        print("\n📄 Extracting text from PDFs...")
        pdf_paths = [n.pdf_path for n in newsletters]
        extracted_contents = extractor.extract_multiple(pdf_paths)
        print(f"Successfully extracted {len(extracted_contents)} PDF(s)")

        # 3. Analyze each newsletter with LLM
        print("\n🤖 Analyzing newsletters with LLM...")
        analyses = []
        for i, (newsletter, content) in enumerate(zip(newsletters, extracted_contents)):
            print(f"  Analyzing {i+1}/{len(extracted_contents)}: {newsletter.pdf_filename}")
            date_str = newsletter.date.strftime("%Y-%m-%d")
            analysis = analyzer.analyze_newsletter(
                source_name=newsletter.sender or newsletter.pdf_filename,
                date=date_str,
                content=content.full_text,
                tables=content.tables
            )
            analyses.append(analysis)

        # 4. Synthesize daily report
        print("\n📊 Synthesizing daily report...")
        report_date = datetime.now(timezone.utc).date().isoformat()
        daily_report = analyzer.synthesize_daily_report(analyses, report_date)

        # 5. Send report via Telegram Bot
        print("\n📤 Sending report via Telegram Bot...")
        success = bot.send_report(daily_report)

        if success:
            print("✅ Report delivered successfully!")
        else:
            print("❌ Failed to deliver report")

        # Save report locally for backup
        report_path = Path("reports") / f"report_{report_date}.json"
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, "w") as f:
            f.write(daily_report.model_dump_json(indent=2))
        print(f"💾 Report saved to {report_path}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await fetcher.stop()
        print("\n🔌 Disconnected from Telegram")

    print(f"\n✅ Completed at: {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())