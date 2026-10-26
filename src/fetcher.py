"""Telegram client for fetching messages and PDF attachments from private channel."""
import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from telethon import TelegramClient
from telethon.tl.types import Message, DocumentAttributeFilename

from src.config import settings


@dataclass
class NewsletterMessage:
    """Represents a newsletter message with PDF attachment."""
    id: int
    date: datetime
    sender: str
    text: str
    pdf_path: Optional[str] = None
    pdf_filename: Optional[str] = None


class TelegramNewsletterFetcher:
    """Fetches newsletter PDFs from a private Telegram channel."""

    def __init__(self):
        self.client = TelegramClient(
            settings.session_name,
            settings.telegram_api_id,
            settings.telegram_api_hash
        )
        self.download_dir = Path("downloads")
        self.download_dir.mkdir(exist_ok=True)

    async def start(self):
        """Start the client and authenticate."""
        await self.client.start(phone=settings.telegram_phone)
        print("Telegram client connected")

    async def stop(self):
        """Disconnect the client."""
        await self.client.disconnect()

    def _is_pdf(self, message: Message) -> bool:
        """Check if message has a PDF attachment."""
        if not message.document:
            return False
        if not message.file:
            return False
        # Check mime type
        if message.file.mime_type == "application/pdf":
            return True
        # Check filename extension
        for attr in message.document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                if attr.file_name.lower().endswith(".pdf"):
                    return True
        return False

    def _get_pdf_filename(self, message: Message) -> Optional[str]:
        """Extract PDF filename from message."""
        if not message.document:
            return None
        for attr in message.document.attributes:
            if isinstance(attr, DocumentAttributeFilename):
                return attr.file_name
        return f"newsletter_{message.id}.pdf"

    async def fetch_recent_newsletters(self) -> List[NewsletterMessage]:
        """Fetch recent messages with PDF attachments from target channel."""
        entity = await self.client.get_entity(settings.target_channel)

        # Calculate cutoff date
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.days_back)

        newsletters = []
        async for message in self.client.iter_messages(
            entity,
            limit=settings.max_messages_per_run,
            offset_date=cutoff,
            reverse=True  # Oldest first
        ):
            if not isinstance(message, Message):
                continue
            if not self._is_pdf(message):
                continue

            # Check file size
            if message.file and message.file.size:
                size_kb = message.file.size / 1024
                if size_kb < settings.min_pdf_size_kb:
                    print(f"Skipping small PDF ({size_kb:.1f} KB): {message.id}")
                    continue

            filename = self._get_pdf_filename(message)
            pdf_path = self.download_dir / f"{message.id}_{filename}"

            # Download PDF
            print(f"Downloading PDF: {filename} (message {message.id})")
            await self.client.download_media(message, file=str(pdf_path))

            sender_name = "Unknown"
            if message.sender:
                if hasattr(message.sender, 'title'):
                    sender_name = message.sender.title
                elif hasattr(message.sender, 'first_name'):
                    sender_name = message.sender.first_name
                    if message.sender.last_name:
                        sender_name += f" {message.sender.last_name}"

            newsletters.append(NewsletterMessage(
                id=message.id,
                date=message.date,
                sender=sender_name,
                text=message.text or "",
                pdf_path=str(pdf_path),
                pdf_filename=filename
            ))

        return newsletters