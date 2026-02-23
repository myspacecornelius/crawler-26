"""
CRAWL — HTTP-Based Discovery Engine
Replaces the Playwright-based DDG searcher with lightweight aiohttp requests.
Much faster, no bot detection, no browser overhead.
Uses DuckDuckGo Lite HTML endpoint which is designed for simple HTTP clients.
"""

import asyncio
import logging
import random
import re
import urllib.parse
from typing import List, Set
from urllib.parse import urlparse

import aiohttp

logger = logging.getLogger(__name__)

# Domains to always exclude (aggregators, social, search engines)
DEFAULT_IGNORE = {
    "linkedin.com", "twitter.com", "x.com", "facebook.com", "instagram.com",
    "crunchbase.com", "angellist.com", "angel.co", "pitchbook.com",
    "dealroom.co", "techcrunch.com", "medium.com", "substack.com",
    "youtube.com", "reddit.com", "wikipedia.org", "google.com",
    "bing.com", "duckduckgo.com", "yahoo.com", "amazon.com",
    "github.com", "stackoverflow.com", "quora.com",
    "tracxn.com", "wellfound.com", "cbinsights.com",
    "sec.gov", "bloomberg.com", "wsj.com", "forbes.com",
    "nytimes.com", "reuters.com", "ft.com",
}


def _is_valid_vc_domain(url: str, ignore_domains: Set[str]) -> bool:
    """Check if a URL likely belongs to an actual VC fund website."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        if not domain or len(domain) < 4:
            return False

        for ignored in ignore_domains:
            if ignored in domain:
                return False

        # Reject country TLDs unlikely to be VC sites
        if domain.endswith((".cn", ".jp", ".ru", ".ir")):
            return False

        # Reject obvious non-VC patterns
        if any(x in domain for x in ("gov.", ".gov", ".edu", "news.", "blog.")):
            return False

        return True
    except Exception:
        return False


def _get_base_url(url: str) -> str:
    """Extract protocol + domain from a URL."""
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return url


def _extract_urls_from_html(html: str) -> List[str]:
    """Extract real URLs from DuckDuckGo Lite HTML response."""
    urls = []

    # DDG Lite uses uddg= parameter in links
    uddg_pattern = r'uddg=([^&"\']+)'
    for match in re.finditer(uddg_pattern, html):
        try:
            decoded = urllib.parse.unquote(match.group(1))
            if decoded.startswith("http"):
                urls.append(decoded)
        except Exception:
            pass

    # Also look for direct href links
    href_pattern = r'href="(https?://[^"]+)"'
    for match in re.finditer(href_pattern, html):
        url = match.group(1)
        if "duckduckgo.com" not in url and url.startswith("http"):
            urls.append(url)

    return urls


async def http_discover(
    queries: List[str],
    target_count: int = 500,
    ignore_domains: Set[str] = None,
    max_concurrent: int = 3,
) -> Set[str]:
    """
    Run search queries via HTTP (no browser) and return discovered VC domains.

    Uses DuckDuckGo Lite (html.duckduckgo.com/html/) which is designed for
    simple HTTP clients and doesn't require JavaScript.
    """
    if ignore_domains is None:
        ignore_domains = DEFAULT_IGNORE

    discovered = set()
    sem = asyncio.Semaphore(max_concurrent)

    async def _search_query(session: aiohttp.ClientSession, query: str) -> List[str]:
        """Execute a single search query and return valid VC domains."""
        async with sem:
            try:
                encoded = urllib.parse.quote_plus(query)
                url = f"https://html.duckduckgo.com/html/?q={encoded}"

                headers = {
                    "User-Agent": random.choice([
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0",
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121.0.0.0",
                    ]),
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                }

                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        logger.debug(f"  DDG HTTP {resp.status} for: {query[:50]}")
                        return []

                    html = await resp.text()

                    # Check for CAPTCHA
                    if "robot" in html.lower() or "captcha" in html.lower():
                        logger.warning(f"  🚨  DDG rate-limited, backing off")
                        await asyncio.sleep(30)
                        return []

                    raw_urls = _extract_urls_from_html(html)
                    valid = []
                    for raw_url in raw_urls:
                        if _is_valid_vc_domain(raw_url, ignore_domains):
                            base = _get_base_url(raw_url)
                            valid.append(base)

                    return valid

            except Exception as e:
                logger.debug(f"  Discovery query failed: {e}")
                return []

    logger.info(f"  🔍  HTTP discovery: {len(queries)} queries targeting {target_count} domains")

    async with aiohttp.ClientSession() as session:
        for i, query in enumerate(queries):
            if len(discovered) >= target_count:
                break

            results = await _search_query(session, query)
            new = 0
            for domain in results:
                if domain not in discovered:
                    discovered.add(domain)
                    new += 1

            if new > 0 or (i + 1) % 10 == 0:
                logger.info(f"  🔎  [{i+1}/{len(queries)}] +{new} domains (total: {len(discovered)}/{target_count})")

            # Polite delay between queries
            await asyncio.sleep(random.uniform(1.0, 3.0))

    logger.info(f"  ✅  HTTP discovery complete: {len(discovered)} unique domains")
    return discovered
