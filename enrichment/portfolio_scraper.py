"""
Portfolio Intelligence Scraper — extracts portfolio companies from VC fund websites.

Uses the same batched Playwright approach as deep_crawl.py.
Visits /portfolio, /companies, /investments pages and extracts company cards.
"""

import asyncio
import logging
import random
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse, urljoin

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup, Tag

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


# ── Data Model ───────────────────────────────────

@dataclass
class PortfolioCompanyData:
    """A single portfolio company extracted from a fund website."""
    fund_name: str
    fund_url: str = ""
    company_name: str = ""
    sector: str = ""
    stage: str = ""
    url: str = ""
    year: Optional[int] = None
    scraped_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ── Portfolio Page Keywords ──────────────────────

PORTFOLIO_PATHS = [
    "/portfolio",
    "/companies",
    "/investments",
    "/portfolio-companies",
    "/our-portfolio",
    "/our-companies",
    "/our-investments",
    "/portfolio/companies",
    "/startups",
    "/founders",
]

PORTFOLIO_LINK_KEYWORDS = [
    "portfolio", "companies", "investments", "our companies",
    "our portfolio", "startups", "founders",
]

# ── Stage Detection ──────────────────────────────

STAGE_KEYWORDS = {
    "pre-seed": "Pre-Seed",
    "preseed": "Pre-Seed",
    "seed": "Seed",
    "series a": "Series A",
    "series b": "Series B",
    "series c": "Series C",
    "series d": "Series D",
    "series e": "Series E",
    "growth": "Growth",
    "late stage": "Late Stage",
    "late-stage": "Late Stage",
    "early stage": "Early Stage",
    "early-stage": "Early Stage",
    "ipo": "IPO",
    "public": "Public",
    "acquired": "Acquired",
    "exited": "Exited",
}


# ── Extraction Helpers ───────────────────────────

def _extract_year(text: str) -> Optional[int]:
    """Extract a plausible investment year from text."""
    matches = re.findall(r'\b(20[0-2]\d)\b', text)
    if matches:
        return int(matches[-1])
    return None


def _detect_stage(text: str) -> str:
    """Detect funding stage from text."""
    lower = text.lower()
    for keyword, label in STAGE_KEYWORDS.items():
        if keyword in lower:
            return label
    return ""


def _clean_company_name(name: str) -> str:
    """Clean extracted company name text."""
    name = re.sub(r'\s+', ' ', name).strip()
    # Remove trailing punctuation
    name = name.rstrip('.,;:!?')
    return name


def _looks_like_company_name(text: str) -> bool:
    """Heuristic check: does this text look like a company name?"""
    if not text or len(text) < 2 or len(text) > 80:
        return False
    if text.lower() in {
        "portfolio", "companies", "investments", "our portfolio",
        "back to top", "learn more", "read more", "view all",
        "see all", "load more", "contact us", "about us",
        "privacy policy", "terms of service", "cookie policy",
        "home", "blog", "news", "team", "careers",
    }:
        return False
    # Reject if it's mostly numbers
    if sum(c.isdigit() for c in text) > len(text) / 2:
        return False
    # Reject very long sentences
    if len(text.split()) > 10:
        return False
    return True


def _extract_company_url(card: Tag, base_url: str) -> str:
    """Extract the company's external URL from a portfolio card."""
    # Look for links in the card
    for a in card.find_all("a", href=True):
        href = a["href"]
        # Skip internal navigation links
        if href.startswith("#") or href.startswith("javascript:"):
            continue
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        # Prefer external links (to the company's own site)
        if parsed.netloc and parsed.netloc != urlparse(base_url).netloc:
            return full_url
    # Fall back to internal portfolio detail page link
    for a in card.find_all("a", href=True):
        href = a["href"]
        if href.startswith("#") or href.startswith("javascript:"):
            continue
        return urljoin(base_url, href)
    return ""


