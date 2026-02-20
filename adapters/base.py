"""
CRAWL — Base Site Adapter
Abstract base class that all site-specific adapters extend.
Handles common operations: page loading, pagination, data extraction.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime

from playwright.async_api import Page
from bs4 import BeautifulSoup


# ──────────────────────────────────────────────────
#  Data Models
# ──────────────────────────────────────────────────

@dataclass
class InvestorLead:
    """A single investor lead extracted from a directory."""
    name: str
    email: str = "N/A"
    role: str = "N/A"
    fund: str = "N/A"
    focus_areas: list = field(default_factory=list)
    stage: str = "N/A"
    check_size: str = "N/A"
    location: str = "N/A"
    linkedin: str = "N/A"
    website: str = "N/A"
    source: str = ""
    scraped_at: str = ""
    lead_score: int = 0
    tier: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["focus_areas"] = ", ".join(self.focus_areas) if self.focus_areas else "N/A"
        return d


# ──────────────────────────────────────────────────
#  Base Adapter
# ──────────────────────────────────────────────────

class BaseSiteAdapter(ABC):
    """
    Abstract base for all site scrapers.
    Subclasses implement parse_cards() with site-specific logic.
    The base class handles pagination, retries, and data collection.
    """

    def __init__(self, site_config: dict, stealth_module=None):
        self.config = site_config
        self.url = site_config["url"]
        self.selectors = site_config.get("selectors", {})
        self.pagination = site_config.get("pagination", {})
        self.stealth = stealth_module
        self.leads: list[InvestorLead] = []

    @property
    def name(self) -> str:
        return self.config.get("adapter", self.__class__.__name__)

    async def run(self, page: Page) -> list[InvestorLead]:
        """
        Full scraping pipeline for this site:
        1. Navigate to target URL
        2. Apply stealth behaviors
        3. Handle pagination
        4. Extract leads from each page state
        """
        print(f"\n{'='*60}")
        print(f"  🕷️  CRAWLING: {self.name.upper()}")
        print(f"  📍  {self.url}")
        print(f"{'='*60}\n")

        await page.goto(self.url, timeout=60000)

        # Let page settle + apply human-like behavior
        if self.stealth:
            await self.stealth.human_wait(page)
            await self.stealth.random_mouse_movement(page)
        else:
            await page.wait_for_timeout(3000)

        # Handle pagination and extract across all pages
        await self._paginate_and_extract(page)

        print(f"\n  ✅  {self.name}: Extracted {len(self.leads)} leads\n")
        return self.leads

    async def _paginate_and_extract(self, page: Page):
        """Route to the correct pagination handler."""
        ptype = self.pagination.get("type", "none")

        if ptype == "infinite_scroll":
            await self._handle_infinite_scroll(page)
        elif ptype == "load_more_button":
            await self._handle_load_more(page)
        elif ptype == "numbered_pages":
            await self._handle_numbered_pages(page)
        else:
            # Single page, just extract
            await self._extract_from_page(page)

    async def _handle_infinite_scroll(self, page: Page):
        """Scroll down repeatedly to trigger lazy-loading content."""
        scroll_count = self.pagination.get("scroll_count", 10)
        scroll_delay = self.pagination.get("scroll_delay_ms", 1500)
        load_indicator = self.pagination.get("load_indicator", "")

        for i in range(scroll_count):
            print(f"  📜  Scrolling... ({i+1}/{scroll_count})")

            if self.stealth:
                await self.stealth.human_scroll(page)
            else:
                await page.mouse.wheel(0, 800)

            # Wait for loading indicator to appear and disappear
            if load_indicator:
                try:
                    await page.wait_for_selector(load_indicator, state="visible", timeout=2000)
                    await page.wait_for_selector(load_indicator, state="hidden", timeout=10000)
                except Exception:
                    pass

            await page.wait_for_timeout(scroll_delay)

        await self._extract_from_page(page)

    async def _handle_load_more(self, page: Page):
        """Click 'Load More' button until exhausted or max reached."""
        button = self.pagination.get("button_selector", "")
        max_clicks = self.pagination.get("max_clicks", 20)
        click_delay = self.pagination.get("click_delay_ms", 2000)

        for i in range(max_clicks):
            try:
                btn = page.locator(button)
                if await btn.count() == 0 or not await btn.is_visible():
                    print(f"  🏁  No more 'Load More' button found after {i} clicks")
                    break

                print(f"  🖱️  Clicking 'Load More'... ({i+1}/{max_clicks})")

                if self.stealth:
                    await self.stealth.human_click(page, button)
                else:
                    await btn.click()

                await page.wait_for_timeout(click_delay)

            except Exception:
                break

        await self._extract_from_page(page)

    async def _handle_numbered_pages(self, page: Page):
        """Navigate through numbered pagination pages."""
        next_button = self.pagination.get("next_button", "")
        max_pages = self.pagination.get("max_pages", 20)

        for i in range(max_pages):
            print(f"  📄  Page {i+1}/{max_pages}")
            await self._extract_from_page(page)

            try:
                btn = page.locator(next_button)
                if await btn.count() == 0 or not await btn.is_visible():
                    print(f"  🏁  No more pages after page {i+1}")
                    break

                if self.stealth:
                    await self.stealth.human_click(page, next_button)
                else:
                    await btn.click()

                await page.wait_for_load_state("networkidle", timeout=10000)

                if self.stealth:
                    await self.stealth.human_wait(page, short=True)
                else:
                    await page.wait_for_timeout(1500)

            except Exception:
                break

    async def _extract_from_page(self, page: Page):
        """Get page HTML, parse it with BeautifulSoup, and extract leads."""
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        card_selector = self.selectors.get("card", "div")
        cards = soup.select(card_selector)

        print(f"  🔍  Found {len(cards)} cards on current page state")

        new_leads = 0
        for card in cards:
            try:
                lead = self.parse_card(card)
                if lead and lead.name and lead.name != "N/A":
                    lead.source = self.url
                    lead.scraped_at = datetime.now().isoformat()
                    # Dedup by name within this adapter
                    if not any(existing.name == lead.name for existing in self.leads):
                        self.leads.append(lead)
                        new_leads += 1
            except Exception as e:
                continue

        print(f"  ➕  {new_leads} new unique leads extracted")

    @abstractmethod
    def parse_card(self, card) -> Optional[InvestorLead]:
        """
        Parse a single investor card from the page HTML.
        Must be implemented by each site adapter.

        Args:
            card: A BeautifulSoup Tag representing one investor card

        Returns:
            InvestorLead or None if card couldn't be parsed
        """
        pass

    # ── Utility helpers for subclasses ──

    def _safe_text(self, card, selector: str, default: str = "N/A") -> str:
        """Safely extract text from a CSS selector within a card."""
        el = card.select_one(selector) if selector else None
        return el.get_text(strip=True) if el else default

    def _safe_attr(self, card, selector: str, attr: str, default: str = "N/A") -> str:
        """Safely extract an attribute from a CSS selector within a card."""
        el = card.select_one(selector) if selector else None
        return el.get(attr, default) if el else default

    def _safe_list(self, card, selector: str) -> list:
        """Extract a list of text values from matching elements."""
        elements = card.select(selector) if selector else []
        return [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]

    def _extract_email(self, card) -> str:
        """
        Multi-strategy email extraction:
        1. Look for mailto: links
        2. Scan text for @ patterns
        """
        email_sel = self.selectors.get("email", "")

        # Strategy 1: mailto link
        if email_sel:
            tag = card.select_one(email_sel)
            if tag:
                href = tag.get("href", "")
                if href.startswith("mailto:"):
                    return href.replace("mailto:", "").split("?")[0].strip()

        # Strategy 2: scan for email-like text
        text = card.get_text()
        if "@" in text:
            import re
            matches = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
            if matches:
                return matches[0]

        return "N/A"
