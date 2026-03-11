"""
CRAWL — Wayback Machine Email Enricher
Fetches archived versions of fund team/about pages from the Internet Archive
to find emails that were published but later removed.

Design:
- Domain-level: one CDX query per fund domain, results cached and shared across leads
- Fetches up to 3 archived snapshots (most recent first)
- Reuses extract_emails_from_html() and _match_email_to_name() from deep_crawl.py
- Rate-limited: 1s between Wayback requests (per polite-use guidelines)
- No API key needed — public endpoint only
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Wayback Machine CDX API
_CDX_URL = "http://web.archive.org/cdx/search/cdx"

# Wayback Machine snapshot prefix
_WAYBACK_PREFIX = "http://web.archive.org/web"

# Rate limit: 1 request per second to be polite to the Archive
_WAYBACK_DELAY = 1.5

# Pages most likely to have team emails
_TEAM_PAGE_SUFFIXES = [
    "/team",
    "/about",
    "/people",
    "/about/team",
    "/about-us",
    "/contact",
]

# Standard email pattern
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,15}')

# Domains/patterns to reject
_IGNORE_EMAIL_PATTERNS = {
    "example.com", "email.com", "domain.com",
    "noreply", "no-reply", "donotreply",
    "archive.org", "web.archive.org",
    "sentry.io", "w3.org",
}

MAX_SNAPSHOTS_PER_PAGE = 3
MAX_PAGES_PER_DOMAIN = 2  # Check /team and /about only to keep it fast


def _is_valid_email(email: str, target_domain: Optional[str] = None) -> bool:
    """Validate that email looks like a real person's work email."""
    if not email or "@" not in email:
        return False
    email = email.lower()
    domain = email.split("@")[-1]
    for pat in _IGNORE_EMAIL_PATTERNS:
        if pat in email:
            return False
    if len(email) > 60 or len(email) < 5:
        return False
    if any(ext in email for ext in [".png", ".jpg", ".gif", ".css", ".js", ".svg"]):
        return False
    if target_domain:
        return domain == target_domain
    return True


def _extract_emails_from_html(html: str, target_domain: Optional[str] = None) -> Set[str]:
    """Parse HTML with BeautifulSoup and extract email addresses."""
    found: Set[str] = set()
    try:
        soup = BeautifulSoup(html, "html.parser")
        # 1. Look for mailto: links first (most reliable)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("mailto:"):
                email = href[7:].split("?")[0].strip().lower()
                if _is_valid_email(email, target_domain):
                    found.add(email)

        # 2. Regex scan the full page text
        page_text = soup.get_text(separator=" ", strip=True)
        for match in _EMAIL_RE.finditer(page_text):
            email = match.group().lower().rstrip(".")
            if _is_valid_email(email, target_domain):
                found.add(email)

        # 3. Also scan raw HTML (some emails are in attributes/comments)
        for match in _EMAIL_RE.finditer(html):
            email = match.group().lower().rstrip(".")
            if _is_valid_email(email, target_domain):
                found.add(email)

    except Exception as e:
        logger.debug(f"  🕰️  HTML parse error: {e}")

    return found