def _extract_sector_from_card(card: Tag) -> str:
    """Try to extract a sector/category label from the card."""
    # Look for common class names indicating sector/category
    for cls_pattern in ["sector", "category", "tag", "industry", "vertical", "focus"]:
        for el in card.find_all(True, class_=re.compile(cls_pattern, re.I)):
            text = el.get_text(strip=True)
            if text and len(text) < 60 and not _looks_like_company_name(text):
                return text
    # Look for small/span/em elements that might hold sector info
    for tag_name in ["span", "small", "em", "p"]:
        for el in card.find_all(tag_name):
            text = el.get_text(strip=True)
            if not text or len(text) > 60 or len(text) < 3:
                continue
            lower = text.lower()
            sector_hints = [
                "fintech", "health", "bio", "ai", "saas", "crypto", "web3",
                "climate", "edtech", "enterprise", "consumer", "hardware",
                "marketplace", "security", "cyber", "data", "analytics",
                "robotics", "deep tech", "deeptech", "gaming", "media",
                "food", "agri", "logistics", "proptech", "insurtech",
                "legaltech", "govtech", "cleantech", "mobility",
                "infrastructure", "developer", "devtools",
            ]
            if any(hint in lower for hint in sector_hints):
                return text
    return ""


def extract_portfolio_companies(
    soup: BeautifulSoup, page_url: str, fund_name: str, fund_url: str
) -> List[PortfolioCompanyData]:
    """
    Extract portfolio companies from a page using multiple strategies.
    Returns a list of PortfolioCompanyData objects.
    """
    companies = []
    seen_names = set()

    def _add(name: str, sector: str = "", stage: str = "", url: str = "", year: Optional[int] = None):
        clean = _clean_company_name(name)
        if not clean or clean.lower() in seen_names:
            return
        if not _looks_like_company_name(clean):
            return
        seen_names.add(clean.lower())
        companies.append(PortfolioCompanyData(
            fund_name=fund_name,
            fund_url=fund_url,
            company_name=clean,
            sector=sector,
            stage=stage,
            url=url,
            year=year,
            scraped_at=datetime.now().isoformat(),
        ))

    page_text = soup.get_text(separator=" ")

    # Strategy 1: Look for structured portfolio cards (div/li/article with heading or strong name)
    for container_tag in ["div", "li", "article", "a"]:
        for card in soup.find_all(container_tag):
            # Skip huge containers (page wrappers)
            card_text = card.get_text(separator=" ", strip=True)
            if len(card_text) > 1000 or len(card_text) < 3:
                continue

            # Find a name via heading tags
            name_el = card.find(["h2", "h3", "h4", "h5", "strong"])
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not _looks_like_company_name(name):
                continue

            sector = _extract_sector_from_card(card)
            stage = _detect_stage(card_text)
            url = _extract_company_url(card, page_url)
            year = _extract_year(card_text)

            _add(name, sector=sector, stage=stage, url=url, year=year)

    # Strategy 2: Grid of logos with alt text / titles (common on portfolio pages)
    if len(companies) < 5:
        for img in soup.find_all("img"):
            alt = img.get("alt", "").strip()
            title = img.get("title", "").strip()
            name = alt or title
            if not name:
                continue
            # Filter out generic images
            lower = name.lower()
            if any(x in lower for x in [
                "logo", "icon", "arrow", "background", "hero",
                "banner", "placeholder", "default", "avatar",
                "close", "menu", "search", "social",
            ]):
                # "logo" alone is noise, but "CompanyName logo" is valid
                if lower == "logo" or lower.endswith(" logo"):
                    name = name.rsplit(" ", 1)[0] if " " in name else ""
                elif "logo" in lower:
                    name = re.sub(r'\s*logo\s*', '', name, flags=re.I).strip()
                else:
                    continue

            if not _looks_like_company_name(name):
                continue

            # Try to find a link wrapping the image
            url = ""
            parent = img.parent
            if parent and parent.name == "a" and parent.get("href"):
                url = urljoin(page_url, parent["href"])

            _add(name, url=url)

    # Strategy 3: Simple list of links (some portfolio pages are just link lists)
    if len(companies) < 5:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(page_url, href)
            parsed = urlparse(full_url)
            # Only external links
            if parsed.netloc == urlparse(page_url).netloc:
                continue
            text = a.get_text(strip=True)
            if text and _looks_like_company_name(text):
                _add(text, url=full_url)

    return companies


