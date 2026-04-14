"""
Demo Offers Platform — Ingestion Pipeline CLI

Usage:
    python -m ingestion.main                   # Run full pipeline
    python -m ingestion.main --discover-only   # Only discover sources
    python -m ingestion.main --dry-run         # No writes
"""

import asyncio
import argparse
import logging
import time
from pathlib import Path

from ingestion.discovery.multi_searcher import discover_offer_sources
from ingestion.crawl.offer_crawler import OfferCrawler
from ingestion.normalize.dedup import OfferDeduplicator
from ingestion.normalize.scoring import OfferScorer
from ingestion.normalize.incremental import CrawlStateManager
from ingestion.sources.aggregator import OfferSourceAggregator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingestion")


class IngestionPipeline:
    """
    Orchestrates the full offer ingestion pipeline:
    1. Source aggregation (deterministic directories)
    2. Discovery (search-engine based source finding)
    3. Crawling (visit pages, extract offer data)
    4. Normalization (dedup, scoring)
    5. Output (write to Supabase or local store)
    """

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.crawl_state = CrawlStateManager(
            stale_days=getattr(args, "stale_days", 7)
        )
        self.raw_offers: list[dict] = []

    async def run(self):
        start = time.time()
        self._print_banner()

        # ── 1. Aggregate known sources ──
        if not self.args.discover_only:
            aggregator = OfferSourceAggregator()
            source_urls = await aggregator.aggregate()
            logger.info(f"Aggregator found {len(source_urls)} source URLs")

        # ── 2. Discovery (optional) ──
        if self.args.discover or self.args.discover_only:
            discovered = await discover_offer_sources(
                target_count=getattr(self.args, "target_count", 500),
            )
            logger.info(f"Discovery found {len(discovered)} domains")
            if self.args.discover_only:
                elapsed = time.time() - start
                logger.info(f"Discovery-only complete in {elapsed:.1f}s")
                return

        # ── 3. Crawl ──
        if not self.args.discover_only:
            crawler = OfferCrawler(
                max_concurrent=getattr(self.args, "concurrency", 5),
                headless=getattr(self.args, "headless", True),
                stale_days=getattr(self.args, "stale_days", 7),
            )
            self.raw_offers = await crawler.crawl_sources(source_urls if not self.args.discover_only else [])
            logger.info(f"Crawled {len(self.raw_offers)} raw offers")

        # ── 4. Normalize ──
        if self.raw_offers:
            # Dedup
            dedup = OfferDeduplicator()
            self.raw_offers = dedup.deduplicate(self.raw_offers)

            # Score
            scorer = OfferScorer()
            self.raw_offers = scorer.score_batch(self.raw_offers)

        # ── 5. Output ──
        if self.raw_offers and not self.args.dry_run:
            from ingestion.output.supabase_writer import write_offers
            await write_offers(self.raw_offers)
            logger.info(f"Wrote {len(self.raw_offers)} offers to store")
        elif self.args.dry_run:
            logger.info(f"DRY RUN — {len(self.raw_offers)} offers would be written")

        elapsed = time.time() - start
        logger.info(f"Pipeline complete in {elapsed:.1f}s — {len(self.raw_offers)} offers")

    def _print_banner(self):
        print()
        print("  ╔══════════════════════════════════════════╗")
        print("  ║  📦  Demo Offers — Ingestion Pipeline    ║")
        print("  ╚══════════════════════════════════════════╝")
        print()


def main():
    parser = argparse.ArgumentParser(description="Demo Offers Ingestion Pipeline")
    parser.add_argument("--discover", action="store_true", help="Run source discovery")
    parser.add_argument("--discover-only", action="store_true", help="Only discover, don't crawl")
    parser.add_argument("--dry-run", action="store_true", help="Don't write output")
    parser.add_argument("--headless", action="store_true", default=True, help="Headless browser")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent crawlers")
    parser.add_argument("--stale-days", type=int, default=7, help="Re-crawl threshold")
    parser.add_argument("--target-count", type=int, default=500, help="Discovery target")
    args = parser.parse_args()

    pipeline = IngestionPipeline(args)
    asyncio.run(pipeline.run())


if __name__ == "__main__":
    main()
