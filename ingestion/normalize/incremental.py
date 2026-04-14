"""
Incremental Crawl — freshness tracking and stale domain filtering.

Directly adapted from crawler-26's enrichment/incremental.py.
Domain-agnostic; only field name changed (leads_found → offers_found).
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DEFAULT_STALE_DAYS = 7


class CrawlStateManager:
    """
    Manages per-domain crawl state.
    Tracks when each domain was last crawled and how many offers were found.
    """

    def __init__(self, stale_days: int = DEFAULT_STALE_DAYS):
        self.stale_days = stale_days
        self._cache: Dict[str, datetime] = {}

    @staticmethod
    def _normalize_domain(url: str) -> str:
        if not url.startswith("http"):
            url = "https://" + url
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        return domain.lower().replace("www.", "").strip("/")

    def is_stale(self, url: str) -> bool:
        domain = self._normalize_domain(url)
        last = self._cache.get(domain)
        if last is None:
            return True
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.stale_days)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        return last < cutoff

    def filter_stale(self, urls: List[str]) -> Tuple[List[str], List[str]]:
        """Split URLs into (stale, fresh) lists."""
        stale, fresh = [], []
        for url in urls:
            (stale if self.is_stale(url) else fresh).append(url)
        return stale, fresh

    def mark_crawled(self, url: str, offers_found: int = 0):
        domain = self._normalize_domain(url)
        self._cache[domain] = datetime.now(timezone.utc)

    def mark_batch_crawled(self, results: List[dict]):
        for item in results:
            self.mark_crawled(
                url=item["url"],
                offers_found=item.get("offers_found", 0),
            )

    def summary(self) -> dict:
        now = datetime.now(timezone.utc)
        total = len(self._cache)
        stale = sum(
            1 for ts in self._cache.values()
            if (ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts)
            < now - timedelta(days=self.stale_days)
        )
        return {
            "total_domains": total,
            "stale_domains": stale,
            "fresh_domains": total - stale,
        }