# ── Portfolio Scraper Class ──────────────────────

class PortfolioScraper:
    """
    Scrapes portfolio pages from VC fund websites.
    Follows the same batched Playwright approach as DeepCrawler.
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        headless: bool = True,
    ):
        self.max_concurrent = max_concurrent
        self.headless = headless
        self.all_companies: List[PortfolioCompanyData] = []

    async def _find_portfolio_pages(self, page: Page, base_url: str) -> List[str]:
        """Scan homepage for links to portfolio pages."""
        portfolio_urls = set()
        try:
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(base_url, href)
                if urlparse(full_url).netloc != urlparse(base_url).netloc:
                    continue
                path = urlparse(full_url).path.lower().strip("/")
                if any(kw in path for kw in ["portfolio", "companies", "investments", "startups"]):
                    portfolio_urls.add(full_url)

                # Also check link text
                text = a.get_text(strip=True).lower()
                if any(kw in text for kw in PORTFOLIO_LINK_KEYWORDS):
                    portfolio_urls.add(full_url)

        except Exception as e:
            logger.error(f"  Error scanning {base_url}: {e}")

        return list(portfolio_urls)

    async def _scrape_portfolio_page(
        self, page: Page, url: str, fund_name: str, fund_url: str
    ) -> List[PortfolioCompanyData]:
        """Extract portfolio companies from a single page, handling pagination."""
        all_companies = []

        try:
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            companies = extract_portfolio_companies(soup, url, fund_name, fund_url)
            all_companies.extend(companies)

            # Handle "Load More" / "Show More" pagination
            for _ in range(5):
                clicked = False
                for btn_text in ["Load More", "Show More", "View All", "See All", "Show all", "Load more"]:
                    try:
                        btn = page.get_by_role("button", name=btn_text)
                        if await btn.count() > 0 and await btn.first.is_visible():
                            await btn.first.click()
                            clicked = True
                            await asyncio.sleep(2.0)
                            html = await page.content()
                            soup = BeautifulSoup(html, "html.parser")
                            extra = extract_portfolio_companies(soup, url, fund_name, fund_url)
                            all_companies.extend(extra)
                            break
                    except Exception:
                        continue
                if not clicked:
                    # Try link/anchor text
                    for btn_text in ["Load More", "Show More", "View All", "See All"]:
                        try:
                            link = page.get_by_text(btn_text, exact=False)
                            if await link.count() > 0 and await link.first.is_visible():
                                await link.first.click()
                                clicked = True
                                await asyncio.sleep(2.0)
                                html = await page.content()
                                soup = BeautifulSoup(html, "html.parser")
                                extra = extract_portfolio_companies(soup, url, fund_name, fund_url)
                                all_companies.extend(extra)
                                break
                        except Exception:
                            continue
                if not clicked:
                    break

            # Handle infinite scroll
            prev_count = len(all_companies)
            for _ in range(5):
                await page.mouse.wheel(0, 3000)
                await asyncio.sleep(1.5)
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                extra = extract_portfolio_companies(soup, url, fund_name, fund_url)
                all_companies.extend(extra)
                if len(all_companies) == prev_count:
                    break
                prev_count = len(all_companies)

        except Exception as e:
            logger.error(f"  Extraction error on {url}: {e}")

        # Deduplicate by company name
        seen = set()
        deduped = []
        for c in all_companies:
            key = c.company_name.lower().strip()
            if key not in seen:
                seen.add(key)
                deduped.append(c)

        return deduped

    async def _scrape_fund(self, browser: Browser, fund_url: str) -> List[PortfolioCompanyData]:
        """Scrape portfolio companies from a single fund website with a hard timeout."""
        fund_name = urlparse(fund_url).netloc.replace("www.", "").split(".")[0].title()
        companies = []

        async def _do_scrape():
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"
            )
            page = await ctx.new_page()

            logger.info(f"  [portfolio] Visiting {fund_url}")
            try:
                await page.goto(fund_url, wait_until="domcontentloaded", timeout=15000)
            except Exception:
                logger.warning(f"  [portfolio] Timeout on {fund_url}, continuing...")
                await ctx.close()
                return []

            await asyncio.sleep(random.uniform(1.0, 2.5))

            # Find portfolio pages from homepage links
            portfolio_urls = await self._find_portfolio_pages(page, fund_url)

            # Also try well-known paths
            for path in PORTFOLIO_PATHS:
                candidate = urljoin(fund_url, path)
                if candidate not in portfolio_urls:
                    portfolio_urls.append(candidate)

            logger.info(f"  [portfolio] Found {len(portfolio_urls)} potential portfolio pages")

            found = []
            for purl in portfolio_urls[:6]:
                try:
                    await page.goto(purl, wait_until="networkidle", timeout=15000)
                    await asyncio.sleep(1.0)

                    title = await page.title()
                    if "404" in title.lower() or "not found" in title.lower():
                        continue

                    page_companies = await self._scrape_portfolio_page(
                        page, purl, fund_name, fund_url
                    )
                    found.extend(page_companies)

                    if page_companies:
                        logger.info(
                            f"  [portfolio] Extracted {len(page_companies)} companies from {purl}"
                        )
                        # If we got a good set, no need to try more pages
                        if len(page_companies) >= 10:
                            break

                except Exception as e:
                    logger.warning(f"  [portfolio] Failed on {purl}: {e}")
                    continue

            # Deduplicate across all pages
            seen = set()
            deduped = []
            for c in found:
                key = c.company_name.lower().strip()
                if key not in seen:
                    seen.add(key)
                    deduped.append(c)

            await ctx.close()
            return deduped

        try:
            companies = await asyncio.wait_for(_do_scrape(), timeout=60.0)
        except asyncio.TimeoutError:
            logger.warning(f"  [portfolio] Hard timeout (60s) for {fund_url}")
        except Exception as e:
            logger.error(f"  [portfolio] Failed to scrape {fund_url}: {e}")

        return companies

    async def scrape_funds(self, fund_urls: List[str]) -> List[PortfolioCompanyData]:
        """Scrape portfolio companies from a list of fund URLs in batches."""
        logger.info(f"""
