"""
CRAWL — Generic Website Deep Crawler
Crawls arbitrary VC fund websites to find team/about pages
and extract contact information (names, roles, emails, LinkedIn).
"""

import asyncio
import csv
import os
import random
import re
import logging
from urllib.parse import urlparse, urljoin
from typing import List, Dict
from datetime import datetime

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup

from adapters.base import InvestorLead
from enrichment.email_validator import EmailValidator
from enrichment.email_guesser import EmailGuesser
from enrichment.scoring import LeadScorer
from output.csv_writer import CSVWriter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)



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
    "eir", "entrepreneur in residence", "scout", "fellow",
    "investor", "member", "operator", "observer", "mentor",
    "board", "team", "staff", "manager", "counsel",
    "secretary", "treasurer", "controller", "intern", "resident",
]


# ── Extraction Helpers ───────────────────────────

def _clean_extracted_email(raw: str) -> str:
    """Clean an email that may have adjacent text concatenated to local part or TLD."""
    if '@' not in raw:
        return raw.lower()
    local, domain = raw.rsplit('@', 1)
    # Clean local part: strip leading uppercase words that are concatenated junk
    # e.g. "Statesinfo" -> "info", "3007Emailinfo" -> "info", "Contacthello" -> "hello"
    clean_local = re.sub(r'^(?:[A-Z][a-zA-Z]*|\d+[A-Z][a-zA-Z]*)(?=[a-z])', '', local)
    if not clean_local or '@' in clean_local:
        clean_local = local  # fallback if stripping removed everything
    # Clean domain TLD: strip trailing uppercase words concatenated to TLD
    # e.g. "site.comLinkedIn" -> "site.com", "site.vcFollow" -> "site.vc"
    parts = domain.rsplit('.', 1)
    if len(parts) == 2:
        base, tld = parts
        # Find where actual TLD ends (case transition from lower to upper)
        clean_tld = tld
        for i in range(1, len(tld)):
            if tld[i].isupper() and tld[i-1].islower():
                clean_tld = tld[:i]
                break
        # Cap TLD at 15 chars (longest real TLD)
        if len(clean_tld) > 15:
            clean_tld = clean_tld[:3]
        domain = f"{base}.{clean_tld}"
    return f"{clean_local}@{domain}".lower()


def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text using regex."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,15}'
    emails = re.findall(pattern, text)
    # Filter out common false positives
    filtered = []
    for e in emails:
        e = _clean_extracted_email(e)
        if any(x in e for x in ['.png', '.jpg', '.svg', '.gif', '.css', '.js', 'example.com', 'email.com', 'domain.com', 'sentry.io', 'wixpress', 'sentry-next']):
            continue
        filtered.append(e)
    return list(set(filtered))


