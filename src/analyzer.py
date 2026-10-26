"""LLM-based newsletter analysis using FCC proxy (Nemotron)."""
import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import requests
from pydantic import BaseModel

from src.config import settings


class NewsletterAnalysis(BaseModel):
    """Structured analysis output for a single newsletter."""
    source_name: str
    executive_summary: str  # 3-5 bullet points
    key_headlines: List[str]  # Top 5-7 headlines
    sectors_covered: List[str]  # e.g., ["Banking", "Markets", "Policy", "Corporate"]
    key_tickers: List[str]  # Stock tickers, indices, commodities mentioned
    policy_macro_points: List[str]  # RBI, govt policy, macro data
    market_moving_events: List[str]  # Earnings, M&A, IPOs, regulatory
    sentiment: str  # "bullish", "bearish", "neutral", "mixed"
    actionable_insights: List[str]  # 2-3 actionable takeaways


class DailyReport(BaseModel):
    """Complete daily report across all newsletters."""
    date: str
    newsletters: List[NewsletterAnalysis]
    sector_breakdown: Dict[str, List[str]]  # sector -> list of key points
    top_themes: List[str]  # 3-5 cross-cutting themes
    watchlist: List[str]  # Tickers/commodities to watch
    overall_sentiment: str


SYSTEM_PROMPT = """You are a financial analyst specializing in Indian markets. Analyze financial newsletter content from sources like Mint, Financial Express, Economic Times, Business Standard, The Economist, etc.

Extract structured insights for a finance student who needs to efficiently cover daily financial news.

Return ONLY valid JSON matching the provided schema. No extra commentary."""


USER_PROMPT_TEMPLATE = """Analyze this financial newsletter content and extract structured insights.

SOURCE: {source_name}
DATE: {date}
CONTENT:
{content}

TABLES (if any):
{tables}

Provide analysis as JSON with these fields:
- source_name: string
- executive_summary: string (3-5 concise bullet points)
- key_headlines: string[] (top 5-7 headlines)
- sectors_covered: string[] (e.g., Banking, Markets, Policy, Corporate, Macro, Commodities, Tech, Auto)
- key_tickers: string[] (stock symbols like RELIANCE, NIFTY, BANKNIFTY, GOLD, USDINR, etc.)
- policy_macro_points: string[] (RBI decisions, govt policy, GDP, inflation, fiscal, etc.)
- market_moving_events: string[] (earnings, M&A, IPOs, regulatory changes, block deals)
- sentiment: string (bullish/bearish/neutral/mixed)
- actionable_insights: string[] (2-3 specific takeaways for a finance student)"""


class LLMAnalyzer:
    """Analyzes newsletter content using LLM via FCC proxy."""

    def __init__(self):
        self.base_url = settings.llm_base_url.rstrip("/")
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _call_llm(self, system: str, user: str, response_format: dict = None) -> str:
        """Call LLM API."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        if response_format:
            payload["response_format"] = response_format

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def analyze_newsletter(self, source_name: str, date: str, content: str, tables: List) -> NewsletterAnalysis:
        """Analyze a single newsletter."""
        tables_text = json.dumps(tables, indent=2) if tables else "None"
        user_prompt = USER_PROMPT_TEMPLATE.format(
            source_name=source_name,
            date=date,
            content=content[:15000],  # Truncate if too long
            tables=tables_text
        )

        # Use structured output
        response_format = {"type": "json_object"}
        result_text = self._call_llm(SYSTEM_PROMPT, user_prompt, response_format)

        try:
            result = json.loads(result_text)
            return NewsletterAnalysis(**result)
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {result_text[:500]}")
            # Return minimal fallback
            return NewsletterAnalysis(
                source_name=source_name,
                executive_summary="Analysis failed",
                key_headlines=[],
                sectors_covered=[],
                key_tickers=[],
                policy_macro_points=[],
                market_moving_events=[],
                sentiment="neutral",
                actionable_insights=[]
            )

    def synthesize_daily_report(self, analyses: List[NewsletterAnalysis], date: str) -> DailyReport:
        """Synthesize cross-newsletter daily report."""
        # Collect all sectors and points
        sector_points = {}
        all_tickers = []
        all_themes = []

        for a in analyses:
            for sector in a.sectors_covered:
                if sector not in sector_points:
                    sector_points[sector] = []
                sector_points[sector].extend(a.key_headlines[:3])  # Top headlines per sector
            all_tickers.extend(a.key_tickers)
            all_themes.extend(a.policy_macro_points)

        # Deduplicate
        for sector in sector_points:
            sector_points[sector] = list(dict.fromkeys(sector_points[sector]))[:5]
        watchlist = list(dict.fromkeys(all_tickers))[:15]
        top_themes = list(dict.fromkeys(all_themes))[:5]

        # Overall sentiment
        sentiments = [a.sentiment for a in analyses]
        if sentiments.count("bullish") > sentiments.count("bearish"):
            overall = "bullish"
        elif sentiments.count("bearish") > sentiments.count("bullish"):
            overall = "bearish"
        elif "mixed" in sentiments:
            overall = "mixed"
        else:
            overall = "neutral"

        return DailyReport(
            date=date,
            newsletters=analyses,
            sector_breakdown=sector_points,
            top_themes=top_themes,
            watchlist=watchlist,
            overall_sentiment=overall
        )