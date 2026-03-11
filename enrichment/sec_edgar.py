"""
CRAWL — SEC EDGAR Full-Text Email Scraper
Searches SEC EDGAR's full-text search for emails published in regulatory
filings (Form D, ADV, 13F). These filings often contain direct contact
emails for fund managers.

Design:
- Domain-level: one query per fund domain, results cached and shared across leads
- SEC requires User-Agent: Company contact@email.com (supplied below)
- Rate-limited: 10 req/sec per SEC fair-use policy (we use 1 req/s to be safe)
- No API key needed — public endpoint only
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Set
from urllib.parse import quote_plus, urlparse

import aiohttp

logger = logging.getLogger(__name__)

# SEC EDGAR full-text search endpoint
_EFTS_URL = "https://efts.sec.gov/LATEST/search-index"

# SEC fair-use: 10 req/sec max; we use 1s to be conservative
_SEC_DELAY = 1.0

# Standard email regex
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,15}')

# SEC EDGAR requires a descriptive User-Agent with contact info
_USER_AGENT = "CRAWL EmailMiner/1.0 (contact@example.com)"

# Forms most likely to contain manager contact emails
_TARGET_FORMS = ["D", "ADV", "13F-HR", "13F-NT"]

# Emails to ignore
_IGNORE_PATTERNS = {
    "sec.gov", "example.com", "email.com", "domain.com",
    "noreply", "no-reply", "donotreply",
}


def _is_valid_email(email: str, target_domain: Optional[str] = None) -> bool:
    """Check if an email is a real person email."""
    if not email or "@" not in email:
        return False
    email = email.lower()
    domain = email.split("@")[-1]
    for pattern in _IGNORE_PATTERNS:
        if pattern in email:
            return False
    if len(email) > 60 or len(email) < 5:
        return False
    if any(ext in email for ext in [".png", ".jpg", ".gif", ".css", ".js"]):
        return False
    if target_domain:
        return domain == target_domain
    return True


class SECEdgarScraper:
    """
    Scrapes SEC EDGAR full-text search for emails published in regulatory
    filings. Groups leads by domain and distributes found emails back.
    """

    def __init__(self):
        self._domain_cache: Dict[str, Set[str]] = {}
        self._stats = {
            "domains_searched": 0,
            "filings_scanned": 0,
            "emails_found": 0,
            "leads_enriched": 0,
            "errors": 0,
        }

    def _headers(self) -> dict:
        return {
            "User-Agent": _USER_AGENT,
            "Accept": "application/json",
        }

    async def _search_edgar(
        self, domain: str, session: aiohttp.ClientSession
    ) -> Set[str]:
        """
        Search EDGAR full-text for a domain and extract emails from filing metadata.
        Uses the EFTS (EDGAR Full-Text Search) endpoint.
        """
        found: Set[str] = set()

        params = {
            "q": f'"@{domain}"',
            "dateRange": "custom",
            "startdt": "2015-01-01",
            "forms": ",".join(_TARGET_FORMS),
            "_source": "file_date,period_of_report,entity_name,file_num",
            "hits.hits.total.value": 0,
            "hits.hits._source.period_of_report": 0,
        }

        try:
            async with session.get(
                _EFTS_URL,
                params=params,
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    logger.debug(f"  📋 EDGAR returned {resp.status} for {domain}")
                    return found
                data = await resp.json(content_type=None)

            hits = data.get("hits", {}).get("hits", [])
            self._stats["filings_scanned"] += len(hits)

            # Extract emails from snippet/highlights (EDGAR returns matched context)
            for hit in hits:
                highlight = hit.get("highlight", {})
                for field_matches in highlight.values():
                    for snippet in field_matches:
                        for match in _EMAIL_RE.finditer(snippet):
                            email = match.group().lower().rstrip(".")
                            if _is_valid_email(email, domain):
                                found.add(email)

                # Also check source fields
                source = hit.get("_source", {})
                for val in source.values():
                    if isinstance(val, str) and "@" in val:
                        for match in _EMAIL_RE.finditer(val):
                            email = match.group().lower().rstrip(".")
                            if _is_valid_email(email, domain):
                                found.add(email)

        except asyncio.TimeoutError:
            logger.debug(f"  📋 EDGAR timeout for {domain}")
        except Exception as e:
            self._stats["errors"] += 1
            logger.debug(f"  📋 EDGAR search error for {domain}: {e}")

        return found

    async def _fetch_filing_document(
        self, accession_url: str, session: aiohttp.ClientSession, target_domain: str
    ) -> Set[str]:
        """
        Fetch an actual filing document and regex-scan it for domain emails.
        Used as a fallback when the search index hits don't contain email text.
        """
        found: Set[str] = set()
        try:
            async with session.get(
                accession_url,
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    return found
                text = await resp.text(errors="replace")
                for match in _EMAIL_RE.finditer(text):
                    email = match.group().lower().rstrip(".")
                    if _is_valid_email(email, target_domain):
                        found.add(email)
        except Exception as e:
            logger.debug(f"  📋 Filing fetch error: {e}")
        return found

    async def search_domain(
        self, domain: str, session: aiohttp.ClientSession
    ) -> Set[str]:
        """
        Search SEC EDGAR for all emails at a given fund domain.
        Results are cached per-domain to avoid duplicate calls.
        """
        if domain in self._domain_cache:
            return self._domain_cache[domain]

        self._stats["domains_searched"] += 1
        emails = await self._search_edgar(domain, session)

        # If index search didn't yield results, try a broader query
        if not emails:
            await asyncio.sleep(_SEC_DELAY)
            # Try without form filter
            try:
                params = {
                    "q": f'"@{domain}"',
                    "dateRange": "custom",
                    "startdt": "2010-01-01",
                }
                async with session.get(
                    _EFTS_URL,
                    params=params,
                    headers=self._headers(),
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        for hit in data.get("hits", {}).get("hits", []):
                            highlight = hit.get("highlight", {})
                            for field_matches in highlight.values():
                                for snippet in field_matches:
                                    for match in _EMAIL_RE.finditer(snippet):
                                        email = match.group().lower().rstrip(".")
                                        if _is_valid_email(email, domain):
                                            emails.add(email)
            except Exception:
                pass

        self._domain_cache[domain] = emails
        self._stats["emails_found"] += len(emails)

        if emails:
            logger.info(f"  📋  SEC EDGAR: found {len(emails)} emails for {domain}")

        await asyncio.sleep(_SEC_DELAY)
        return emails

    async def enrich_batch(self, leads: list) -> list:
        """
        Enrich leads with emails found in SEC EDGAR filings.
        Only processes leads that still don't have emails.
        """
        from deep_crawl import _match_email_to_name

        no_email = [
            lead for lead in leads
            if not lead.email or lead.email in ("N/A", "N/A (invalid)")
        ]

        if not no_email:
            logger.info("  📋  SEC EDGAR: no leads need enrichment")
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
            f"  📋  SEC EDGAR: searching {len(domain_leads)} domains "
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
                            lead.email_status = "sec_edgar"
                            unmatched.remove(best_email)
                            self._stats["leads_enriched"] += 1
                            logger.info(
                                f"  📋  SEC EDGAR email for {lead.name}: "
                                f"{best_email} (score={best_score:.2f})"
                            )

        logger.info(
            f"  📋  SEC EDGAR complete: {self._stats['leads_enriched']} leads enriched, "
            f"{self._stats['emails_found']} emails found "
            f"({self._stats['domains_searched']} domains, "
            f"{self._stats['filings_scanned']} filings scanned)"
        )
        return leads

    @property
    def stats(self) -> dict:
        return dict(self._stats)