def extract_emails_from_html(soup: BeautifulSoup, page_text: str) -> List[str]:
    """
    Extract emails from ALL sources in HTML:
    1. mailto: links (highest quality — intentionally published)
    2. data-email / data-contact attributes
    3. Page text regex
    4. Raw HTML regex (catches JS-rendered or hidden emails)
    5. Common obfuscation patterns (e.g., 'john [at] domain [dot] com')
    """
    emails = set()

    # 1. mailto: links — highest signal
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("mailto:"):
            raw = href.replace("mailto:", "").split("?")[0].strip()
            if "@" in raw and "." in raw.split("@")[-1]:
                emails.add(raw.lower())

    # 2. data attributes that commonly hold emails
    for tag in soup.find_all(True):
        for attr in ["data-email", "data-mail", "data-contact", "data-href"]:
            val = tag.get(attr, "")
            if "@" in val and "." in val:
                emails.add(val.strip().lower())

    # 3. Page text regex
    text_emails = extract_emails(page_text)
    emails.update(text_emails)

    # 4. Raw HTML regex (catches emails in JS vars, hidden spans, etc.)
    raw_html = str(soup)
    html_emails = extract_emails(raw_html)
    emails.update(html_emails)

    # 5. Obfuscation patterns
    obfuscation_patterns = [
        r'([a-zA-Z0-9._%+-]+)\s*\[at\]\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'([a-zA-Z0-9._%+-]+)\s*\(at\)\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'([a-zA-Z0-9._%+-]+)\s*@\s*([a-zA-Z0-9.-]+)\s*\.\s*([a-zA-Z]{2,})',
    ]
    for pat in obfuscation_patterns:
        for match in re.finditer(pat, page_text, re.IGNORECASE):
            groups = match.groups()
            if len(groups) == 2:
                emails.add(f"{groups[0]}@{groups[1]}".lower())
            elif len(groups) == 3:
                emails.add(f"{groups[0]}@{groups[1]}.{groups[2]}".lower())

    # Filter out false positives
    filtered = set()
    for e in emails:
        if any(x in e for x in ['.png', '.jpg', '.svg', '.gif', '.css', '.js',
                                  'example.com', 'email.com', 'domain.com',
                                  'sentry.io', 'wixpress', '@2x', '@3x']):
            continue
        if len(e) > 60 or len(e) < 5:
            continue
        filtered.add(e)

    return list(filtered)


def _match_email_to_name(email: str, name: str) -> float:
    """
    Score how well an email matches a person's name.
    Returns 0.0-1.0 confidence score.
    """
    import unicodedata
    local = email.split("@")[0].lower()
    parts = name.lower().split()
    if len(parts) < 2:
        return 0.0

    def _norm(s):
        nfkd = unicodedata.normalize("NFKD", s)
        return re.sub(r"[^a-z]", "", nfkd.encode("ascii", "ignore").decode("ascii").lower())

    first = _norm(parts[0])
    last = _norm(parts[-1])
    if not first or not last:
        return 0.0

    # Exact pattern matches
    if local == f"{first}.{last}":
        return 1.0
    if local == first:
        return 0.8
    if local == f"{first}{last}":
        return 0.9
    if local == f"{first[0]}{last}":
        return 0.85
    if local == f"{first[0]}.{last}":
        return 0.85
    if local == last:
        return 0.6
    if local == f"{first}_{last}":
        return 0.9
    if local == f"{last}.{first}":
        return 0.8
    # Partial matches
    if first in local and last in local:
        return 0.7
    if first in local:
        return 0.4
    if last in local:
        return 0.5
    return 0.0


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


def _clean_role_text(raw: str) -> str:
    """Clean garbled role text from structured HTML (e.g. 'Based InBay AreaSpecialtySpecialistsFocusInvestor Relations')."""
    import re as _re
    # Add space before uppercase letters that follow lowercase (camelCase boundaries)
    text = _re.sub(r'([a-z])([A-Z])', r'\1 \2', raw)
    # Remove common structural prefixes from team page HTML
    noise_patterns = [
        r'Based\s+In\s*', r'Specialty\s*', r'Specialists?\s*',
        r'Focus\s*', r'Location\s*', r'Office\b\s*:?\s*', r'Region\s*',
    ]
    for pat in noise_patterns:
        text = _re.sub(pat, ' ', text, flags=_re.IGNORECASE)
    # Remove city/location names that leak into role text
    locations = [
        'Bay Area', 'San Francisco', 'New York', 'Palo Alto', 'Boston',
        'London', 'Berlin', 'Tel Aviv', 'Singapore', 'Beijing', 'Shanghai',
        'Los Angeles', 'Chicago', 'Austin', 'Seattle', 'Menlo Park',
        'Mountain View', 'Toronto', 'Mumbai', 'Bangalore', 'Bengaluru',
    ]
    for loc in locations:
        text = _re.sub(_re.escape(loc), '', text, flags=_re.IGNORECASE)
    # Collapse whitespace and strip
    text = _re.sub(r'\s+', ' ', text).strip()
    # If what remains is too short or just a single word, likely not a useful role
    if len(text) < 3:
        return 'N/A'
    return text


