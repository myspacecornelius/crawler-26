"""
CRAWL — Email Pattern Guesser (v2)
For named contacts with a known fund domain, generates email addresses
using detected patterns or statistical defaults.

Key fix from v1: MX records are domain-level, not email-level. Checking
MX per-candidate always picks the first pattern. Now we check MX once
per domain, then apply the best pattern.
"""

import asyncio
import logging
import re
import unicodedata
from typing import List, Optional
from urllib.parse import urlparse

from enrichment.email_validator import EmailValidator

logger = logging.getLogger(__name__)


# Common email patterns ordered by prevalence at professional firms
# first.last is the most common professional pattern (Google Workspace, O365 default)
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

# Default pattern when no learned pattern exists — first.last is statistically
# most common for professional orgs (Google Workspace, Microsoft 365)
_DEFAULT_PATTERN = "{first}.{last}@{domain}"

# Words that indicate a company/fund name rather than a person name
_COMPANY_WORDS = {
    "capital", "ventures", "partners", "fund", "group", "holdings",
    "management", "investments", "equity", "advisors", "advisory",
    "associates", "labs", "studio", "studios", "foundation",
    "initiative", "institute", "accelerator", "incubator", "llc",
    "inc", "corp", "ltd", "limited", "gmbh", "sa", "ag",
    "news", "our", "the", "about", "additional", "strategic",
    "continuity", "growth", "seed", "series", "demo", "day",
    "portfolio", "companies", "company", "team", "meet", "join",
    "alumni", "network", "community", "program", "programs",
    "scout", "scouts", "bio", "life", "sciences", "games",
    "start", "path", "next", "catalyst", "innovation",
    "development", "fundamentals", "research", "digital",
    "global", "international", "technology", "technologies",
    "operating", "platform", "select", "emerging",
    "twitter", "linkedin", "facebook", "instagram", "youtube",
    "follow", "contact", "apply", "subscribe", "sign", "read",
    "learn", "view", "visit", "more", "blog", "press", "media",
    "on", "in", "at", "for", "to", "of", "an", "by", "from",
    "cookies", "cookie", "functional", "performance", "targeting",
    "marketing", "privacy", "overview", "principles", "core",
    "leadership", "history", "availability", "resources",
    "navigation", "submission", "submissions", "board",
    "shared", "values", "philosophy", "customers", "colleagues",
    "communities", "activity", "putting", "challenging",
    "convention", "smarter", "together", "humbly", "check",
    "your", "every", "stage", "how", "we", "help",
    "startups", "links", "additional", "information", "connect",
}


def _is_person_name(name: str) -> bool:
    """Check if a name looks like a real person (not a company/fund)."""
    if not name or name == "N/A" or name.lower() == "unknown":
        return False
    # Strip common prefixes from team pages
    cleaned = name.strip()
    for prefix in ["Meet ", "About ", "Dr. ", "Prof. "]:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    # Remove trailing periods
    cleaned = cleaned.rstrip(".")
    words = cleaned.lower().split()
    if len(words) < 2 or len(words) > 5:
        return False
    # If ANY word is a company indicator, reject
    if any(w.rstrip(".,;:") in _COMPANY_WORDS for w in words):
        return False
    # All-caps multi-word strings are likely headers, not names
    if cleaned == cleaned.upper() and len(words) > 2:
        return False
    # Names with numbers are not person names
    if any(c.isdigit() for c in cleaned):
        return False
    return True


def _clean_person_name(name: str) -> str:
    """Clean up a person name for email generation (strip prefixes, suffixes)."""
    cleaned = name.strip()
    for prefix in ["Meet ", "About ", "Dr. ", "Prof. "]:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    return cleaned.rstrip(".").strip()


def _normalize(name_part: str) -> str:
    """Lowercase, strip accents, keep only ascii alpha chars."""
    nfkd = unicodedata.normalize("NFKD", name_part)
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z]", "", ascii_only.lower())


def _extract_domain(website: str) -> Optional[str]:
    """Pull the bare domain from a website URL."""
    if not website or website == "N/A":
        return None
    try:
        parsed = urlparse(website if "://" in website else f"https://{website}")
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc if netloc else None
    except Exception:
        return None


def generate_candidates(name: str, domain: str) -> List[str]:
    """
    Generate all email pattern candidates for a given name + domain.
    Returns an empty list if the name cannot be split into first/last.
    """
    parts = name.strip().split()
    if len(parts) < 2:
        return []

    first = _normalize(parts[0])
    last = _normalize(parts[-1])

    if not first or not last:
        return []

    f = first[0]

    candidates = []
    for pattern in _PATTERNS:
        candidate = pattern.format(first=first, last=last, f=f, domain=domain)
        candidates.append(candidate)

    return candidates


