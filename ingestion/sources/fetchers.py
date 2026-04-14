"""
Offer Directory Fetchers — HTTP-based sources for demo incentive pages.

Adapted from crawler-26's directory_fetchers.py pattern: a registry of
async fetcher functions that pull from public data sources.

Currently a starter set — add new fetchers as offer source pages are identified.
"""

import asyncio
import logging
from typing import List

import aiohttp

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36"
DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=20)


# ── Fetcher implementations ─────────────────────

async def _fetch_known_offer_pages(session: aiohttp.ClientSession) -> List[str]:
    """
    Seed list of known pages that aggregate demo incentives.
    These are manually curated starting points.
    """
    return [
        # Placeholder URLs — replace with real sources as discovered
        # "https://example.com/demo-incentives",
    ]


# ── Aggregation ──────────────────────────────────

_FETCHERS = [
    ("Known Pages", _fetch_known_offer_pages),
]


async def fetch_all_offer_directories() -> List[str]:
    """
    Run all directory fetchers concurrently.
    Returns a deduplicated list of source URLs to crawl.
    """
    all_urls: List[str] = []

    async with aiohttp.ClientSession(
        headers={"User-Agent": USER_AGENT}
    ) as session:
        tasks = [fetcher(session) for _, fetcher in _FETCHERS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for (name, _), result in zip(_FETCHERS, results):
            if isinstance(result, Exception):
                logger.warning(f"Fetcher '{name}' failed: {result}")
            elif isinstance(result, list):
                all_urls.extend(result)

    # Deduplicate
    unique = list(set(all_urls))
    logger.info(f"Directory fetchers: {len(unique)} unique source URLs")
    return unique
