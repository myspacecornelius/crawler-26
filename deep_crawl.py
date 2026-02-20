"""
CRAWL — Generic Website Deep Crawler
Crawls arbitrary VC fund websites to find team/about pages
and extract contact information (names, roles, emails, LinkedIn).
"""

import asyncio
import random
import re
import csv
import os
import logging
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ── Data Structures ──────────────────────────────

@dataclass
class Contact:
    name: str = ""
    role: str = ""
    email: str = ""
    linkedin: str = ""
    fund_name: str = ""
    fund_url: str = ""
    source_page: str = ""


# ── Team Page Keywords ────────────────────────────

TEAM_PAGE_KEYWORDS = [
    "team", "people", "about", "who-we-are", "our-team",
    "partners", "leadership", "staff", "investors", "bios",
    "professionals", "portfolio-team", "our-people", "meet-the-team"
]

# Words that indicate a person's role
ROLE_KEYWORDS = [
    "partner", "principal", "associate", "analyst", "founder",
    "managing", "director", "vice president", "vp", "ceo",
    "cto", "cfo", "coo", "general partner", "venture partner",
    "operating partner", "senior associate", "investment",
    "head of", "chief", "chairman", "advisory", "advisor",
    "eir", "entrepreneur in residence", "scout", "fellow"
]


# ── Extraction Helpers ───────────────────────────

def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text using regex."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    # Filter out common false positives
    filtered = []
    for e in emails:
        e_lower = e.lower()
        if any(x in e_lower for x in ['.png', '.jpg', '.svg', '.gif', '.css', '.js', 'example.com', 'email.com', 'domain.com']):
            continue
        filtered.append(e)
    return list(set(filtered))


def extract_linkedin_urls(soup: BeautifulSoup) -> List[str]:
    """Extract LinkedIn profile URLs from page."""
    urls = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "linkedin.com/in/" in href:
            urls.add(href.split("?")[0])  # Remove tracking params
    return list(urls)


def is_team_page_url(url: str) -> bool:
    """Check if a URL likely leads to a team/about page."""
    path = urlparse(url).path.lower().strip("/")
    return any(kw in path for kw in TEAM_PAGE_KEYWORDS)