def detect_pattern(email: str, name: str) -> Optional[str]:
    """
    Given a known email and the person's name, detect which pattern was used.
    Returns the pattern string (e.g. '{first}@{domain}') or None.
    """
    parts = name.strip().split()
    if len(parts) < 2:
        return None

    first = _normalize(parts[0])
    last = _normalize(parts[-1])
    if not first or not last:
        return None

    local, _, domain = email.partition("@")
    if not local or not domain:
        return None

    local = local.lower()
    f = first[0]

    # Check each pattern against the known email's local part
    for pattern in _PATTERNS:
        expected_local = pattern.split("@")[0].format(first=first, last=last, f=f, domain=domain)
        if local == expected_local:
            return pattern

    return None


class _PatternCache:
    """Stores detected email patterns per domain for reuse across contacts."""

    def __init__(self):
        self._patterns: dict[str, str] = {}  # domain -> pattern

    def get(self, domain: str) -> Optional[str]:
        return self._patterns.get(domain)

    def learn(self, domain: str, email: str, name: str) -> Optional[str]:
        """Try to detect and cache the pattern for a domain."""
        if domain in self._patterns:
            return self._patterns[domain]
        pattern = detect_pattern(email, name)
        if pattern:
            self._patterns[domain] = pattern
            logger.debug(f"  🔑  Learned pattern for {domain}: {pattern}")
        return pattern

    def apply(self, name: str, domain: str) -> Optional[str]:
        """Apply a cached pattern to generate an email for a new contact."""
        pattern = self._patterns.get(domain)
        if not pattern:
            return None
        parts = name.strip().split()
        if len(parts) < 2:
            return None
        first = _normalize(parts[0])
        last = _normalize(parts[-1])
        if not first or not last:
            return None
        f = first[0]
        return pattern.format(first=first, last=last, f=f, domain=domain)

    @property
    def domains_known(self) -> int:
        return len(self._patterns)


