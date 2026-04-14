"""
CRAWL — Gravatar Oracle
Confirms which email permutation is real by probing avatar services.

Technique: Gravatar and Libravatar map email → avatar via MD5 hash.
Requesting an avatar with ?d=404 returns HTTP 404 for unregistered
emails and 200 for registered ones. Since Gravatar is embedded in
WordPress, GitHub, Slack, Jira, Trello and hundreds of other services,
any tech-adjacent person almost certainly has a registration somewhere.

This gives us a free, rate-limit-free, zero-auth email existence oracle
that's stronger than SMTP verification (no greylisting, no catch-all
confusion, works against Gmail).

Probes two services in parallel for each candidate:
  1. Gravatar  (WordPress / Automattic ecosystem)
  2. Libravatar (Fedora / FOSS ecosystem)
A hit on EITHER confirms the email is real.
"""

import asyncio
import hashlib
import logging
import re
import unicodedata
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import aiohttp

logger = logging.getLogger(__name__)

# ── Email permutation patterns (same as email_guesser) ────────────────
_PATTERNS = [
    "{first}.{last}@{domain}",
    "{first}@{domain}",
    "{f}{last}@{domain}",
    "{first}{last}@{domain}",
    "{f}.{last}@{domain}",
    "{last}@{domain}",
    "{first}_{last}@{domain}",
    "{last}.{first}@{domain}",
]

_ORACLE_URLS = [
    "https://gravatar.com/avatar/{}?d=404&s=1",
    "https://cdn.libravatar.org/avatar/{}?d=404&s=1",
]


def _normalize(name_part: str) -> str:
    """Lowercase, strip accents, keep only ascii alpha."""
    nfkd = unicodedata.normalize("NFKD", name_part)
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z]", "", ascii_only.lower())


def _avatar_hash(email: str) -> str:
    """MD5 hash of the lowercased, stripped email per Gravatar/Libravatar spec."""
    return hashlib.md5(email.lower().strip().encode("utf-8")).hexdigest()


def _generate_candidates(name: str, domain: str) -> List[str]:
    """Generate all plausible email permutations for a name + domain."""
    parts = name.strip().split()
    if len(parts) < 2:
        return []
    first = _normalize(parts[0])
    last = _normalize(parts[-1])
    if not first or not last:
        return []
    f = first[0]
    return [p.format(first=first, last=last, f=f, domain=domain) for p in _PATTERNS]


class GravatarOracle:
    """
    Probes Gravatar + Libravatar to confirm which email permutation is real.
    Fast, free, no API key, no rate limit.  Fires parallel HEAD requests
    against CDN endpoints for every candidate email.
    """

    def __init__(self, concurrency: int = 80):
        self._sem = asyncio.Semaphore(concurrency)
        self._stats = {
            "leads_checked": 0,
            "candidates_probed": 0,
            "emails_confirmed": 0,
            "leads_enriched": 0,
        }

    async def _check_one(
        self, email: str, session: aiohttp.ClientSession
    ) -> bool:
        """Check a single email against ALL oracle services.
        Returns True on the first 200 from any service."""
        h = _avatar_hash(email)
        for url_tpl in _ORACLE_URLS:
            url = url_tpl.format(h)
            try:
                async with self._sem:
                    async with session.head(
                        url,
                        timeout=aiohttp.ClientTimeout(total=5),
                        allow_redirects=True,
                    ) as resp:
                        self._stats["candidates_probed"] += 1
                        if resp.status == 200:
                            return True
            except Exception:
                pass
        return False

    async def _probe_candidates(
        self, candidates: List[str], session: aiohttp.ClientSession
    ) -> Optional[str]:
        """Probe candidates in parallel. Return first confirmed email."""
        tasks = [self._check_one(c, session) for c in candidates]
        results = await asyncio.gather(*tasks)
        for candidate, hit in zip(candidates, results):
            if hit:
                return candidate
        return None

    async def enrich_batch(self, leads: list) -> list:
        """
        For each lead without an email, generate permutations and probe
        avatar services to confirm which one is real.
        """
        no_email = [
            lead for lead in leads
            if not lead.email or lead.email in ("N/A", "N/A (invalid)")
        ]

        if not no_email:
            logger.info("  👻  Gravatar oracle: no leads need enrichment")
            return leads

        # Group by domain
        domain_leads: Dict[str, List] = {}
        for lead in no_email:
            if lead.website and lead.website not in ("N/A", ""):
                try:
                    parsed = urlparse(
                        lead.website if "://" in lead.website
                        else f"https://{lead.website}"
                    )
                    domain = parsed.netloc.lower().replace("www.", "")
                except Exception:
                    continue
                if domain:
                    domain_leads.setdefault(domain, []).append(lead)

        logger.info(
            f"  👻  Gravatar oracle: probing {len(domain_leads)} domains "
            f"for {len(no_email)} leads..."
        )

        async with aiohttp.ClientSession() as session:
            for domain, domain_group in domain_leads.items():
                for lead in domain_group:
                    self._stats["leads_checked"] += 1
                    candidates = _generate_candidates(lead.name, domain)
                    if not candidates:
                        continue

                    confirmed = await self._probe_candidates(
                        candidates, session
                    )
                    if confirmed:
                        lead.email = confirmed
                        lead.email_status = "gravatar_confirmed"
                        self._stats["emails_confirmed"] += 1
                        self._stats["leads_enriched"] += 1
                        logger.info(
                            f"  👻  Gravatar CONFIRMED: "
                            f"{lead.name} → {confirmed}"
                        )

        logger.info(
            f"  👻  Gravatar oracle complete: "
            f"{self._stats['emails_confirmed']} confirmed "
            f"out of {self._stats['candidates_probed']} probes "
            f"({self._stats['leads_checked']} leads checked)"
        )
        return leads

    @property
    def stats(self) -> dict:
        return dict(self._stats)