class WaybackEnricher:
    """
    Enriches leads by fetching archived versions of fund team/about pages
    from the Wayback Machine and extracting email addresses.
    """

    def __init__(self):
        self._domain_cache: Dict[str, Set[str]] = {}
        self._stats = {
            "domains_queried": 0,
            "snapshots_fetched": 0,
            "emails_found": 0,
            "leads_enriched": 0,
            "errors": 0,
        }

    def _headers(self) -> dict:
        return {
            "User-Agent": "CRAWL EmailMiner/1.0 (Internet Archive CDX lookup)",
            "Accept": "application/json",
        }

    async def _get_cdx_snapshots(
        self, url_pattern: str, session: aiohttp.ClientSession, limit: int = 5
    ) -> List[str]:
        """
        Query the CDX API for archived snapshots of a URL pattern.
        Returns a list of (timestamp, original_url) pairs for the most recent snapshots.
        """
        params = {
            "url": url_pattern,
            "output": "json",
            "limit": limit,
            "fl": "timestamp,original",
            "filter": "statuscode:200",
            "collapse": "digest",
            "from": "20150101",
        }
        try:
            async with session.get(
                _CDX_URL,
                params=params,
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json(content_type=None)
                # First row is the header ["timestamp", "original"]
                if not data or len(data) < 2:
                    return []
                records = data[1:]  # skip header row
                # Build Wayback URL for each snapshot (most recent = last in list)
                snapshots = []
                for record in reversed(records):
                    if len(record) >= 2:
                        timestamp, original = record[0], record[1]
                        wayback_url = f"{_WAYBACK_PREFIX}/{timestamp}/{original}"
                        snapshots.append(wayback_url)
                return snapshots
        except asyncio.TimeoutError:
            logger.debug(f"  🕰️  CDX timeout for {url_pattern}")
        except Exception as e:
            self._stats["errors"] += 1
            logger.debug(f"  🕰️  CDX error for {url_pattern}: {e}")
        return []

    async def _fetch_snapshot(
        self, wayback_url: str, session: aiohttp.ClientSession, target_domain: str
    ) -> Set[str]:
        """Fetch a single Wayback snapshot and extract emails."""
        found: Set[str] = set()
        try:
            async with session.get(
                wayback_url,
                headers={
                    "User-Agent": "CRAWL EmailMiner/1.0",
                    "Accept": "text/html",
                },
                timeout=aiohttp.ClientTimeout(total=25),
                allow_redirects=True,
            ) as resp:
                if resp.status != 200:
                    return found
                html = await resp.text(errors="replace")
                self._stats["snapshots_fetched"] += 1
                found = _extract_emails_from_html(html, target_domain)
        except asyncio.TimeoutError:
            logger.debug(f"  🕰️  Snapshot timeout: {wayback_url[:80]}")
        except Exception as e:
            self._stats["errors"] += 1
            logger.debug(f"  🕰️  Snapshot fetch error: {e}")
        return found

    async def search_domain(
        self, domain: str, session: aiohttp.ClientSession
    ) -> Set[str]:
        """
        Search the Wayback Machine for emails at a given fund domain.
        Checks archived team/about pages and caches results per domain.
        """
        if domain in self._domain_cache:
            return self._domain_cache[domain]

        self._stats["domains_queried"] += 1
        all_emails: Set[str] = set()

        pages_checked = 0
        for suffix in _TEAM_PAGE_SUFFIXES:
            if pages_checked >= MAX_PAGES_PER_DOMAIN:
                break

            url_pattern = f"{domain}{suffix}*"
            snapshots = await self._get_cdx_snapshots(
                url_pattern, session, limit=MAX_SNAPSHOTS_PER_PAGE
            )
            await asyncio.sleep(_WAYBACK_DELAY)

            if not snapshots:
                continue

            pages_checked += 1
            for snapshot_url in snapshots[:MAX_SNAPSHOTS_PER_PAGE]:
                emails = await self._fetch_snapshot(snapshot_url, session, domain)
                all_emails.update(emails)
                await asyncio.sleep(_WAYBACK_DELAY)

        self._domain_cache[domain] = all_emails
        self._stats["emails_found"] += len(all_emails)

        if all_emails:
            logger.info(
                f"  🕰️  Wayback: found {len(all_emails)} emails for {domain}"
            )

        return all_emails

    async def enrich_batch(self, leads: list) -> list:
        """
        Enrich leads with emails found in Wayback Machine snapshots.
        Only processes leads that still don't have emails.
        """
        from deep_crawl import _match_email_to_name

        no_email = [
            lead for lead in leads
            if not lead.email or lead.email in ("N/A", "N/A (invalid)")
        ]

        if not no_email:
            logger.info("  🕰️  Wayback enricher: no leads need enrichment")
            return leads

        # Group by domain
        domain_leads: Dict[str, List] = {}
        for lead in no_email:
            if lead.website and lead.website not in ("N/A", ""):
                try:
                    parsed = urlparse(
                        lead.website if "://" in lead.website else f"https://{lead.website}"
                    )
                    domain = parsed.netloc.lower().replace("www.", "")
                except Exception:
                    continue
                if domain:
                    domain_leads.setdefault(domain, []).append(lead)

        logger.info(
            f"  🕰️  Wayback enricher: searching {len(domain_leads)} domains "
            f"for {len(no_email)} leads..."
        )

        async with aiohttp.ClientSession() as session:
            for domain, domain_group in domain_leads.items():
                domain_emails = await self.search_domain(domain, session)

                if domain_emails:
                    unmatched = list(domain_emails)
                    for lead in domain_group:
                        if lead.email and lead.email not in ("N/A", "N/A (invalid)"):
                            continue
                        best_email = None
                        best_score = 0.0
                        for email in unmatched:
                            score = _match_email_to_name(email, lead.name)
                            if score > best_score:
                                best_score = score
                                best_email = email
                        if best_email and best_score >= 0.3:
                            lead.email = best_email
                            lead.email_status = "wayback"
                            unmatched.remove(best_email)
                            self._stats["leads_enriched"] += 1
                            logger.info(
                                f"  🕰️  Wayback email for {lead.name}: "
                                f"{best_email} (score={best_score:.2f})"
                            )

        logger.info(
            f"  🕰️  Wayback enricher complete: {self._stats['leads_enriched']} leads enriched, "
            f"{self._stats['emails_found']} emails found "
            f"({self._stats['domains_queried']} domains, "
            f"{self._stats['snapshots_fetched']} snapshots fetched)"
        )
        return leads

    @property
    def stats(self) -> dict:
        return dict(self._stats)
