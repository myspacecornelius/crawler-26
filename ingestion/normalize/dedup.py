"""
Offer Deduplication — persistent cross-run dedup with change detection.

Key difference from the old LeadDeduplicator:

The old dedup merged by (person_name, fund_name) and silently combined records.
For offers, the same vendor can *change* a reward amount or add/remove requirements
over time. Those changes are meaningful — they should create OfferSnapshots,
not be silently swallowed.

This deduplicator:
1. Uses (vendor_domain, slugified_title) as the identity key
2. On re-encounter, checks if meaningful fields changed
3. Tags changed offers so the output layer can create OfferSnapshots
4. Only merges when it's filling in empty fields (no data loss)
"""

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)

# Fields that, if changed, represent a real offer update (not just noise)
CHANGE_SIGNIFICANT_FIELDS = ["reward_value", "cta_url", "description"]


def _slugify(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _dedup_key(vendor_domain: str, title: str) -> str:
    """Stable dedup key from vendor domain + slugified title."""
    slug = _slugify(title)
    raw = f"{vendor_domain.lower()}|{slug}"
    return hashlib.md5(raw.encode()).hexdigest()


def _fields_changed(existing: dict, new: dict) -> List[str]:
    """Check which significant fields changed between existing and new."""
    changed = []
    for field in CHANGE_SIGNIFICANT_FIELDS:
        old_val = str(existing.get(field, "") or "").strip()
        new_val = str(new.get(field, "") or "").strip()
        if old_val and new_val and old_val != new_val:
            changed.append(field)
    return changed


class OfferDeduplicator:
    """
    Cross-run offer deduplication with change detection.
    Maintains a persistent index at data/offer_dedup_index.json.
    """

    def __init__(self, index_path: str = "data/offer_dedup_index.json"):
        self.index_path = Path(index_path)
        self.index: Dict[str, dict] = {}
        self._load_index()

    def _load_index(self):
        if self.index_path.exists():
            try:
                with open(self.index_path, "r") as f:
                    self.index = json.load(f)
                logger.info(f"Loaded dedup index: {len(self.index)} entries")
            except (json.JSONDecodeError, IOError):
                self.index = {}

    def _save_index(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(self.index_path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(self.index, f, indent=2, default=str)
            os.replace(tmp, str(self.index_path))
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def _fill_empty(self, existing: dict, new: dict) -> dict:
        """Fill in missing fields from new data. Never overwrites existing values."""
        merged = dict(existing)
        for field in ["description", "reward_value", "cta_url", "category", "extraction_method"]:
            if not merged.get(field) and new.get(field):
                merged[field] = new[field]
        return merged

    def deduplicate(self, offers: List[dict]) -> List[dict]:
        """
        Deduplicate offers against persistent index.

        Returns a list of unique offers, each annotated with:
        - _dedup_status: "new" | "unchanged" | "changed"
        - _changed_fields: list of field names that changed (if status is "changed")
        - _previous_values: dict of old values for changed fields

        The output layer uses _dedup_status to decide whether to create an OfferSnapshot.
        """
        results: List[dict] = []
        seen_this_batch: Set[str] = set()
        stats = {"new": 0, "unchanged": 0, "changed": 0, "batch_dups": 0}

        for offer in offers:
            key = _dedup_key(
                offer.get("vendor_domain", ""),
                offer.get("title", ""),
            )

            # Skip within-batch duplicates
            if key in seen_this_batch:
                stats["batch_dups"] += 1
                continue
            seen_this_batch.add(key)

            if key in self.index:
                existing = self.index[key]
                changed = _fields_changed(existing, offer)

                if changed:
                    # Offer exists but has meaningful changes → snapshot trigger
                    offer["_dedup_status"] = "changed"
                    offer["_changed_fields"] = changed
                    offer["_previous_values"] = {f: existing.get(f) for f in changed}
                    # Update index with new values
                    self.index[key] = {
                        **existing,
                        **{f: offer[f] for f in changed if offer.get(f)},
                        "last_seen": datetime.now().isoformat(),
                        "times_seen": existing.get("times_seen", 1) + 1,
                    }
                    stats["changed"] += 1
                else:
                    # Same offer, no changes — fill empty fields, bump counter
                    self.index[key] = self._fill_empty(existing, offer)
                    self.index[key]["last_seen"] = datetime.now().isoformat()
                    self.index[key]["times_seen"] = existing.get("times_seen", 1) + 1
                    offer["_dedup_status"] = "unchanged"
                    stats["unchanged"] += 1
            else:
                # Brand new offer
                self.index[key] = {
                    **offer,
                    "first_seen": datetime.now().isoformat(),
                    "last_seen": datetime.now().isoformat(),
                    "times_seen": 1,
                }
                offer["_dedup_status"] = "new"
                stats["new"] += 1

            # Enrich from index (fill in any fields the index has that this crawl missed)
            idx = self.index.get(key, {})
            for field in ["description", "reward_value", "cta_url"]:
                if not offer.get(field) and idx.get(field):
                    offer[field] = idx[field]

            results.append(offer)

        self._save_index()
        logger.info(
            f"Dedup: {stats['new']} new, {stats['unchanged']} unchanged, "
            f"{stats['changed']} changed, {stats['batch_dups']} batch dups removed"
        )
        return results