def extract_name_role_pairs(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Extract (name, role) pairs from a team page using heuristics.
    Looks for common patterns: heading + paragraph, or structured divs.
    """
    pairs = []

    # Words that are definitely NOT person names
    BLOCKLIST = {
        "san francisco", "new york", "palo alto", "los angeles", "boston",
        "chicago", "austin", "seattle", "menlo park", "silicon valley",
        "mountain view", "tel aviv", "london", "berlin", "toronto",
        "helpful tips", "read more", "learn more", "contact us", "get started",
        "our portfolio", "our approach", "our story", "our mission",
        "our values", "our focus", "latest news", "press releases",
        "sign up", "log in", "about us", "who we are", "what we do",
        "how it works", "join us", "careers", "open positions",
        "portfolio companies", "recent investments", "featured",
        "view all", "see more", "load more", "subscribe", "follow us",
        "privacy policy", "terms of service", "cookie policy",
    }

    def looks_like_name(text: str) -> bool:
        """Check if text looks like a real person name."""
        words = text.split()
        if len(words) < 2 or len(words) > 5:
            return False
        if len(text) > 40 or len(text) < 4:
            return False
        if any(c.isdigit() for c in text):
            return False
        if text.lower() in BLOCKLIST:
            return False
        # Each word should be capitalized and alphabetic (allow hyphens, dots, apostrophes)
        for w in words:
            cleaned = w.replace("-", "").replace(".", "").replace("'", "")
            if not cleaned:
                return False
            if not cleaned[0].isupper():
                return False
            if not cleaned.isalpha():
                return False
        # Reject single-character first or last names
        if len(words[0]) < 2 or len(words[-1]) < 2:
            return False
        return True

    # Strategy 1: Look for structured cards with headings + nearby role text
    for container_tag in ["div", "li", "article"]:
        for container in soup.find_all(container_tag):
            # Skip huge containers (likely page wrappers, not individual cards)
            if len(container.get_text()) > 2000:
                continue

            heading = container.find(["h2", "h3", "h4", "h5"])
            if not heading:
                continue

            name_text = heading.get_text(strip=True)

            if not looks_like_name(name_text):
                continue

            # Look for role text nearby
            role_text = ""
            for sibling in [heading.find_next_sibling(), heading.find_next()]:
                if sibling and sibling.name in ["p", "span", "div", "small", "em"]:
                    candidate = sibling.get_text(strip=True)
                    if len(candidate) < 80 and any(kw in candidate.lower() for kw in ROLE_KEYWORDS):
                        role_text = candidate
                        break

            # Only accept if we found a role — otherwise it's probably not a team card
            if role_text:
                pairs.append({"name": name_text, "role": role_text})

    # Strategy 2: If strategy 1 found nothing, try names WITHOUT role requirement
    # but only if the page URL strongly suggests it's a team page
    if not pairs:
        for container_tag in ["div", "li", "article"]:
            for container in soup.find_all(container_tag):
                if len(container.get_text()) > 1500:
                    continue
                heading = container.find(["h2", "h3", "h4", "h5"])
                if not heading:
                    continue
                name_text = heading.get_text(strip=True)
                if not looks_like_name(name_text):
                    continue
                # Check for any nearby role-ish text (even without strict keyword match)
                role_text = ""
                for sibling in [heading.find_next_sibling(), heading.find_next()]:
                    if sibling and sibling.name in ["p", "span", "div", "small", "em"]:
                        candidate = sibling.get_text(strip=True)
                        if 3 < len(candidate) < 60:
                            role_text = candidate
                            break
                pairs.append({"name": name_text, "role": role_text})

    # Deduplicate by name
    seen_names = set()
    unique_pairs = []
    for p in pairs:
        if p["name"] not in seen_names:
            seen_names.add(p["name"])
            unique_pairs.append(p)

    return unique_pairs


# ── Deep Crawler Class ───────────────────────────

class DeepCrawler:
    """
    Crawls individual VC fund websites to extract team contacts.
    """

    def __init__(
        self,
        target_file: str = "data/target_funds.txt",
        output_file: str = "data/vc_contacts.csv",
        max_concurrent: int = 3,
        headless: bool = True
    ):
        self.target_file = target_file
        self.output_file = output_file
        self.max_concurrent = max_concurrent
        self.headless = headless
        self.all_contacts: List[Contact] = []

    def _load_targets(self) -> List[str]:
        """Load target URLs from file, skipping comments and empty lines."""
        targets = []
        with open(self.target_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    targets.append(line)
        return list(set(targets))  # Deduplicate

    async def _find_team_pages(self, page: Page, base_url: str) -> List[str]:
        """Scan homepage for links to team/about pages."""
        team_urls = set()

        try:
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(base_url, href)

                # Only follow internal links
                if urlparse(full_url).netloc != urlparse(base_url).netloc:
                    continue

                if is_team_page_url(full_url):
                    team_urls.add(full_url)

            # Also check link text for clues
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True).lower()
                if any(kw in text for kw in ["team", "people", "about us", "who we are", "our team"]):
                    full_url = urljoin(base_url, a["href"])
                    if urlparse(full_url).netloc == urlparse(base_url).netloc:
                        team_urls.add(full_url)
        except Exception as e:
            logger.error(f"  ❌ Error scanning {base_url}: {e}")

        return list(team_urls)

    async def _extract_from_page(self, page: Page, url: str, fund_name: str, fund_url: str) -> List[Contact]:
        """Extract contacts from a single page."""
        contacts = []

        try:
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            page_text = soup.get_text()

            # Extract data
            emails = extract_emails(page_text)
            linkedin_urls = extract_linkedin_urls(soup)
            name_roles = extract_name_role_pairs(soup)

            # Build contact objects
            for i, pair in enumerate(name_roles):
                contact = Contact(
                    name=pair["name"],
                    role=pair["role"],
                    fund_name=fund_name,
                    fund_url=fund_url,
                    source_page=url
                )

                # Try to match a LinkedIn URL (by name proximity in HTML)
                name_lower = pair["name"].lower().replace(" ", "")
                for li_url in linkedin_urls:
                    if name_lower[:6] in li_url.lower().replace("-", ""):
                        contact.linkedin = li_url
                        break

                contacts.append(contact)

            # If we found emails but no name-role pairs, still record them
            if emails and not name_roles:
                for email in emails:
                    contacts.append(Contact(
                        email=email,
                        fund_name=fund_name,
                        fund_url=fund_url,
                        source_page=url
                    ))

            # Distribute emails to contacts if we have both
            if emails and name_roles:
                # Generic fund email goes to first contact
                for contact in contacts:
                    if not contact.email and emails:
                        contact.email = emails.pop(0)

        except Exception as e:
            logger.error(f"  ❌ Extraction error on {url}: {e}")

        return contacts

    async def _crawl_fund(self, browser: Browser, fund_url: str) -> List[Contact]:
        """Crawl a single VC fund website."""
        fund_name = urlparse(fund_url).netloc.replace("www.", "").split(".")[0].title()
        contacts = []

        try:
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"
            )
            page = await ctx.new_page()

            # Navigate to homepage
            logger.info(f"  🌐 Visiting {fund_url}")
            try:
                await page.goto(fund_url, wait_until="domcontentloaded", timeout=15000)
            except Exception:
                logger.warning(f"  ⏳ Timeout on {fund_url}, continuing...")
                await ctx.close()
                return []

            await asyncio.sleep(random.uniform(1.0, 2.5))

            # Find team pages
            team_urls = await self._find_team_pages(page, fund_url)

            if not team_urls:
                # If no team page found, try common paths
                for path in ["/team", "/about", "/people", "/about-us", "/our-team"]:
                    team_urls.append(urljoin(fund_url, path))

            logger.info(f"  📄 Found {len(team_urls)} potential team pages")

            # Visit each team page (max 3 to be reasonable)
            for team_url in team_urls[:3]:
                try:
                    await page.goto(team_url, wait_until="domcontentloaded", timeout=10000)
                    await asyncio.sleep(random.uniform(0.5, 1.5))

                    # Check if page loaded (not 404)
                    title = await page.title()
                    if "404" in title.lower() or "not found" in title.lower():
                        continue

                    page_contacts = await self._extract_from_page(
                        page, team_url, fund_name, fund_url
                    )
                    contacts.extend(page_contacts)

                    if page_contacts:
                        logger.info(f"  ✅ Extracted {len(page_contacts)} contacts from {team_url}")
                        break  # Found contacts, no need to try more pages

                except Exception as e:
                    continue

            await ctx.close()

        except Exception as e:
            logger.error(f"  ❌ Failed to crawl {fund_url}: {e}")

        return contacts

    def _save_csv(self):
        """Save all contacts to CSV."""
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        fieldnames = ["name", "role", "email", "linkedin", "fund_name", "fund_url", "source_page"]

        with open(self.output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for contact in self.all_contacts:
                writer.writerow(asdict(contact))

        logger.info(f"💾 Saved {len(self.all_contacts)} contacts to {self.output_file}")

    async def run(self):
        """Execute the deep crawl across all target funds."""
        targets = self._load_targets()
        logger.info(f"""
╔══════════════════════════════════════════╗
║   🕷️  DEEP CRAWLER v1                    ║
║   VC Contact Extraction Engine           ║
╚══════════════════════════════════════════╝

  ⏰  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  🎯  Target funds: {len(targets)}
  🖥️  Headless: {'YES' if self.headless else 'NO'}
  📁  Output: {self.output_file}
""")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)

            # Process funds with a semaphore for concurrency control
            sem = asyncio.Semaphore(self.max_concurrent)

            async def process_fund(url):
                async with sem:
                    contacts = await self._crawl_fund(browser, url)
                    self.all_contacts.extend(contacts)

            # Process in batches
            tasks = [process_fund(url) for url in targets]
            await asyncio.gather(*tasks)

            await browser.close()

        # Save results
        self._save_csv()

        # Print summary
        funds_with_contacts = len(set(c.fund_url for c in self.all_contacts if c.name))
        total_emails = len([c for c in self.all_contacts if c.email])
        total_linkedin = len([c for c in self.all_contacts if c.linkedin])

        logger.info(f"""
============================================================
  📊  DEEP CRAWL SUMMARY
============================================================
  📝  Total contacts: {len(self.all_contacts)}
  🏢  Funds with contacts: {funds_with_contacts}/{len(targets)}
  📧  Emails found: {total_emails}
  🔗  LinkedIn profiles: {total_linkedin}
  ⏱️  Complete
============================================================
""")


# ── CLI Entry Point ──────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CRAWL Deep Crawler — Extract contacts from VC websites")
    parser.add_argument("--targets", default="data/target_funds.txt", help="Path to target URLs file")
    parser.add_argument("--output", default="data/vc_contacts.csv", help="Output CSV path")
    parser.add_argument("--concurrent", type=int, default=3, help="Max concurrent crawls")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--headed", action="store_true", help="Run with browser visible")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of funds to crawl (0 = all)")

    args = parser.parse_args()

    crawler = DeepCrawler(
        target_file=args.targets,
        output_file=args.output,
        max_concurrent=args.concurrent,
        headless=not args.headed
    )

    if args.limit > 0:
        original_load = crawler._load_targets
        def limited_load():
            return original_load()[:args.limit]
        crawler._load_targets = limited_load

    asyncio.run(crawler.run())
