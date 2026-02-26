"""
CRAWL — Google Dorker Email Enricher
Uses Google search queries to find emails leaked on third-party sites
(SEC filings, conference programs, press releases, cached pages, etc.).

Falls back to SerpAPI if direct Google scraping gets rate-limited.
"""

import asyncio
import logging
import os
import random
import re
from typing import Dict, List, Optional, Set
from urllib.parse import quote_plus, urlparse

import aiohttp

logger = logging.getLogger(__name__)

# ── Rate Limiting ────────────────────────────────
_MIN_DELAY = 2.0   # minimum seconds between Google requests
_MAX_DELAY = 4.0   # maximum seconds between Google requests
_MAX_RESULTS_PER_QUERY = 10

# ── User-Agent rotation ─────────────────────────
_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]

# Standard email regex
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,15}')

# False positive domains to skip
_SKIP_DOMAINS = {
    "example.com", "email.com", "domain.com", "sentry.io",
    "wixpress.com", "w3.org", "schema.org", "googleapis.com",
    "google.com", "gstatic.com", "googleusercontent.com",
    "facebook.com", "twitter.com", "github.com",
}


def _extract_emails_from_text(text: str, target_domain: Optional[str] = None) -> Set[str]:
    """Extract email addresses from text, optionally filtering to a target domain."""
    emails = set()
    for match in _EMAIL_RE.finditer(text):
        email = match.group().lower().rstrip(".")
        # Skip false positives
        email_domain = email.split("@")[-1]
        if email_domain in _SKIP_DOMAINS:
            continue
        if any(ext in email for ext in [".png", ".jpg", ".svg", ".gif", ".css", ".js"]):
            continue
        if len(email) > 60 or len(email) < 5:
            continue
        # If we have a target domain, prefer matches but keep all
        emails.add(email)
    return emails


