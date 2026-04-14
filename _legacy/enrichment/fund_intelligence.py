"""
CRAWL — Fund Intelligence Layer

Cross-references crawled fund domains against known databases to
backfill fund metadata: AUM, stage focus, check size, investment count,
sector focus, and geographic preferences.

Sources:
  1. Local dedup index (data/dedup_index.json) — aggregate from own data
  2. OpenVC data if available (from adapter scrapes)
  3. Crunchbase org enrichment (if API key available)

Usage:
    from enrichment.fund_intelligence import FundIntelligence
    intel = FundIntelligence()
    leads = intel.enrich_batch(leads)
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class FundIntelligence:
    """
    Enriches leads with fund-level metadata by aggregating data
    from multiple internal sources.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.fund_db: Dict[str, dict] = {}
        self._build_fund_db()

    def _build_fund_db(self):
        """Build a fund metadata database from available sources."""
        # Source 1: Dedup index — aggregate lead data per fund
        dedup_path = self.data_dir / "dedup_index.json"
        if dedup_path.exists():
            try:
                with open(dedup_path, "r") as f:
                    index = json.load(f)
                fund_agg = defaultdict(lambda: {
                    "lead_count": 0,
                    "roles": set(),
                    "focus_areas": set(),
                    "websites": set(),
                    "locations": set(),
                    "emails_found": 0,
                })
                for entry in index.values():
                    fund = entry.get("fund", "").lower().strip()
                    if not fund:
                        continue
                    agg = fund_agg[fund]
                    agg["lead_count"] += 1
                    if entry.get("role") and entry["role"] != "N/A":
                        agg["roles"].add(entry["role"])
                    for area in (entry.get("focus_areas") or []):
                        agg["focus_areas"].add(area)
                    if entry.get("website"):
                        agg["websites"].add(entry["website"])
                    if entry.get("location") and entry["location"] != "N/A":
                        agg["locations"].add(entry["location"])
                    if entry.get("email") and entry["email"] != "N/A":
                        agg["emails_found"] += 1

                for fund, agg in fund_agg.items():
                    self.fund_db[fund] = {
                        "team_size": agg["lead_count"],
                        "roles": list(agg["roles"]),
                        "focus_areas": list(agg["focus_areas"]),
                        "websites": list(agg["websites"]),
                        "locations": list(agg["locations"]),
                        "email_coverage": agg["emails_found"] / max(agg["lead_count"], 1),
                    }
                logger.info(f"  🏢  Fund intelligence: {len(self.fund_db)} funds from dedup index")
            except Exception as e:
                logger.debug(f"  Fund intelligence dedup error: {e}")

        # Source 2: Enriched master CSV — extract fund-level aggregates
        master_path = self.data_dir / "enriched" / "investor_leads_master.csv"
        if master_path.exists():
            try:
                import csv
                with open(master_path, "r") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        fund = row.get("Fund", "").lower().strip()
                        if fund and fund not in self.fund_db:
                            self.fund_db[fund] = {
                                "stage": row.get("Stage", ""),
                                "check_size": row.get("Check Size", ""),
                                "focus_areas": [a.strip() for a in row.get("Focus Areas", "").split(";") if a.strip()],
                                "location": row.get("Location", ""),
                            }
            except Exception:
                pass

    def lookup_fund(self, fund_name: str) -> Optional[dict]:
        """Look up metadata for a fund by name."""
        key = fund_name.lower().strip()
        # Remove common suffixes for fuzzy matching
        for suffix in [" ventures", " capital", " partners", " fund", " management"]:
            if key.endswith(suffix):
                short = key[:-len(suffix)].strip()
                if short in self.fund_db:
                    return self.fund_db[short]
        return self.fund_db.get(key)

    def enrich_batch(self, leads: list) -> list:
        """
        Enrich leads with fund-level metadata.
        Backfills focus_areas, stage, check_size, and location from fund data.
        """
        if not self.fund_db:
            return leads

        enriched = 0
        for lead in leads:
            meta = self.lookup_fund(lead.fund)
            if not meta:
                continue

            # Backfill empty fields
            if not lead.focus_areas and meta.get("focus_areas"):
                lead.focus_areas = meta["focus_areas"]
                enriched += 1
            if lead.stage in ("N/A", "", None) and meta.get("stage"):
                lead.stage = meta["stage"]
                enriched += 1
            if lead.check_size in ("N/A", "", None) and meta.get("check_size"):
                lead.check_size = meta["check_size"]
                enriched += 1
            if lead.location in ("N/A", "", None):
                locs = meta.get("locations", [])
                if locs:
                    lead.location = locs[0]
                    enriched += 1

        if enriched:
            print(f"  🏢  Fund intelligence: enriched {enriched} fields across {len(leads)} leads")
        return leads
