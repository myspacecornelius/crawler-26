"""
Base Offer Source Adapter

Adapted from crawler-26's adapters/base.py. Same pattern:
config-driven pagination, card extraction, stealth integration.
Different data model — returns raw offer dicts instead of InvestorLead objects.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from playwright.async_api import Page
from bs4 import BeautifulSoup


class BaseOfferSourceAdapter(ABC):
    """
    Abstract base for offer source scrapers.
    Subclasses implement parse_offer_card() with source-specific logic.
    """

    def __init__(self, source_config: dict, stealth_module=None):
        self.config = source_config
        self.url = source_config["url"]
        self.selectors = source_config.get("selectors", {})
        self.pagination = source_config.get("pagination", {})
        self.stealth = stealth_module
        self.offers: List[dict] = []

    @property
    def name(self) -> str:
        return self.config.get("name", self.__class__.__name__)

    async def run(self, page: Page) -> List[dict]:
        """Full scraping pipeline for this source."""
        await page.goto(self.url, timeout=60000)
        if self.stealth:
            await self.stealth.human_wait(page)
        else:
            await page.wait_for_timeout(3000)

        await self._extract_from_page(page)
        return self.offers

    async def _extract_from_page(self, page: Page):
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        card_selector = self.selectors.get("card", "div")
        cards = soup.select(card_selector)

        for card in cards:
            try:
                offer = self.parse_offer_card(card)
                if offer and offer.get("title"):
                    offer["source_url"] = self.url
                    offer["fetched_at"] = datetime.now().isoformat()
                    # Dedup within adapter
                    if not any(o.get("title") == offer["title"] for o in self.offers):
                        self.offers.append(offer)
            except Exception:
                continue

    @abstractmethod
    def parse_offer_card(self, card) -> Optional[dict]:
        """
        Parse a single offer card from HTML.
        Returns a dict with keys: title, description, vendor_domain,
        reward_value, cta_url, category, etc.
        """
        pass

    # ── Utility helpers for subclasses ──

    def _safe_text(self, card, selector: str, default: str = "") -> str:
        el = card.select_one(selector) if selector else None
        return el.get_text(strip=True) if el else default

    def _safe_attr(self, card, selector: str, attr: str, default: str = "") -> str:
        el = card.select_one(selector) if selector else None
        return el.get(attr, default) if el else default