class GoogleDorker:
    """
    Searches Google for leaked email addresses using targeted dork queries.
    Groups leads by domain for efficient batching.
    """

    def __init__(self, concurrency: int = 3):
        self._sem = asyncio.Semaphore(concurrency)
        self._serpapi_key = os.getenv("SERPAPI_KEY", "")
        self._domain_cache: Dict[str, Set[str]] = {}  # domain -> set of found emails
        self._stats = {
            "domains_searched": 0,
            "queries_made": 0,
            "emails_found": 0,
            "leads_enriched": 0,
            "rate_limited": 0,
        }

    async def _google_search(self, query: str, session: aiohttp.ClientSession) -> str:
        """Execute a Google search and return the results page HTML."""
        url = f"https://www.google.com/search?q={quote_plus(query)}&num={_MAX_RESULTS_PER_QUERY}"
        headers = {
            "User-Agent": random.choice(_USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
        }
        try:
            async with self._sem:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 429:
                        self._stats["rate_limited"] += 1
                        logger.warning("  ⚠️  Google rate-limited, backing off...")
                        await asyncio.sleep(random.uniform(30, 60))
                        return ""
                    if resp.status != 200:
                        return ""
                    return await resp.text()
        except Exception as e:
            logger.debug(f"  Google search failed: {e}")
            return ""

    async def _serpapi_search(self, query: str, session: aiohttp.ClientSession) -> str:
        """Fallback: use SerpAPI for Google results."""
        if not self._serpapi_key:
            return ""
        url = "https://serpapi.com/search.json"
        params = {
            "q": query,
            "api_key": self._serpapi_key,
            "num": _MAX_RESULTS_PER_QUERY,
            "engine": "google",
        }
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return ""
                data = await resp.json()
                # Concatenate all snippet text for email extraction
                text_parts = []
                for result in data.get("organic_results", []):
                    text_parts.append(result.get("snippet", ""))
                    text_parts.append(result.get("title", ""))
                    text_parts.append(result.get("link", ""))
                return " ".join(text_parts)
        except Exception as e:
            logger.debug(f"  SerpAPI search failed: {e}")
            return ""

    async def search_domain(self, domain: str, session: aiohttp.ClientSession) -> Set[str]:
        """Search Google for all emails at a given domain."""
        if domain in self._domain_cache:
            return self._domain_cache[domain]

        all_emails: Set[str] = set()

        # Query 1: Direct email pattern search
        queries = [
            f'"@{domain}"',                           # Any email at this domain
            f'"@{domain}" email contact team',         # Contextual
            f'site:sec.gov "@{domain}"',               # SEC filings
            f'site:crunchbase.com "@{domain}"',        # Crunchbase
        ]

        for query in queries:
            self._stats["queries_made"] += 1

            # Try direct Google first
            html = await self._google_search(query, session)

            if not html and self._serpapi_key:
                # Fallback to SerpAPI
                html = await self._serpapi_search(query, session)

            if html:
                found = _extract_emails_from_text(html, domain)
                # Only keep emails matching the target domain
                domain_emails = {e for e in found if e.endswith(f"@{domain}")}
                all_emails.update(domain_emails)

            # Rate limit between queries
            await asyncio.sleep(random.uniform(_MIN_DELAY, _MAX_DELAY))

        self._domain_cache[domain] = all_emails
        self._stats["domains_searched"] += 1
        self._stats["emails_found"] += len(all_emails)

        if all_emails:
            logger.info(f"  🔍  Google dorker: found {len(all_emails)} emails for {domain}")

        return all_emails

    async def search_person(
        self, name: str, domain: str, session: aiohttp.ClientSession
    ) -> Optional[str]:
        """Search Google for a specific person's email at a domain."""
        query = f'"{name}" "@{domain}"'
        self._stats["queries_made"] += 1

        html = await self._google_search(query, session)
        if not html and self._serpapi_key:
            html = await self._serpapi_search(query, session)

        if html:
            found = _extract_emails_from_text(html, domain)
            domain_emails = [e for e in found if e.endswith(f"@{domain}")]
            if domain_emails:
                await asyncio.sleep(random.uniform(_MIN_DELAY, _MAX_DELAY))
                return domain_emails[0]

        await asyncio.sleep(random.uniform(_MIN_DELAY, _MAX_DELAY))
        return None

    async def enrich_batch(self, leads: list) -> list:
        """
        Enrich a batch of InvestorLead objects with Google-dorked emails.
        Only processes leads that still don't have emails.
        """
        from deep_crawl import _match_email_to_name

        no_email = [
            lead for lead in leads
            if not lead.email or lead.email in ("N/A", "N/A (invalid)")
        ]

        if not no_email:
            logger.info("  🔍  Google dorker: no leads need enrichment")
            return leads

        # Group by domain
        domain_leads: Dict[str, List] = {}
        for lead in no_email:
            if lead.website and lead.website not in ("N/A", ""):
                try:
                    parsed = urlparse(lead.website if "://" in lead.website else f"https://{lead.website}")
                    domain = parsed.netloc.lower().replace("www.", "")
                except Exception:
                    continue
                if domain:
                    domain_leads.setdefault(domain, []).append(lead)

        logger.info(f"  🔍  Google dorker: searching {len(domain_leads)} domains for {len(no_email)} leads...")

        async with aiohttp.ClientSession() as session:
            for domain, domain_group in domain_leads.items():
                # Phase 1: Domain-wide search
                domain_emails = await self.search_domain(domain, session)

                # Match found emails to leads by name
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
                            lead.email_status = "dorked"
                            unmatched.remove(best_email)
                            self._stats["leads_enriched"] += 1
                            logger.info(f"  🔍  Dorked email for {lead.name}: {best_email} (score={best_score:.2f})")

                # Phase 2: Per-person search for remaining leads (limited to 3 per domain)
                still_missing = [
                    l for l in domain_group
                    if not l.email or l.email in ("N/A", "N/A (invalid)")
                ]
                for lead in still_missing[:3]:
                    email = await self.search_person(lead.name, domain, session)
                    if email:
                        lead.email = email
                        lead.email_status = "dorked"
                        self._stats["leads_enriched"] += 1
                        logger.info(f"  🔍  Dorked email for {lead.name}: {email}")

        logger.info(
            f"  🔍  Google dorker complete: {self._stats['leads_enriched']} leads enriched, "
            f"{self._stats['emails_found']} emails found across {self._stats['domains_searched']} domains "
            f"({self._stats['queries_made']} queries, {self._stats['rate_limited']} rate-limited)"
        )
        return leads

    @property
    def stats(self) -> dict:
        return dict(self._stats)
