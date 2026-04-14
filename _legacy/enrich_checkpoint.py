"""
Quick script to run enrichment pipeline on checkpoint CSV data.
Loads contacts from vc_contacts_checkpoint.csv, runs email guessing,
validation, and scoring, then saves via CSVWriter.
"""
import asyncio
import csv
import logging

from adapters.base import InvestorLead
from enrichment.email_validator import EmailValidator
from enrichment.email_guesser import EmailGuesser
from enrichment.scoring import LeadScorer
from output.csv_writer import CSVWriter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def load_checkpoint(path: str = "data/vc_contacts_checkpoint.csv"):
    contacts = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lead = InvestorLead(
                name=row.get('name', ''),
                role=row.get('role', ''),
                email=row.get('email', 'N/A'),
                linkedin=row.get('linkedin', 'N/A'),
                fund=row.get('fund_name', ''),
                website=row.get('fund_url', ''),
            )
            contacts.append(lead)
    return contacts


async def main():
    logger.info("Loading checkpoint...")
    contacts = load_checkpoint()
    logger.info(f"Loaded {len(contacts)} contacts from checkpoint")

    validator = EmailValidator()
    guesser = EmailGuesser(concurrency=10)
    scorer = LeadScorer("config/scoring.yaml")
    writer = CSVWriter("data")

    # Step 1: Validate existing emails
    logger.info(f"📧 Validating {len(contacts)} emails...")
    for contact in contacts:
        result = validator.validate(contact.email)
        if result["quality"] == "invalid":
            contact.email = "N/A (invalid)"
        elif result["is_disposable"]:
            contact.email = f"{contact.email} ⚠️ (disposable)"

    # Step 2: Guess emails for contacts without one
    logger.info("✉️  Guessing emails for contacts without one...")
    contacts = await guesser.guess_batch(contacts)
    stats = guesser.stats
    logger.info(f"✉️  Guesser: {stats['found']} found / {stats['attempted']} attempted")

    # Step 3: Score leads
    logger.info("📊 Scoring leads...")
    contacts = scorer.score_batch(contacts)

    # Step 4: Save
    logger.info("💾 Writing enriched output...")
    writer.write_master(contacts)
    logger.info(f"💾 Saved {len(contacts)} enriched contacts")

    # Summary
    total_emails = len([c for c in contacts if c.email and c.email != "N/A" and "invalid" not in c.email])
    total_linkedin = len([c for c in contacts if c.linkedin and c.linkedin != "N/A"])
    scorer_stats = scorer.stats

    logger.info(f"""
============================================================
  📊  ENRICHMENT SUMMARY
============================================================
  📝  Total contacts: {len(contacts)}
  📧  Emails found: {total_emails}
  🔗  LinkedIn profiles: {total_linkedin}
  📈  Avg score: {scorer_stats.get('avg_score', 0)}
  🔴  HOT leads: {scorer_stats.get('hot_count', 0)}
  ⏱️  Complete
============================================================
""")


if __name__ == "__main__":
    asyncio.run(main())
