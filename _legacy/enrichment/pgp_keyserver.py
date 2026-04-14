"""
CRAWL — PGP Keyserver Scraper
Searches public PGP keyservers by person name to extract email addresses
from published public keys.

PGP keyservers are federated, public databases where people publish their
cryptographic keys. Each key contains one or more UIDs — and UIDs almost
always include the owner's real email address. Since these keys are *intended*
to be publicly discoverable (that's the whole point of a keyserver), querying
them is completely legitimate.

We search multiple keyservers for redundancy:
  1. keys.openpgp.org  — the main modern keyserver
  2. keyserver.ubuntu.com  — Ubuntu/Canonical's server, large user base
  3. keys.mailvelope.com  — Mailvelope browser extension users

The HKP (HTTP Keyserver Protocol) search returns an index with UIDs that
contain email addresses. We parse those out and match to the target domain.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Set
from urllib.parse import quote, urlparse

import aiohttp

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,15}')

# HKP search endpoint format — returns machine-readable key index
_KEYSERVERS = [
    "https://keyserver.ubuntu.com/pks/lookup?op=vindex&search={query}&options=mr",
    "https://keys.mailvelope.com/pks/lookup?op=vindex&search={query}&options=mr",
]

# Emails to ignore
_IGNORE_PATTERNS = {
    "noreply", "no-reply", "example.com", "test@", "root@",
    "admin@", "support@", "info@", "security@",
}


def _is_useful_email(email: str, target_domain: Optional[str] = None) -> bool:
    """Filter garbage emails from keyserver results."""
    if not email or "@" not in email:
        return False
    email = email.lower()
    for pat in _IGNORE_PATTERNS:
        if pat in email:
            return False
    if len(email) > 60 or len(email) < 5:
        return False
    if target_domain and not email.endswith(f"@{target_domain}"):
        return False
    return True


class PGPKeyserverScraper:
    """
    Scrapes PGP keyservers by person name to find their email.
    Unlike the Gravatar approach (which confirms a guess), this can
    discover emails we'd never have guessed — personal domains,
    university addresses, alternate formats.
    """

    def __init__(self, concurrency: int = 10):
        self._sem = asyncio.Semaphore(concurrency)
        self._name_cache: Dict[str, Set[str]] = {}
        self._stats = {
            "leads_checked": 0,
            "keyservers_queried": 0,
            "keys_found": 0,
            "emails_extracted": 0,
            "leads_enriched": 0,
        }

    async def _search_keyserver(
        self, url: str, session: aiohttp.ClientSession
    ) -> Set[str]:
        """Query a single keyserver and extract emails from the response."""
        found: Set[str] = set()
        try:
            async with self._sem:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={"User-Agent": "CRAWL-PGPScraper/1.0"},
                ) as resp:
                    self._stats["keyservers_queried"] += 1
                    if resp.status != 200:
                        return found
                    text = await resp.text(errors="replace")

            # HKP machine-readable format: uid lines contain URL-encoded UIDs
            # Format: uid:<url-encoded name <email>>:<creation_ts>:<expiry_ts>:<flags>
            for line in text.splitlines():
                if line.startswith("uid:"):
                    # URL-decode the UID field
                    from urllib.parse import unquote
                    uid = unquote(line.split(":")[1])
                    for match in _EMAIL_RE.finditer(uid):
                        email = match.group().lower().rstrip(".")
                        found.add(email)
                        self._stats["keys_found"] += 1

        except Exception as e:
            logger.debug(f"  🔑  PGP keyserver error: {e}")
        return found

    async def search_by_name(
        self, name: str, target_domain: Optional[str], session: aiohttp.ClientSession
    ) -> Set[str]:
        """Search all keyservers for a person's name, return matching emails."""
        cache_key = f"{name}|{target_domain}"
        if cache_key in self._name_cache:
            return self._name_cache[cache_key]

        query = quote(name)
        tasks = [
            self._search_keyserver(url.format(query=query), session)
            for url in _KEYSERVERS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_emails: Set[str] = set()
        for r in results:
            if isinstance(r, set):
                all_emails.update(r)

        # Filter to target domain if specified
        valid = {e for e in all_emails if _is_useful_email(e, target_domain)}
        self._name_cache[cache_key] = valid
        self._stats["emails_extracted"] += len(valid)
        return valid

    async def enrich_batch(self, leads: list) -> list:
        """
        For each lead without an email, search PGP keyservers by name.
        If we find an email matching their fund's domain, assign it.
        """
        no_email = [
            lead for lead in leads
            if not lead.email or lead.email in ("N/A", "N/A (invalid)")
        ]

        if not no_email:
            logger.info("  🔑  PGP scraper: no leads need enrichment")
            return leads

        logger.info(
            f"  🔑  PGP keyserver: searching {len(no_email)} names "
            f"across {len(_KEYSERVERS)} keyservers..."
        )

        async with aiohttp.ClientSession() as session:
            for lead in no_email:
                self._stats["leads_checked"] += 1

                # Extract domain for filtering
                target_domain = None
                if lead.website and lead.website not in ("N/A", ""):
                    try:
                        parsed = urlparse(
                            lead.website if "://" in lead.website
                            else f"https://{lead.website}"
                        )
                        target_domain = parsed.netloc.lower().replace("www.", "")
                    except Exception:
                        pass

                emails = await self.search_by_name(
                    lead.name, target_domain, session
                )

                if emails:
                    # Prefer domain-matching email; fall back to any
                    best = None
                    for e in emails:
                        if target_domain and e.endswith(f"@{target_domain}"):
                            best = e
                            break
                    if not best:
                        best = list(emails)[0]

                    lead.email = best
                    lead.email_status = "pgp_keyserver"
                    self._stats["leads_enriched"] += 1
                    logger.info(
                        f"  🔑  PGP key found: {lead.name} → {best}"
                    )

                # Polite delay between searches
                await asyncio.sleep(0.3)

        logger.info(
            f"  🔑  PGP scraper complete: {self._stats['leads_enriched']} enriched, "
            f"{self._stats['emails_extracted']} emails extracted "
            f"({self._stats['keyservers_queried']} queries across "
            f"{self._stats['leads_checked']} leads)"
        )
        return leads

    @property
    def stats(self) -> dict:
        return dict(self._stats)
