"""
Import leads from CSV into the database for a given campaign.

Usage:
    python -m api.import_leads <campaign_id> [--csv path/to/file.csv] [--user-email email]

If --csv is not specified, defaults to data/enriched/investor_leads_master.csv
If --user-email is specified and no campaign_id given, creates a new campaign for that user.
"""

import argparse
import csv
import asyncio
import sys
from pathlib import Path
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select

from .database import async_session, init_db
from .models import Campaign, Lead, User


DEFAULT_CSV = "data/enriched/investor_leads_master.csv"

TIER_MAP = {
    "🔴 HOT": "HOT",
    "HOT": "HOT",
    "🟡 WARM": "WARM",
    "WARM": "WARM",
    "🔵 COOL": "COOL",
    "COOL": "COOL",
}


def parse_score(val: str) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def clean(val: str) -> str:
    """Return stripped value or 'N/A' if empty."""
    v = (val or "").strip()
    return v if v else "N/A"


async def import_csv(campaign_id: str, csv_path: str) -> dict:
    """Import leads from a CSV file into the given campaign. Returns stats dict."""
    await init_db()

    path = Path(csv_path)
    if not path.exists():
        print(f"ERROR: CSV file not found: {path}")
        sys.exit(1)

    async with async_session() as db:
        # Verify campaign exists
        result = await db.execute(select(Campaign).where(Campaign.id == UUID(campaign_id)))
        campaign = result.scalar_one_or_none()
        if not campaign:
            print(f"ERROR: Campaign {campaign_id} not found")
            sys.exit(1)

        # Read CSV
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"Read {len(rows)} rows from {path}")

        imported = 0
        emails_found = 0
        skipped = 0

        for row in rows:
            name = clean(row.get("Name", ""))
            if name == "N/A" or not name:
                skipped += 1
                continue

            email = clean(row.get("Email", ""))
            tier_raw = clean(row.get("Tier", "COOL"))
            tier = TIER_MAP.get(tier_raw, "COOL")
            score = parse_score(row.get("Lead Score", "0"))

            email_source = "scraped" if email != "N/A" and "@" in email else "none"

            scraped_at_str = row.get("Scraped At", "")
            try:
                scraped_at = datetime.fromisoformat(scraped_at_str)
            except (ValueError, TypeError):
                scraped_at = datetime.now(timezone.utc)

            lead = Lead(
                campaign_id=UUID(campaign_id),
                name=name,
                email=email,
                email_verified=False,
                email_source=email_source,
                linkedin=clean(row.get("LinkedIn", "")),
                phone="N/A",
                fund=clean(row.get("Fund", "")),
                role=clean(row.get("Role", "")),
                website=clean(row.get("Website", "")),
                sectors=clean(row.get("Focus Areas", "")),
                check_size=clean(row.get("Check Size", "")),
                stage=clean(row.get("Stage", "")),
                hq=clean(row.get("Location", "")),
                score=score,
                tier=tier,
                source=clean(row.get("Source", "")),
                scraped_at=scraped_at,
            )
            db.add(lead)
            imported += 1
            if email != "N/A" and "@" in email:
                emails_found += 1

        # Update campaign stats
        campaign.total_leads = imported
        campaign.total_emails = emails_found
        campaign.status = "completed"
        campaign.completed_at = datetime.now(timezone.utc)

        await db.commit()

    stats = {
        "imported": imported,
        "emails_found": emails_found,
        "skipped": skipped,
        "campaign_id": campaign_id,
    }
    print(f"Imported {imported} leads ({emails_found} with email, {skipped} skipped)")
    return stats


async def create_campaign_and_import(user_email: str, csv_path: str, campaign_name: str = "CSV Import"):
    """Create a campaign for the given user and import leads into it."""
    await init_db()

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == user_email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"ERROR: User with email '{user_email}' not found")
            sys.exit(1)

        campaign = Campaign(
            user_id=user.id,
            name=campaign_name,
            vertical="vc",
            status="pending",
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        print(f"Created campaign: {campaign.id} ({campaign.name})")

    return await import_csv(str(campaign.id), csv_path)


def main():
    parser = argparse.ArgumentParser(description="Import leads from CSV into database")
    parser.add_argument("campaign_id", nargs="?", help="Campaign UUID to import into")
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Path to CSV file")
    parser.add_argument("--user-email", help="User email (creates new campaign if no campaign_id)")
    parser.add_argument("--name", default="CSV Import", help="Campaign name (when creating new)")
    args = parser.parse_args()

    if args.campaign_id:
        asyncio.run(import_csv(args.campaign_id, args.csv))
    elif args.user_email:
        asyncio.run(create_campaign_and_import(args.user_email, args.csv, args.name))
    else:
        print("ERROR: Provide either a campaign_id or --user-email")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
