"""
CRAWL — GitHub Commit Email Miner
Mines GitHub commit metadata to discover real email addresses.
Many VC operators contribute to open-source and their git commits
contain their actual work email in the commit author field.
"""

import asyncio
import logging
import os
import re
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import aiohttp

logger = logging.getLogger(__name__)

# GitHub API base
_API_BASE = "https://api.github.com"

# Emails to ignore (GitHub's privacy noreply addresses, etc.)
_IGNORE_EMAIL_PATTERNS = {
    "noreply.github.com",
    "users.noreply.github.com",
    "github.com",
    "localhost",
    "example.com",
}

# Rate limits
_DELAY_BETWEEN_REQUESTS = 0.5  # seconds between API calls


class GitHubMiner:
    """
    Mines GitHub commit history for email addresses.
    Uses the GitHub Search API to find commits by author name,
    then extracts the commit author email from metadata.
    """

    def __init__(self, concurrency: int = 10):
        self._token = os.getenv("GITHUB_TOKEN", "")
        self._sem = asyncio.Semaphore(concurrency)
        self._domain_cache: Dict[str, Set[str]] = {}  # domain -> emails found
        self._stats = {
            "searches_made": 0,
            "commits_inspected": 0,
            "emails_found": 0,
            "leads_enriched": 0,
            "rate_limited": 0,
        }

    def _headers(self) -> dict:
        """Build request headers with optional auth token."""
        headers = {
            "Accept": "application/vnd.github.cloak-preview+json",  # commit search preview
            "User-Agent": "CRAWL-EmailMiner/1.0",
        }
        if self._token:
            headers["Authorization"] = f"token {self._token}"
        return headers

    async def _api_get(self, url: str, params: dict, session: aiohttp.ClientSession) -> Optional[dict]:
        """Make a rate-limited GitHub API request."""
        try:
            async with self._sem:
                async with session.get(
                    url, params=params, headers=self._headers(),
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 403:
                        # Rate limited
                        self._stats["rate_limited"] += 1
                        retry_after = resp.headers.get("Retry-After", "60")
                        logger.warning(f"  ⚠️  GitHub rate-limited, waiting {retry_after}s...")
                        await asyncio.sleep(int(retry_after))
                        return None
                    if resp.status == 422:
                        # Validation error (query too broad, etc.)
                        return None
                    if resp.status != 200:
                        return None
                    return await resp.json()
        except Exception as e:
            logger.debug(f"  GitHub API error: {e}")
            return None

    def _is_valid_email(self, email: str) -> bool:
        """Check if an email is a real person email (not a noreply/bot)."""
        if not email or "@" not in email:
            return False
        email = email.lower()
        domain = email.split("@")[-1]
        if domain in _IGNORE_EMAIL_PATTERNS:
            return False
        if "noreply" in email or "bot" in email:
            return False
        if len(email) > 60 or len(email) < 5:
            return False
        return True

    async def search_by_name(
        self, name: str, target_domain: Optional[str], session: aiohttp.ClientSession
    ) -> Set[str]:
        """
        Search GitHub commits by author name and extract emails.
        Optionally filter to emails matching target_domain.
        """
        self._stats["searches_made"] += 1

        # Build search query
        query = f'author-name:"{name}"'
        if target_domain:
            # Also try a domain-specific search
            query_domain = f'author-email:@{target_domain}'
        else:
            query_domain = None

        found_emails: Set[str] = set()

        # Search by name
        data = await self._api_get(
            f"{_API_BASE}/search/commits",
            {"q": query, "per_page": 5, "sort": "author-date", "order": "desc"},
            session,
        )
        if data and "items" in data:
            for item in data["items"]:
                self._stats["commits_inspected"] += 1
                commit = item.get("commit", {})
                author = commit.get("author", {})
                email = author.get("email", "")
                if self._is_valid_email(email):
                    if target_domain and email.lower().endswith(f"@{target_domain}"):
                        found_emails.add(email.lower())
                    elif not target_domain:
                        found_emails.add(email.lower())

        await asyncio.sleep(_DELAY_BETWEEN_REQUESTS)

        # Also search by domain if available
        if query_domain:
            data = await self._api_get(
                f"{_API_BASE}/search/commits",
                {"q": query_domain, "per_page": 10, "sort": "author-date", "order": "desc"},
                session,
            )
            if data and "items" in data:
                for item in data["items"]:
                    self._stats["commits_inspected"] += 1
                    commit = item.get("commit", {})
                    author = commit.get("author", {})
                    email = author.get("email", "")
                    name_from_commit = author.get("name", "")
                    if self._is_valid_email(email):
                        found_emails.add(email.lower())

            await asyncio.sleep(_DELAY_BETWEEN_REQUESTS)

        self._stats["emails_found"] += len(found_emails)
        return found_emails

    async def search_domain(
        self, domain: str, session: aiohttp.ClientSession
    ) -> Set[str]:
        """Search for all emails at a domain via GitHub commits."""
        if domain in self._domain_cache:
            return self._domain_cache[domain]

        data = await self._api_get(
            f"{_API_BASE}/search/commits",
            {"q": f"author-email:@{domain}", "per_page": 30, "sort": "author-date", "order": "desc"},
            session,
        )

        found: Set[str] = set()
        if data and "items" in data:
            for item in data["items"]:
                self._stats["commits_inspected"] += 1
                commit = item.get("commit", {})
                email = commit.get("author", {}).get("email", "")
                if self._is_valid_email(email) and email.lower().endswith(f"@{domain}"):
                    found.add(email.lower())

        self._domain_cache[domain] = found
        self._stats["emails_found"] += len(found)

        if found:
            logger.info(f"  🐙  GitHub miner: found {len(found)} emails for {domain}")

        await asyncio.sleep(_DELAY_BETWEEN_REQUESTS)
        return found

    async def enrich_batch(self, leads: list) -> list:
        """
        Enrich leads with emails discovered from GitHub commit metadata.
        Only processes leads that still don't have emails.
        """
        from deep_crawl import _match_email_to_name

        no_email = [
            lead for lead in leads
            if not lead.email or lead.email in ("N/A", "N/A (invalid)")
        ]

        if not no_email:
            logger.info("  🐙  GitHub miner: no leads need enrichment")
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

        logger.info(f"  🐙  GitHub miner: searching {len(domain_leads)} domains for {len(no_email)} leads...")

        if not self._token:
            logger.warning("  ⚠️  No GITHUB_TOKEN set — limited to 60 req/hr (set env var for 5,000/hr)")

        async with aiohttp.ClientSession() as session:
            for domain, domain_group in domain_leads.items():
                # Phase 1: Domain-wide commit search
                domain_emails = await self.search_domain(domain, session)

                # Match found emails to leads
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
                            lead.email_status = "github"
                            unmatched.remove(best_email)
                            self._stats["leads_enriched"] += 1
                            logger.info(f"  🐙  GitHub email for {lead.name}: {best_email} (score={best_score:.2f})")

                # Phase 2: Per-person search for top 5 remaining
                still_missing = [
                    l for l in domain_group
                    if not l.email or l.email in ("N/A", "N/A (invalid)")
                ]
                for lead in still_missing[:5]:
                    found = await self.search_by_name(lead.name, domain, session)
                    if found:
                        email = list(found)[0]
                        lead.email = email
                        lead.email_status = "github"
                        self._stats["leads_enriched"] += 1
                        logger.info(f"  🐙  GitHub email for {lead.name}: {email}")

        logger.info(
            f"  🐙  GitHub miner complete: {self._stats['leads_enriched']} leads enriched, "
            f"{self._stats['emails_found']} emails found "
            f"({self._stats['searches_made']} searches, "
            f"{self._stats['commits_inspected']} commits inspected, "
            f"{self._stats['rate_limited']} rate-limited)"
        )
        return leads

    @property
    def stats(self) -> dict:
        return dict(self._stats)
