"""Telegram Bot for delivering daily reports."""
import asyncio
import json
from datetime import datetime
from typing import Optional
import requests
from dataclasses import asdict

from src.config import settings
from src.analyzer import DailyReport, NewsletterAnalysis


class TelegramBot:
    """Sends formatted daily reports via Telegram Bot API."""

    def __init__(self):
        self.bot_token = settings.bot_token
        self.chat_id = settings.report_chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def _send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message via Bot API."""
        try:
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True
                },
                timeout=30
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

    def _split_long_message(self, text: str, max_length: int = 4000) -> list:
        """Split long message into chunks."""
        if len(text) <= max_length:
            return [text]
        chunks = []
        for i in range(0, len(text), max_length):
            chunks.append(text[i:i + max_length])
        return chunks

    def format_newsletter_analysis(self, analysis: NewsletterAnalysis) -> str:
        """Format single newsletter analysis for Telegram."""
        lines = [
            f"<b>📰 {analysis.source_name}</b>",
            f"<b>Sentiment:</b> {analysis.sentiment.upper()}",
            "",
            "<b>📋 Executive Summary:</b>",
            analysis.executive_summary,
            "",
            "<b>🎯 Key Headlines:</b>"
        ]
        for i, headline in enumerate(analysis.key_headlines, 1):
            lines.append(f"{i}. {headline}")

        if analysis.sectors_covered:
            lines.append("")
            lines.append(f"<b>🏢 Sectors:</b> {', '.join(analysis.sectors_covered)}")

        if analysis.key_tickers:
            lines.append("")
            lines.append(f"<b>📊 Key Tickers:</b> {', '.join(analysis.key_tickers)}")

        if analysis.policy_macro_points:
            lines.append("")
            lines.append("<b>🏛 Policy/Macro:</b>")
            for point in analysis.policy_macro_points[:3]:
                lines.append(f"• {point}")

        if analysis.market_moving_events:
            lines.append("")
            lines.append("<b>📈 Market-Moving Events:</b>")
            for event in analysis.market_moving_events[:3]:
                lines.append(f"• {event}")

        if analysis.actionable_insights:
            lines.append("")
            lines.append("<b>💡 Actionable Insights:</b>")
            for insight in analysis.actionable_insights:
                lines.append(f"• {insight}")

        return "\n".join(lines)

    def format_daily_report(self, report: DailyReport) -> list:
        """Format complete daily report as list of messages (split if needed)."""
        date_str = datetime.fromisoformat(report.date).strftime("%d %b %Y") if "T" in report.date else report.date

        header = [
            f"<b>📅 Daily Financial Newsletter Digest — {date_str}</b>",
            f"<b>Overall Market Sentiment:</b> {report.overall_sentiment.upper()}",
            f"<b>Sources Analyzed:</b> {len(report.newsletters)}",
            ""
        ]

        if report.top_themes:
            header.append("<b>🔥 Top Themes Today:</b>")
            for theme in report.top_themes:
                header.append(f"• {theme}")
            header.append("")

        if report.watchlist:
            header.append(f"<b>👀 Watchlist:</b> {', '.join(report.watchlist[:10])}")
            header.append("")

        messages = ["\n".join(header)]

        # Each newsletter as separate message
        for analysis in report.newsletters:
            msg = self.format_newsletter_analysis(analysis)
            messages.append(msg)

        # Sector breakdown
        if report.sector_breakdown:
            sector_msg = ["<b>📂 Sector Breakdown:</b>"]
            for sector, points in report.sector_breakdown.items():
                sector_msg.append(f"\n<b>{sector}:</b>")
                for point in points[:3]:
                    sector_msg.append(f"• {point}")
            messages.append("\n".join(sector_msg))

        # Split any message that's too long
        final_messages = []
        for msg in messages:
            final_messages.extend(self._split_long_message(msg))

        return final_messages

    def send_report(self, report: DailyReport) -> bool:
        """Send complete daily report."""
        messages = self.format_daily_report(report)
        success = True
        for i, msg in enumerate(messages):
            if not self._send_message(msg):
                success = False
            if i < len(messages) - 1:
                asyncio.sleep(0.5)  # Rate limit
        return success

    def send_test_message(self) -> bool:
        """Send a test message to verify bot works."""
        return self._send_message(
            "✅ <b>Newsletter Bot Test</b>\n\nBot is connected and ready to deliver daily reports!",
            parse_mode="HTML"
        )