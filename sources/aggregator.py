"""
CRAWL — Source Aggregator
Orchestrates multiple lead sources into a unified pipeline.
Sources: seed database, GitHub VC lists, HTTP-based discovery.
This is the primary lead generation engine — deterministic and reliable.
"""

import asyncio
import logging
from typing import List
from datetime import datetime

from adapters.base import InvestorLead
from sources.seed_db import load_seed_leads

logger = logging.getLogger(__name__)


class SourceAggregator:
    """
    Aggregates investor leads from multiple deterministic sources.
    Unlike browser-based scraping, these sources are reliable and fast.
    """

    def __init__(self):
        self.all_leads: List[InvestorLead] = []
        self._seen_names: set = set()
        self._stats = {
            "seed_db": 0,
            "github_lists": 0,
            "http_directories": 0,
            "total_deduped": 0,
        }

    def _dedup_add(self, leads: List[InvestorLead], source_label: str) -> int:
        """Add leads, deduplicating by normalized name. Returns count of new leads added."""
        added = 0
        for lead in leads:
            key = lead.name.strip().lower()
            if key and key not in self._seen_names:
                self._seen_names.add(key)
                self.all_leads.append(lead)
                added += 1
        self._stats[source_label] = added
        return added

    async def aggregate(self) -> List[InvestorLead]:
        """
        Run all source collectors and return deduplicated leads.
        """
        print(f"\n{'='*60}")
        print("  📡  SOURCE AGGREGATOR")
        print(f"{'='*60}\n")

        # ── Source 1: Curated seed database ──
        seed_leads = load_seed_leads()
        seed_count = self._dedup_add(seed_leads, "seed_db")
        print(f"  📂  Seed database: {seed_count} leads")

        # ── Source 2: GitHub VC lists (HTTP-based, no browser) ──
        try:
            from sources.github_lists import fetch_github_vc_lists
            github_leads = await fetch_github_vc_lists()
            gh_count = self._dedup_add(github_leads, "github_lists")
            print(f"  🐙  GitHub lists: {gh_count} new leads")
        except Exception as e:
            logger.warning(f"  ⚠️  GitHub lists failed: {e}")

        self._stats["total_deduped"] = len(self.all_leads)

        print(f"\n  ✅  Aggregator complete: {len(self.all_leads)} unique leads")
        print(f"      Seed: {self._stats['seed_db']} | GitHub: {self._stats['github_lists']}")

        return self.all_leads

    @property
    def stats(self) -> dict:
        return dict(self._stats)


async def generate_target_funds(leads: List[InvestorLead], output_path: str = "data/target_funds.txt"):
    """
    Extract fund websites from aggregated leads and write to target_funds.txt
    for the deep_crawl module to process.
    """
    from pathlib import Path
    websites = set()
    for lead in leads:
        if lead.website and lead.website not in ("N/A", "", "/pricing"):
            websites.add(lead.website)

    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w") as f:
        for site in sorted(websites):
            f.write(site + "\n")

    logger.info(f"  🎯  Generated {len(websites)} target fund URLs → {target_path}")
    return websites
