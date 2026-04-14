"""
Supabase Writer — writes normalized offers to persistent storage.

Currently writes to local JSON files. When SUPABASE_URL is configured,
switches to Supabase upserts.

Uses dedup metadata (_dedup_status, _changed_fields, _previous_values) to
decide what goes into the offers table vs. the offer_snapshots table:
- "new" offers → INSERT into offers
- "changed" offers → UPDATE offers + INSERT into offer_snapshots
- "unchanged" offers → UPDATE last_verified_at only
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def _strip_internal_fields(offer: dict) -> dict:
    """Remove _-prefixed internal metadata before persisting."""
    return {k: v for k, v in offer.items() if not k.startswith("_")}


async def write_offers(offers: List[dict], output_dir: str = "data/output"):
    """
    Write offers to persistent storage.

    Decision logic based on _dedup_status (set by OfferDeduplicator):
    - "new":       New offer discovered — full INSERT
    - "changed":   Known offer with updated fields — UPDATE + store snapshot
    - "unchanged": Known offer, no changes — bump last_verified_at

    Falls back to local JSON until Supabase env vars are configured.
    """
    # Categorize by dedup status
    new_offers = [o for o in offers if o.get("_dedup_status") == "new"]
    changed_offers = [o for o in offers if o.get("_dedup_status") == "changed"]
    unchanged_offers = [o for o in offers if o.get("_dedup_status") == "unchanged"]

    logger.info(
        f"Write: {len(new_offers)} new, {len(changed_offers)} changed, "
        f"{len(unchanged_offers)} unchanged"
    )

    # Log change details for visibility
    for offer in changed_offers:
        changed_fields = offer.get("_changed_fields", [])
        prev = offer.get("_previous_values", {})
        logger.info(
            f"  Changed: {offer.get('vendor_domain')}/{offer.get('title', '')[:40]}"
            f" — fields: {changed_fields}, prev: {prev}"
        )

    # Write to local JSON (Supabase deferred)
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = path / f"offers_{ts}.json"

    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "new": len(new_offers),
            "changed": len(changed_offers),
            "unchanged": len(unchanged_offers),
        },
        "offers": [_strip_internal_fields(o) for o in new_offers],
        "snapshots": [
            {
                "offer": _strip_internal_fields(o),
                "changed_fields": o.get("_changed_fields", []),
                "previous_values": o.get("_previous_values", {}),
            }
            for o in changed_offers
        ],
    }

    with open(out_file, "w") as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(f"Wrote {len(new_offers)} offers + {len(changed_offers)} snapshots → {out_file}")
    return out_file
