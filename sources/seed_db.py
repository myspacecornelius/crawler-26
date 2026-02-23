"""
CRAWL — Seed Database Loader
Loads curated VC firm data from CSV and converts to InvestorLead objects.
This provides a deterministic, high-volume lead source that doesn't depend on scraping.
"""

import csv
import logging
from pathlib import Path
from typing import List
from datetime import datetime

from adapters.base import InvestorLead

logger = logging.getLogger(__name__)

DEFAULT_SEED_PATH = Path("data/seed/vc_firms.csv")


def load_seed_leads(seed_path: Path = DEFAULT_SEED_PATH) -> List[InvestorLead]:
    """
    Load VC firms from the curated seed CSV and convert to InvestorLead objects.

    CSV columns: name, website, stage, focus_areas, location, check_size
    """
    if not seed_path.exists():
        logger.warning(f"Seed file not found: {seed_path}")
        return []

    leads = []
    seen_names = set()

    with open(seed_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name or name in seen_names:
                continue
            seen_names.add(name)

            website = (row.get("website") or "").strip()
            stage = (row.get("stage") or "N/A").strip()
            focus_raw = (row.get("focus_areas") or "").strip()
            location = (row.get("location") or "N/A").strip()
            check_size = (row.get("check_size") or "N/A").strip()

            focus_areas = [s.strip() for s in focus_raw.split() if s.strip()] if focus_raw else []

            lead = InvestorLead(
                name=name,
                fund=name,
                website=website if website else "N/A",
                stage=stage,
                focus_areas=focus_areas,
                location=location,
                check_size=check_size if check_size else "N/A",
                source="seed_database",
                scraped_at=datetime.now().isoformat(),
            )
            leads.append(lead)

    logger.info(f"  📂  Seed database: loaded {len(leads)} VC firms from {seed_path}")
    return leads
