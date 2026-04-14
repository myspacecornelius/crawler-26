"""
Offer Crawler — visits pages and extracts demo incentive offers.

Adapted from crawler-26's deep_crawl.py. What's actually here:
- Concurrent browser sessions via Playwright
- Stealth integration (fingerprint rotation, human behavior)
- Offer-page detection via URL keywords and link text matching
- Delegation to page_extractor for HTML → offer data

Not yet ported from deep_crawl.py (add when needed):
- Sitemap/robots.txt scanning
- Checkpoint/recovery for interrupted crawls
"""

import asyncio
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin

from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup

from ingestion.crawl.page_extractor import extract_offers_from_page
from ingestion.stealth.fingerprint import FingerprintManager
from ingestion.stealth.behavior import HumanBehavior

logger = logging.getLogger(__name__)

# Keywords that indicate a page might list demo incentives
OFFER_PAGE_KEYWORDS = [
    "demo", "incentive", "gift-card", "reward", "trial",
    "get-started", "free-trial", "request-demo", "book-demo",
    "pricing", "offer", "promotion", "evaluation",
]


def is_offer_page_url(url: str) -> bool:
    """Check if a URL likely leads to an offer/demo page."""
    path = urlparse(url).path.lower().strip("/")
    return any(kw in path for kw in OFFER_PAGE_KEYWORDS)


class OfferCrawler:
    """Crawls websites to find and extract demo incentive offers."""

    def __init__(
        self,
        max_concurrent: int = 5,
        headless: bool = True,
        stale_days: int = 7,
    ):
        self.max_concurrent = max_concurrent
        self.headless = headless
        self.stale_days = stale_days
        self.fingerprint_mgr = FingerprintManager()
        self.behavior = HumanBehavior(speed_factor=0.8)
        self.all_offers: List[dict] = []

    async def crawl_sources(self, source_urls: List[str]) -> List[dict]:
        """Crawl a list of source URLs and extract offers."""
        if not source_urls:
            logger.info("No source URLs to crawl")
            return []

        logger.info(f"Crawling {len(source_urls)} sources (concurrency={self.max_concurrent})")

        sem = asyncio.Semaphore(self.max_concurrent)

        async def _crawl_one(url: str):
            async with sem:
                try:
                    offers = await self._crawl_site(url)
                    self.all_offers.extend(offers)
                except Exception as e:
                    logger.warning(f"Error crawling {url}: {e}")

        async with async_playwright() as p:
            tasks = [_crawl_one(url) for url in source_urls]
            await asyncio.gather(*tasks)

        logger.info(f"Crawl complete: {len(self.all_offers)} offers from {len(source_urls)} sources")
        return self.all_offers

    async def _crawl_site(self, base_url: str) -> List[dict]:
        """Crawl a single site for offers."""
        offers: List[dict] = []

        # Normalize URL
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"

        domain = urlparse(base_url).netloc.lower().replace("www.", "")
        logger.info(f"  🌐 Crawling {domain}")

        # Generate fingerprint
        fingerprint = self.fingerprint_mgr.generate()
        context_kwargs = self.fingerprint_mgr.get_context_kwargs(fingerprint)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(**context_kwargs)
            page = await context.new_page()
            await self.fingerprint_mgr.apply_js_overrides(page)

            try:
                # Visit homepage
                await page.goto(base_url, timeout=30000, wait_until="domcontentloaded")
                await self.behavior.human_wait(page, short=True)

                # Find offer-related pages
                offer_urls = await self._find_offer_pages(page, base_url)
                offer_urls = list(set(offer_urls))[:10]  # cap at 10 pages per site

                if not offer_urls:
                    # Try extracting from homepage itself
                    page_offers = await self._extract_from_page(page, base_url, domain)
                    offers.extend(page_offers)
                else:
                    for url in offer_urls:
                        try:
                            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
                            await self.behavior.human_wait(page, short=True)
                            page_offers = await self._extract_from_page(page, url, domain)
                            offers.extend(page_offers)
                        except Exception as e:
                            logger.debug(f"  Error on {url}: {e}")

            except Exception as e:
                logger.debug(f"  Failed to load {base_url}: {e}")
            finally:
                await browser.close()

        if offers:
            logger.info(f"  ✅ {domain}: {len(offers)} offers found")

        return offers

    async def _find_offer_pages(self, page: Page, base_url: str) -> List[str]:
        """Scan a page for links to offer/demo/pricing pages."""
        offer_urls = set()
        try:
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(base_url, href)
                if urlparse(full_url).netloc != urlparse(base_url).netloc:
                    continue
                if is_offer_page_url(full_url):
                    offer_urls.add(full_url)

                # Also check link text
                text = a.get_text(strip=True).lower()
                if any(kw in text for kw in ["demo", "trial", "pricing", "incentive", "reward", "gift card"]):
                    full_url = urljoin(base_url, href)
                    if urlparse(full_url).netloc == urlparse(base_url).netloc:
                        offer_urls.add(full_url)

        except Exception as e:
            logger.debug(f"Error scanning {base_url}: {e}")

        return list(offer_urls)

    async def _extract_from_page(self, page: Page, url: str, domain: str) -> List[dict]:
        """Extract offer data from a single page."""
        try:
            html = await page.content()
            return extract_offers_from_page(html, url, domain)
        except Exception as e:
            logger.debug(f"Extraction error on {url}: {e}")
            return []