========================================================
  PORTFOLIO SCRAPER
  Extracting portfolio companies from fund websites
========================================================

  Target funds: {len(fund_urls)}
  Headless: {'YES' if self.headless else 'NO'}
""")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)

            batch_size = self.max_concurrent
            total = len(fund_urls)
            for batch_start in range(0, total, batch_size):
                batch = fund_urls[batch_start:batch_start + batch_size]
                batch_end = min(batch_start + batch_size, total)
                logger.info(
                    f"  [portfolio] Batch {batch_start // batch_size + 1}: "
                    f"funds {batch_start + 1}-{batch_end}/{total}"
                )

                tasks = [self._scrape_fund(browser, url) for url in batch]
                try:
                    results = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=batch_size * 65.0,
                    )
                    for result in results:
                        if isinstance(result, list):
                            self.all_companies.extend(result)
                except asyncio.TimeoutError:
                    logger.warning(f"  [portfolio] Batch timeout, moving on")

                logger.info(f"  [portfolio] Running total: {len(self.all_companies)} companies")

            await browser.close()

        # Final dedup
        seen = set()
        deduped = []
        for c in self.all_companies:
            key = (c.fund_name.lower(), c.company_name.lower())
            if key not in seen:
                seen.add(key)
                deduped.append(c)
        self.all_companies = deduped

        logger.info(f"""
========================================================
  PORTFOLIO SCRAPE SUMMARY
  Total companies: {len(self.all_companies)}
  Funds with results: {len(set(c.fund_name for c in self.all_companies))}
========================================================
""")

        return self.all_companies
