"""
Offer Source Aggregator

Adapted from crawler-26's sources/aggregator.py. Same orchestration pattern:
multiple sources → concurrent fetch → dedup → unified list of source URLs.
"""

import asyncio
import logging
from typing import List, Set

from ingestion.sources.fetchers import fetch_all_offer_directories

logger = logging.getLogger(__name__)


class OfferSourceAggregator:
    """Aggregates offer source URLs from multiple deterministic sources."""

    def __init__(self):
        self._seen: Set[str] = set()
        self._stats = {"directories": 0, "total": 0}

    async def aggregate(self) -> List[str]:
        """Run all source collectors and return deduplicated source URLs."""
        logger.info("Running offer source aggregation")

        # Source 1: Known offer directories
        try:
            dir_urls = await fetch_all_offer_directories()
            for url in dir_urls:
                if url not in self._seen:
                    self._seen.add(url)
            self._stats["directories"] = len(dir_urls)
        except Exception as e:
            logger.warning(f"Directory fetch failed: {e}")

        self._stats["total"] = len(self._seen)
        logger.info(f"Aggregator: {len(self._seen)} unique source URLs")
        return list(self._seen)

    @property
    def stats(self) -> dict:
        return dict(self._stats)