def extract_name_role_pairs(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Extract (name, role) pairs from a team page using heuristics.
    Looks for common patterns: heading + paragraph, or structured divs.
    """
    pairs = []

    # Words that are definitely NOT person names
    BLOCKLIST = {
        # Cities / locations
        "san francisco", "new york", "palo alto", "los angeles", "boston",
        "chicago", "austin", "seattle", "menlo park", "silicon valley",
        "mountain view", "tel aviv", "london", "berlin", "toronto",
        "hong kong", "singapore", "beijing", "shanghai", "mumbai",
        # Navigation / UI
        "helpful tips", "read more", "learn more", "contact us", "get started",
        "sign up", "log in", "about us", "who we are", "what we do",
        "how it works", "join us", "careers", "open positions",
        "view all", "see more", "load more", "subscribe", "follow us",
        "main navigation", "quick links", "site map", "back top",
        "check availability", "founder resources", "submit application",
        # Section headers
        "our portfolio", "our approach", "our story", "our mission",
        "our values", "our focus", "our team", "our people",
        "our philosophy", "our leadership", "our customers",
        "our colleagues", "our communities", "our shared values",
        "latest news", "press releases", "recent investments",
        "portfolio companies", "featured",
        "investment team", "advisory board", "advisory team",
        "investment activity", "core principles",
        "company history", "putting our",
        # Cookie / privacy banners
        "functional cookies", "performance cookies", "targeting cookies",
        "marketing cookies", "privacy overview", "privacy policy",
        "terms of service", "cookie policy", "cookie settings",
        # Slogans / taglines
        "smarter together", "humbly open-minded", "challenging convention",
        "we invest in", "how we help", "our startups",
        "our blog", "connect with us", "links you may",
        "more from", "additional information",
        "your partner at", "citi ventures in",
        "summit partners news",
    }

    # Words that appear in job titles but NOT in person names
    JOB_TITLE_WORDS = {
        "officer", "manager", "director", "engineer", "specialist",
        "accountant", "analyst", "coordinator", "administrator",
        "president", "vice", "senior", "junior", "associate",
        "lead", "chief", "head", "staff", "principal",
        "marketing", "operations", "technology", "financial",
        "reporting", "portfolio", "accounting", "product",
        "investment", "full", "stack", "fund",
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
        lower = text.lower()
        if lower in BLOCKLIST:
            return False
        # Reject if ANY blocklist phrase is contained in the text
        for blocked in BLOCKLIST:
            if blocked in lower:
                return False
        # Reject if it looks like a job title (2+ job title words)
        lower_words = set(lower.split())
        title_overlap = lower_words & JOB_TITLE_WORDS
        if len(title_overlap) >= 2:
            return False
        # Reject if first word is a common non-name word
        NON_NAME_STARTERS = {
            "the", "a", "an", "our", "your", "my", "this", "that",
            "we", "how", "set", "more", "about", "meet",
        }
        if words[0].lower() in NON_NAME_STARTERS:
            return False
        # Each word should be capitalized and alphabetic (allow hyphens, dots, apostrophes, accents)
        for w in words:
            cleaned = w.replace("-", "").replace(".", "").replace("'", "").replace("\u2019", "")
            if not cleaned:
                return False
            if not cleaned[0].isupper():
                return False
            # Allow unicode letters (accented names like Jérémy)
            if not all(c.isalpha() for c in cleaned):
                return False
        # Reject single-character first or last names
        if len(words[0]) < 2 or len(words[-1]) < 2:
            return False
        return True

    def _role_is_actually_a_name(role_text: str) -> bool:
        """Detect off-by-one: role text is actually the next person's name."""
        if not role_text:
            return False
        # If role text passes looks_like_name AND doesn't contain any role keywords, it's a name
        if looks_like_name(role_text):
            role_lower = role_text.lower()
            if not any(kw in role_lower for kw in ROLE_KEYWORDS):
                return True
        return False

    # ── Helper: search siblings for role text (up to 3 levels deep) ──
    def _find_role_nearby(heading, require_keyword=True):
        """Search up to 3 siblings and the heading's parent for role-like text."""
        candidates = []
        # Collect up to 3 next siblings
        sib = heading.find_next_sibling()
        for _ in range(3):
            if sib is None:
                break
            candidates.append(sib)
            sib = sib.find_next_sibling()
        # Also search within the heading's parent container
        parent = heading.parent
        if parent:
            for child in parent.children:
                if child is not heading and hasattr(child, 'get_text'):
                    candidates.append(child)

        for elem in candidates:
            if not hasattr(elem, 'get_text'):
                continue
            candidate = elem.get_text(separator=" ", strip=True)
            candidate = _clean_role_text(candidate)
            if candidate == 'N/A' or len(candidate) >= 80:
                continue
            if _role_is_actually_a_name(candidate):
                continue
            if require_keyword:
                if any(kw in candidate.lower() for kw in ROLE_KEYWORDS):
                    return candidate
            else:
                if 3 < len(candidate) < 60:
                    return candidate
        return ""

    # ── Strategy 0: CSS class-based extraction ──
    TEAM_CSS_PATTERNS = re.compile(r'team|member|person|staff|bio|people', re.IGNORECASE)
    HEADING_TAGS = ["h2", "h3", "h4", "h5", "h6", "strong"]

    # Combine class and id matches
    css_matches = set(soup.find_all(True, attrs={"class": TEAM_CSS_PATTERNS}))
    css_matches.update(soup.find_all(True, attrs={"id": TEAM_CSS_PATTERNS}))

    for el in css_matches:
        # Look for a heading-like child for the name
        heading = el.find(HEADING_TAGS)
        if not heading:
            # Try <a> or <span> with class containing 'name'
            heading = el.find(True, attrs={"class": re.compile(r'name', re.IGNORECASE)})
        if not heading:
            continue
        name_text = heading.get_text(strip=True)
        if not looks_like_name(name_text):
            continue
        role_text = _find_role_nearby(heading, require_keyword=True)
        if not role_text:
            # Try relaxed: any short text that isn't a name
            role_text = _find_role_nearby(heading, require_keyword=False)
        pairs.append({"name": name_text, "role": role_text})

    # ── Strategy 1: Structured cards with headings + nearby role text ──
    for container_tag in ["div", "li", "article"]:
        for container in soup.find_all(container_tag):
            # Skip very large containers (page wrappers)
            if len(container.get_text()) > 20000:
                continue

            heading = container.find(HEADING_TAGS)
            if not heading:
                continue

            name_text = heading.get_text(strip=True)

            if not looks_like_name(name_text):
                continue

            # Look for role text nearby (up to 3 siblings deep)
            role_text = _find_role_nearby(heading, require_keyword=True)

            # Only accept if we found a role — otherwise it's probably not a team card
            if role_text:
                pairs.append({"name": name_text, "role": role_text})

    # Strategy 2: If strategy 1 found nothing, try names WITHOUT role requirement
    # but only if the page URL strongly suggests it's a team page
    if not pairs:
        for container_tag in ["div", "li", "article"]:
            for container in soup.find_all(container_tag):
                if len(container.get_text()) > 20000:
                    continue
                heading = container.find(HEADING_TAGS)
                if not heading:
                    continue
                name_text = heading.get_text(strip=True)
                if not looks_like_name(name_text):
                    continue
                # Check for any nearby role-ish text (relaxed — no keyword requirement)
                role_text = _find_role_nearby(heading, require_keyword=False)
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
        max_concurrent: int = 10,
        headless: bool = True,
        force_recrawl: bool = False,
        seen_file: str = "data/seen_domains.txt",
        skip_enrichment: bool = False,
        stale_days: int = 7,
    ):
        self.target_file = target_file
        self.output_file = output_file
        self.max_concurrent = max_concurrent
        self.headless = headless
        self.force_recrawl = force_recrawl
        self.seen_file = seen_file
        self.stale_days = stale_days
        self.all_contacts: List[InvestorLead] = []
        self.skip_enrichment = skip_enrichment
        self.email_validator = EmailValidator()
        self.email_guesser = EmailGuesser(concurrency=10)
        self.scorer = LeadScorer("config/scoring.yaml")
        self.csv_writer = CSVWriter("data")

    def _checkpoint_path(self) -> str:
        return self.output_file.replace('.csv', '_checkpoint.csv')

    def _save_checkpoint(self):
        """Write all contacts to a checkpoint CSV after each batch."""
        path = self._checkpoint_path()
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'role', 'email', 'linkedin', 'fund_name', 'fund_url', 'source_page'])
            for c in self.all_contacts:
                writer.writerow([
                    c.name, c.role, c.email, c.linkedin,
                    c.fund, c.website, getattr(c, 'source', ''),
                ])
        logger.info(f"  💾 Checkpoint: {len(self.all_contacts)} contacts → {path}")

    def _load_checkpoint(self):
        """Load contacts from checkpoint CSV (crash recovery)."""
        path = self._checkpoint_path()
        if not os.path.exists(path):
            return
        recovered = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                lead = InvestorLead(
                    name=row.get('name', ''),
                    role=row.get('role', ''),
                    email=row.get('email', 'N/A'),
                    linkedin=row.get('linkedin', 'N/A'),
                    fund=row.get('fund_name', ''),
                    website=row.get('fund_url', ''),
                )
                recovered.append(lead)
        self.all_contacts = recovered
        logger.info(f"  🔄 Recovered {len(recovered)} contacts from checkpoint")

    def _load_seen(self) -> set:
        """Load previously crawled domains from seen_domains.txt (legacy)."""
        seen = set()
        try:
            with open(self.seen_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        seen.add(line)
        except FileNotFoundError:
            pass
        return seen

    def _save_seen(self, domains: List[str]):
        """Write freshly crawled domains to seen file (replaces, not appends)."""
        os.makedirs("data", exist_ok=True)
        # Merge with existing so we don't lose history
        existing = self._load_seen()
        existing.update(domains)
        with open(self.seen_file, "w") as f:
            for domain in sorted(existing):
                f.write(domain + "\n")

    def _load_targets(self) -> List[str]:
        """Load target URLs from file, applying freshness-based filtering."""
        targets = []
        with open(self.target_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    targets.append(line)
        targets = list(set(targets))  # Deduplicate within file

        if self.force_recrawl:
            return targets

        # Freshness-based filtering: skip domains crawled within stale_days
        from enrichment.incremental import CrawlStateManager
        freshness = CrawlStateManager(stale_days=self.stale_days)

        # Seed CrawlStateManager from seen_domains.txt timestamps
        # seen_domains.txt has no timestamps, so treat entries as "last crawled
        # at file mtime" — if the file is older than stale_days, re-crawl everything
        seen = self._load_seen()
        if seen:
            import os
            from datetime import datetime, timezone, timedelta
            try:
                mtime = os.path.getmtime(self.seen_file)
                file_age = datetime.now(timezone.utc) - datetime.fromtimestamp(mtime, tz=timezone.utc)
                if file_age > timedelta(days=self.stale_days):
                    logger.info(f"  📅  seen_domains.txt is {file_age.days}d old (>{self.stale_days}d) — all domains are stale, re-crawling")
                    return targets
                else:
                    # File is recent — filter out seen domains
                    before = len(targets)
                    targets = [t for t in targets if t not in seen]
                    skipped = before - len(targets)
                    if skipped:
                        logger.info(f"  ⏭️  Skipping {skipped} domains crawled within {self.stale_days}d (use --force-recrawl to override)")
            except Exception:
                pass

        return targets

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

    async def _extract_from_page(self, page: Page, url: str, fund_name: str, fund_url: str) -> List[InvestorLead]:
        """Extract contacts from a single page."""
        contacts = []

        try:
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            page_text = soup.get_text(separator=" ")

            # Extract data using comprehensive extraction
            emails = extract_emails_from_html(soup, page_text)
            linkedin_urls = extract_linkedin_urls(soup)
            name_roles = extract_name_role_pairs(soup)

            # Build contact objects
            for pair in name_roles:
                # Try to match a LinkedIn URL (by name proximity in HTML)
                linkedin = "N/A"
                name_lower = pair["name"].lower().replace(" ", "")
                for li_url in linkedin_urls:
                    if name_lower[:6] in li_url.lower().replace("-", ""):
                        linkedin = li_url
                        break

                contact = InvestorLead(
                    name=pair["name"],
                    role=pair["role"] or "N/A",
                    fund=fund_name,
                    website=fund_url,
                    source=url,
                    linkedin=linkedin,
                    scraped_at=datetime.now().isoformat(),
                )
                contacts.append(contact)

            # If we found emails but no name-role pairs, still record them
            if emails and not name_roles:
                for email in emails:
                    contacts.append(InvestorLead(
                        name="Unknown",
                        email=email,
                        fund=fund_name,
                        website=fund_url,
                        source=url,
                        scraped_at=datetime.now().isoformat(),
                    ))

            # Smart email-to-contact matching: score each email against each
            # contact name and assign the best match (not random sequential)
            if emails and name_roles:
                unassigned_emails = list(emails)
                for contact in contacts:
                    if contact.email != "N/A":
                        continue
                    best_email = None
                    best_score = 0.0
                    for email in unassigned_emails:
                        score = _match_email_to_name(email, contact.name)
                        if score > best_score:
                            best_score = score
                            best_email = email
                    if best_email and best_score >= 0.3:
                        contact.email = best_email
                        unassigned_emails.remove(best_email)

        except Exception as e:
            logger.error(f"  ❌ Extraction error on {url}: {e}")

        return contacts

    async def _scrape_linkedin_email(self, page: Page, linkedin_url: str) -> str:
        """
        Attempt to extract a contact email from a public LinkedIn profile page.
        LinkedIn rarely exposes emails directly, but some profiles include them
        in the contact info section visible without login, or in the page source.
        Returns the email string if found, else "N/A".
        """
        try:
            await page.goto(linkedin_url, wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(random.uniform(1.0, 2.0))

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            page_text = soup.get_text(separator=" ")

            emails = extract_emails(page_text)
            if emails:
                return emails[0]

            raw_emails = extract_emails(html)
            if raw_emails:
                return raw_emails[0]

        except Exception as e:
            logger.debug(f"  LinkedIn email scrape failed for {linkedin_url}: {e}")

        return "N/A"

    async def _linkedin_fallback(self, page: Page, contacts: List[InvestorLead]) -> List[InvestorLead]:
        """
        For contacts that have a LinkedIn URL but no email, attempt to scrape
        the public profile page for a contact email.
        Caps at 5 attempts per fund to avoid rate-limiting.
        """
        candidates = [
            c for c in contacts
            if c.email in ("N/A", "N/A (invalid)")
            and c.linkedin not in ("N/A", "", None)
            and "linkedin.com/in/" in c.linkedin
        ]

        for contact in candidates[:5]:
            email = await self._scrape_linkedin_email(page, contact.linkedin)
            if email != "N/A":
                contact.email = email
                logger.info(f"  🔗 LinkedIn email found for {contact.name}: {email}")
            await asyncio.sleep(random.uniform(2.0, 4.0))  # Polite delay between profiles

        return contacts

    async def _crawl_fund(self, browser: Browser, fund_url: str) -> List[InvestorLead]:
        """Crawl a single VC fund website with a 30s hard timeout."""
        fund_name = urlparse(fund_url).netloc.replace("www.", "").split(".")[0].title()
        contacts = []

        async def _do_crawl():
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"
            )
            page = await ctx.new_page()

            logger.info(f"  🌐 Visiting {fund_url}")
            try:
                await page.goto(fund_url, wait_until="domcontentloaded", timeout=15000)
            except Exception:
                logger.warning(f"  ⏳ Timeout on {fund_url}, continuing...")
                await ctx.close()
                return []

            await asyncio.sleep(random.uniform(1.0, 2.5))

            team_urls = await self._find_team_pages(page, fund_url)

            if not team_urls:
                for path in ["/team", "/about", "/people", "/about-us", "/our-team",
                             "/leadership", "/who-we-are", "/about/team",
                             "/partners", "/our-people"]:
                    team_urls.append(urljoin(fund_url, path))

            logger.info(f"  📄 Found {len(team_urls)} potential team pages")

            found = []
            for team_url in team_urls[:8]:  # Try up to 8 pages
                try:
                    await page.goto(team_url, wait_until="networkidle", timeout=15000)
                    await asyncio.sleep(1.0)  # Post-load delay for JS rendering

                    title = await page.title()
                    if "404" in title.lower() or "not found" in title.lower():
                        continue

                    page_contacts = await self._extract_from_page(
                        page, team_url, fund_name, fund_url
                    )

                    # Pagination: click "Load More" / "Show More" / "View All" buttons
                    for _ in range(3):  # Up to 3 clicks
                        clicked = False
                        for btn_text in ["Load More", "Show More", "View All", "See All", "Show all"]:
                            try:
                                btn = page.get_by_role("button", name=btn_text)
                                if await btn.count() > 0 and await btn.first.is_visible():
                                    await btn.first.click()
                                    clicked = True
                                    await asyncio.sleep(2.0)
                                    extra = await self._extract_from_page(
                                        page, team_url, fund_name, fund_url
                                    )
                                    page_contacts.extend(extra)
                                    break
                            except Exception:
                                continue
                        # Also try generic link/anchor with those texts
                        if not clicked:
                            for btn_text in ["Load More", "Show More", "View All", "See All"]:
                                try:
                                    link = page.get_by_text(btn_text, exact=False)
                                    if await link.count() > 0 and await link.first.is_visible():
                                        await link.first.click()
                                        clicked = True
                                        await asyncio.sleep(2.0)
                                        extra = await self._extract_from_page(
                                            page, team_url, fund_name, fund_url
                                        )
                                        page_contacts.extend(extra)
                                        break
                                except Exception:
                                    continue
                        if not clicked:
                            break

                    # Check for ?page=2 style pagination links
                    try:
                        html = await page.content()
                        soup_pg = BeautifulSoup(html, "html.parser")
                        for a in soup_pg.find_all("a", href=True):
                            href = a["href"]
                            full = urljoin(team_url, href)
                            if urlparse(full).netloc == urlparse(team_url).netloc:
                                if re.search(r'[?&]page=\d+', full):
                                    try:
                                        await page.goto(full, wait_until="networkidle", timeout=10000)
                                        await asyncio.sleep(1.0)
                                        extra = await self._extract_from_page(
                                            page, full, fund_name, fund_url
                                        )
                                        page_contacts.extend(extra)
                                    except Exception:
                                        pass
                    except Exception:
                        pass

                    found.extend(page_contacts)

                    if page_contacts:
                        logger.info(f"  ✅ Extracted {len(page_contacts)} contacts from {team_url}")

                except Exception as e:
                    logger.warning(f"  ⚠️ Failed to extract from {team_url}: {e}")
                    continue

            # LinkedIn fallback disabled — causes hangs due to rate-limiting delays
            # if found:
            #     found = await self._linkedin_fallback(page, found)

            # Dedup contacts by name (case-insensitive) before returning
            seen_names = set()
            deduped = []
            for c in found:
                key = c.name.lower().strip()
                if key not in seen_names:
                    seen_names.add(key)
                    deduped.append(c)
            if len(found) != len(deduped):
                logger.info(f"  🔄 Deduped {len(found)} → {len(deduped)} contacts for {fund_name}")
            found = deduped

            await ctx.close()
            return found

        try:
            contacts = await asyncio.wait_for(_do_crawl(), timeout=45.0)
        except asyncio.TimeoutError:
            logger.warning(f"  ⏱️ Hard timeout (45s) reached for {fund_url}, skipping")
        except Exception as e:
            logger.error(f"  ❌ Failed to crawl {fund_url}: {e}")

        return contacts

    async def _enrich_and_save(self):
        """Run enrichment pipeline and save via CSVWriter (mirrors engine.py)."""
        logger.info(f"  📧  Validating {len(self.all_contacts)} emails...")
        for contact in self.all_contacts:
            result = self.email_validator.validate(contact.email)
            if result["quality"] == "invalid":
                contact.email = "N/A (invalid)"
            elif result["is_disposable"]:
                contact.email = f"{contact.email} ⚠️ (disposable)"

        logger.info("  ✉️  Guessing emails for contacts without one...")
        self.all_contacts = await self.email_guesser.guess_batch(self.all_contacts)
        guesser_stats = self.email_guesser.stats
        logger.info(f"  ✉️  Guesser: {guesser_stats['found']} found / {guesser_stats['attempted']} attempted")

        logger.info("  📊  Scoring leads...")
        self.all_contacts = self.scorer.score_batch(self.all_contacts)

        logger.info("  💾  Writing output...")
        self.csv_writer.write_master(self.all_contacts)
        logger.info(f"💾 Saved {len(self.all_contacts)} contacts via CSVWriter")

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

            # Process funds in batches to avoid overwhelming browser
            batch_size = self.max_concurrent
            total = len(targets)
            for batch_start in range(0, total, batch_size):
                batch = targets[batch_start:batch_start + batch_size]
                batch_end = min(batch_start + batch_size, total)
                logger.info(f"  📦 Batch {batch_start // batch_size + 1}: funds {batch_start + 1}-{batch_end}/{total}")

                tasks = [self._crawl_fund(browser, url) for url in batch]
                try:
                    results = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=batch_size * 50.0,  # ~50s per fund in batch
                    )
                    for result in results:
                        if isinstance(result, list):
                            self.all_contacts.extend(result)
                except asyncio.TimeoutError:
                    logger.warning(f"  ⏱️ Batch timeout — moving to next batch")

                contacts_so_far = len(self.all_contacts)
                logger.info(f"  📊 Running total: {contacts_so_far} contacts")

                # Incremental checkpoint — save raw contacts after each batch
                self._save_checkpoint()

            await browser.close()

        # Recover from checkpoint if all_contacts is empty (crash recovery)
        if not self.all_contacts:
            self._load_checkpoint()

        # Persist seen domains so next run skips them
        self._save_seen(targets)

        # Enrich and save (skip if engine will handle enrichment)
        if not self.skip_enrichment:
            await self._enrich_and_save()

        # Print summary
        funds_with_contacts = len(set(c.website for c in self.all_contacts if c.name))
        total_emails = len([c for c in self.all_contacts if c.email and c.email != "N/A"])
        total_linkedin = len([c for c in self.all_contacts if c.linkedin and c.linkedin != "N/A"])
        scorer_stats = self.scorer.stats

        logger.info(f"""
============================================================
  📊  DEEP CRAWL SUMMARY
============================================================
  📝  Total contacts: {len(self.all_contacts)}
  🏢  Funds with contacts: {funds_with_contacts}/{len(targets)}
  📧  Emails found: {total_emails}
  🔗  LinkedIn profiles: {total_linkedin}
  📈  Avg score: {scorer_stats.get('avg_score', 0)}
  🔴  HOT leads: {scorer_stats.get('hot_count', 0)}
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
