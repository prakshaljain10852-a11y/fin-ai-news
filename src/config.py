"""Configuration management using python-dotenv."""
import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Settings:
    # Telegram User Account
    telegram_api_id: int
    telegram_api_hash: str
    telegram_phone: str
    target_channel: str

    # Telegram Bot (for delivery)
    bot_token: str
    report_chat_id: int

    # LLM Configuration
    llm_base_url: str
    llm_api_key: str
    llm_model: str

    # Processing
    max_messages_per_run: int
    days_back: int
    min_pdf_size_kb: int

    # Session file path
    session_name: str


def load_settings() -> Settings:
    """Load settings from environment variables."""
    # Load .env file if exists
    env_path = Path(".env")
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    return Settings(
        telegram_api_id=int(os.getenv("TELEGRAM_API_ID", "0")),
        telegram_api_hash=os.getenv("TELEGRAM_API_HASH", ""),
        telegram_phone=os.getenv("TELEGRAM_PHONE", ""),
        target_channel=os.getenv("TARGET_CHANNEL", ""),
        bot_token=os.getenv("BOT_TOKEN", ""),
        report_chat_id=int(os.getenv("REPORT_CHAT_ID", "0")),
        llm_base_url=os.getenv("LLM_BASE_URL", "http://host.docker.internal:8082/v1"),
        llm_api_key=os.getenv("LLM_API_KEY", "dummy"),
        llm_model=os.getenv("LLM_MODEL", "open_router/nvidia/nemotron-3-super-120b-a12b"),
        max_messages_per_run=int(os.getenv("MAX_MESSAGES_PER_RUN", "50")),
        days_back=int(os.getenv("DAYS_BACK", "1")),
        min_pdf_size_kb=int(os.getenv("MIN_PDF_SIZE_KB", "10")),
        session_name=os.getenv("SESSION_NAME", "newsletter_session"),
    )


settings = load_settings()