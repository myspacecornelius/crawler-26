"""
Multi-Engine Offer Source Discovery

Adapted from crawler-26's multi_searcher. Queries search engines to find
pages that list B2B demo incentives, then extracts base domains.

Engines: DuckDuckGo (no key), Google (SerpAPI), Bing, Brave.
"""

import asyncio
import logging
import os
import random
import re
import urllib.parse
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import aiohttp

logger = logging.getLogger(__name__)

# Domains that are never offer sources
IGNORE_DOMAINS = {
    "linkedin.com", "twitter.com", "x.com", "facebook.com", "instagram.com",
    "youtube.com", "reddit.com", "wikipedia.org", "google.com",
    "bing.com", "duckduckgo.com", "yahoo.com", "amazon.com",
    "github.com", "stackoverflow.com", "quora.com",
    "brave.com", "search.brave.com", "serpapi.com",
}

# Demo-incentive oriented search queries
DEFAULT_QUERIES = [
    "B2B demo incentive gift card",
    "get a gift card for taking a software demo",
    "vendor demo reward program",
    "SaaS demo incentive offer",
    "enterprise software demo gift card",
    "B2B product demo reward",
    "demo incentive marketplace",
    "get paid to take a software demo",
    "software evaluation incentive",
    "demo reward B2B SaaS",
    "vendor sponsored demo offer",
    "free gift card software demo B2B",
]


def _is_valid_source_domain(url: str, ignore: Set[str]) -> bool:
    """Check if a URL could be an offer source (not a social/news site)."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")
        if not domain or len(domain) < 4:
            return False
        for ign in ignore:
            if ign in domain:
                return False
        if domain.endswith((".gov", ".edu", ".mil")):
            return False
        return True
    except Exception:
        return False


def _get_base_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return url


# ── Search Engine Backends ───────────────────────

class SearchEngine(ABC):
    name: str = "base"
    requires_key: bool = False

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @abstractmethod
    async def search(self, session: aiohttp.ClientSession, query: str) -> List[str]:
        ...


class DuckDuckGoEngine(SearchEngine):
    name = "duckduckgo"

    async def search(self, session: aiohttp.ClientSession, query: str) -> List[str]:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121.0.0.0",
            "Accept": "text/html",
        }
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()
                if "robot" in html.lower() or "captcha" in html.lower():
                    await asyncio.sleep(30)
                    return []
                return self._extract_urls(html)
        except Exception:
            return []

    @staticmethod
    def _extract_urls(html: str) -> List[str]:
        urls = []
        for match in re.finditer(r'uddg=([^&"\']+)', html):
            try:
                decoded = urllib.parse.unquote(match.group(1))
                if decoded.startswith("http"):
                    urls.append(decoded)
            except Exception:
                pass
        return urls


class GoogleSerpAPIEngine(SearchEngine):
    name = "google"
    requires_key = True

    async def search(self, session: aiohttp.ClientSession, query: str) -> List[str]:
        if not self.api_key:
            return []
        params = {"q": query, "api_key": self.api_key, "engine": "google", "num": 30}
        try:
            async with session.get(
                "https://serpapi.com/search.json", params=params,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [r["link"] for r in data.get("organic_results", []) if "link" in r]
        except Exception:
            return []


class BingSearchEngine(SearchEngine):
    name = "bing"
    requires_key = True

    async def search(self, session: aiohttp.ClientSession, query: str) -> List[str]:
        if not self.api_key:
            return []
        try:
            async with session.get(
                "https://api.bing.microsoft.com/v7.0/search",
                headers={"Ocp-Apim-Subscription-Key": self.api_key},
                params={"q": query, "count": 30},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [p["url"] for p in data.get("webPages", {}).get("value", []) if "url" in p]
        except Exception:
            return []


class BraveSearchEngine(SearchEngine):
    name = "brave"
    requires_key = True

    async def search(self, session: aiohttp.ClientSession, query: str) -> List[str]:
        if not self.api_key:
            return []
        try:
            async with session.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"X-Subscription-Token": self.api_key, "Accept": "application/json"},
                params={"q": query, "count": 20},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [r["url"] for r in data.get("web", {}).get("results", []) if "url" in r]
        except Exception:
            return []


# ── Engine Registry ──────────────────────────────

ENGINE_CLASSES: Dict[str, type] = {
    "duckduckgo": DuckDuckGoEngine,
    "google": GoogleSerpAPIEngine,
    "bing": BingSearchEngine,
    "brave": BraveSearchEngine,
}


def _build_engines(config: dict | None = None) -> List[SearchEngine]:
    config = config or {}
    engines = []
    for name, cls in ENGINE_CLASSES.items():
        cfg = config.get(name, {})
        if not cfg.get("enabled", name == "duckduckgo"):
            continue
        api_key = cfg.get("api_key") or os.environ.get(f"{name.upper()}_API_KEY")
        if cls.requires_key and not api_key:
            continue
        engines.append(cls(api_key=api_key))
    if not engines:
        engines.append(DuckDuckGoEngine())
    return engines


# ── Public API ───────────────────────────────────

async def discover_offer_sources(
    queries: List[str] | None = None,
    target_count: int = 500,
    ignore_domains: Set[str] | None = None,
    engine_config: dict | None = None,
    max_concurrent: int = 5,
) -> Set[str]:
    """
    Search for pages that list B2B demo incentives.
    Returns a set of base URLs (domains).
    """
    if queries is None:
        queries = DEFAULT_QUERIES
    if ignore_domains is None:
        ignore_domains = IGNORE_DOMAINS

    engines = _build_engines(engine_config)
    discovered: Set[str] = set()
    sem = asyncio.Semaphore(max_concurrent)

    logger.info(f"Discovery: {len(engines)} engines, {len(queries)} queries, target={target_count}")

    async def _run_query(engine: SearchEngine, query: str):
        async with sem:
            async with aiohttp.ClientSession() as session:
                urls = await engine.search(session, query)
            for url in urls:
                if _is_valid_source_domain(url, ignore_domains):
                    discovered.add(_get_base_url(url))

    batch_size = len(engines) * 3
    idx = 0
    while idx < len(queries) and len(discovered) < target_count:
        tasks = []
        end = min(idx + batch_size, len(queries))
        for i in range(idx, end):
            engine = engines[i % len(engines)]
            tasks.append(_run_query(engine, queries[i]))
        await asyncio.gather(*tasks)
        idx = end
        await asyncio.sleep(random.uniform(1.5, 3.0))

    logger.info(f"Discovery complete: {len(discovered)} unique domains")
    return discovered