class EmailGuesser:
    """
    Generates email addresses for contacts using pattern detection and
    domain-level MX verification.

    Key design: MX records are domain-level (not email-level), so we check
    MX once per domain, then apply the best pattern to ALL contacts at that
    domain. This avoids the v1 bug where MX check always picked the first
    pattern.

    Pipeline:
    1. Learn patterns from contacts that already have verified emails.
    2. Apply learned patterns to contacts at the same domain.
    3. For remaining contacts, check domain MX once, then apply default
       pattern (first.last@domain — the most common professional format).
    4. Generate alternative candidates ranked by likelihood.
    """

    def __init__(self, concurrency: int = 10):
        self.validator = EmailValidator()
        self.concurrency = concurrency
        self._sem = asyncio.Semaphore(concurrency)
        self._pattern_cache = _PatternCache()
        self._mx_cache: dict[str, bool] = {}  # domain -> has_mx
        self._stats = {
            "attempted": 0, "found": 0, "skipped": 0,
            "pattern_hits": 0, "default_hits": 0, "mx_rejects": 0,
            "company_skipped": 0, "patterns_discovered": 0,
        }

    async def _discover_domain_pattern(self, name: str, domain: str) -> Optional[str]:
        """SMTP-verify top 3 candidates for one contact to discover domain's email pattern."""
        clean = _clean_person_name(name)
        candidates = generate_candidates(clean, domain)[:3]
        if not candidates:
            return None

        smtp_ok = await self.validator.smtp_self_test()
        if not smtp_ok:
            return None

        for candidate in candidates:
            async with self._sem:
                result = await self.validator.verify_smtp(candidate)
            if result.get("deliverable") is True:
                pattern = detect_pattern(candidate, clean)
                if pattern:
                    self._pattern_cache._patterns[domain] = pattern
                    self._stats["patterns_discovered"] += 1
                    logger.info(f"  \U0001f50d  Discovered pattern for {domain}: {pattern} (via {candidate})")
                    return candidate
            await asyncio.sleep(0.5)

        return None

    async def _check_domain_mx(self, domain: str) -> bool:
        """Check MX once per domain (cached). Returns True if domain can receive email."""
        if domain in self._mx_cache:
            return self._mx_cache[domain]
        async with self._sem:
            has_mx = await self.validator.verify_mx(f"probe@{domain}")
            self._mx_cache[domain] = has_mx
        return has_mx

    def _generate_best_email(self, name: str, domain: str) -> Optional[str]:
        """
        Generate the best email for a name+domain using learned pattern
        or the statistical default (first.last@domain).
        """
        clean = _clean_person_name(name)
        # Try learned pattern first
        email = self._pattern_cache.apply(clean, domain)
        if email:
            return email
        # Fall back to default pattern
        parts = clean.strip().split()
        if len(parts) < 2:
            return None
        first = _normalize(parts[0])
        last = _normalize(parts[-1])
        if not first or not last:
            return None
        f = first[0]
        return _DEFAULT_PATTERN.format(first=first, last=last, f=f, domain=domain)

    async def guess(self, name: str, website: str) -> Optional[str]:
        """
        Generate the best email guess for a single contact.
        Checks domain MX once, then applies best pattern.
        """
        if not _is_person_name(name):
            self._stats["company_skipped"] += 1
            return None

        domain = _extract_domain(website)
        if not domain:
            self._stats["skipped"] += 1
            return None

        # Check domain MX once (cached)
        has_mx = await self._check_domain_mx(domain)
        if not has_mx:
            self._stats["mx_rejects"] += 1
            return None

        self._stats["attempted"] += 1

        email = self._generate_best_email(name, domain)
        if email:
            self._stats["found"] += 1
            self._stats["default_hits"] += 1
            logger.debug(f"  ✉️  Guessed email: {email}")
        return email

    def generate_all_candidates(self, name: str, website: str) -> List[str]:
        """
        Generate ALL plausible email candidates for a contact, ranked by
        likelihood. Useful for downstream SMTP verification.
        """
        domain = _extract_domain(website)
        if not domain or not _is_person_name(name):
            return []
        return generate_candidates(name, domain)

    async def guess_batch(self, leads: list) -> list:
        """
        Run email guessing across a batch of InvestorLead objects.
        Phase 1: Learn patterns from leads that already have emails.
        Phase 2: Apply learned patterns to leads without emails.
        Phase 3: For remaining, check domain MX + apply default pattern.
        Updates leads in-place and returns the list.
        """
        # Phase 1: Learn patterns from existing emails
        for lead in leads:
            if lead.email and lead.email not in ("N/A", "N/A (invalid)") and "@" in lead.email:
                domain = _extract_domain(lead.website)
                if domain and _is_person_name(lead.name):
                    self._pattern_cache.learn(domain, lead.email, lead.name)

        no_email = [
            lead for lead in leads
            if not lead.email or lead.email in ("N/A", "N/A (invalid)")
        ]

        logger.info(f"  \u2709\ufe0f  Email guesser: {len(no_email)} leads without email (of {len(leads)} total)")
        logger.info(f"  \U0001f511  Patterns learned for {self._pattern_cache.domains_known} domains")

        # Phase 1.5: Discover patterns via SMTP for unknown domains
        # Pick one contact per domain, probe top 3 patterns
        domains_to_probe = {}
        for lead in no_email:
            if not _is_person_name(lead.name):
                continue
            domain = _extract_domain(lead.website)
            if domain and not self._pattern_cache.get(domain) and domain not in domains_to_probe:
                domains_to_probe[domain] = lead

        if domains_to_probe:
            logger.info(f"  \U0001f50d  Probing {len(domains_to_probe)} domains for email patterns via SMTP...")
            for domain, lead in domains_to_probe.items():
                await self._discover_domain_pattern(lead.name, domain)
            logger.info(f"  \U0001f50d  Pattern discovery complete: {self._stats['patterns_discovered']} patterns found")

        # Phase 2: Apply known patterns (fast, no MX needed — pattern was
        # learned from a verified email, so domain definitely accepts mail)
        still_no_email = []
        for lead in no_email:
            if not _is_person_name(lead.name):
                self._stats["company_skipped"] += 1
                still_no_email.append(lead)  # keep in list but won't get email
                continue
            domain = _extract_domain(lead.website)
            if domain:
                email = self._pattern_cache.apply(lead.name, domain)
                if email:
                    lead.email = email
                    self._stats["pattern_hits"] += 1
                    continue
            still_no_email.append(lead)

        # Phase 3: Check domain MX once, then apply default pattern
        async def _process(lead):
            if not _is_person_name(lead.name):
                return
            guessed = await self.guess(lead.name, lead.website)
            if guessed:
                lead.email = guessed
                # Learn this as the pattern for the domain
                domain = _extract_domain(lead.website)
                if domain:
                    self._pattern_cache.learn(domain, guessed, lead.name)

        await asyncio.gather(*[_process(lead) for lead in still_no_email])

        found = sum(1 for lead in no_email if lead.email and lead.email not in ("N/A", "N/A (invalid)"))
        logger.info(
            f"  \u2709\ufe0f  Email guesser complete: {found}/{len(no_email)} emails generated "
            f"({self._stats['pattern_hits']} from learned patterns, "
            f"{self._stats['patterns_discovered']} patterns discovered via SMTP, "
            f"{self._stats['default_hits']} from default pattern, "
            f"{self._stats['mx_rejects']} domains had no MX, "
            f"{self._stats['company_skipped']} company names skipped)"
        )
        return leads

    @property
    def stats(self) -> dict:
        return dict(self._stats)
