"""
Incremental Crawl — freshness tracking and stale domain filtering.

Provides:
- CrawlStateManager: tracks per-domain crawl timestamps in the database
- filter_stale_domains: returns only domains that haven't been crawled recently
- update_lead_freshness: stamps last_verified / last_crawled_at on leads
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Default freshness thresholds
DEFAULT_STALE_DAYS = 7          # Re-crawl domains older than 7 days
DEFAULT_REVERIFY_DAYS = 14      # Re-verify emails older than 14 days


class CrawlStateManager:
    """
    Manages per-domain crawl state using the CrawlState DB table.
    Falls back to a local JSON file if the DB is unavailable.
    """

    def __init__(self, stale_days: int = DEFAULT_STALE_DAYS):
        self.stale_days = stale_days
        self._cache: Dict[str, datetime] = {}
        self._db_available = False

    @staticmethod
    def _normalize_domain(url: str) -> str:
        """Extract bare domain from a URL."""
        if not url.startswith("http"):
            url = "https://" + url
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        return domain.lower().replace("www.", "").strip("/")

    async def load_from_db(self):
        """Load crawl state from the database into cache."""
        try:
            from api.database import async_session, init_db
            from api.models import CrawlState
            from sqlalchemy import select

            await init_db()
            async with async_session() as session:
                result = await session.execute(select(CrawlState))
                rows = result.scalars().all()
                for row in rows:
                    self._cache[row.domain] = row.last_crawled_at
                self._db_available = True
                logger.info(f"  [incremental] Loaded {len(self._cache)} domain states from DB")
        except Exception as e:
            logger.warning(f"  [incremental] DB unavailable, using fresh state: {e}")
            self._db_available = False

    def is_stale(self, url: str) -> bool:
        """Check if a domain needs re-crawling."""
        domain = self._normalize_domain(url)
        last = self._cache.get(domain)
        if last is None:
            return True  # Never crawled
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.stale_days)
        # Handle naive datetimes from SQLite
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        return last < cutoff

    def filter_stale(self, urls: List[str]) -> Tuple[List[str], List[str]]:
        """
        Split URLs into (stale, fresh) lists.
        Returns (urls_to_crawl, urls_to_skip).
        """
        stale = []
        fresh = []
        for url in urls:
            if self.is_stale(url):
                stale.append(url)
            else:
                fresh.append(url)
        return stale, fresh

    async def mark_crawled(
        self,
        url: str,
        leads_found: int = 0,
        status: str = "completed",
        duration_s: float = 0.0,
    ):
        """Record that a domain was just crawled."""
        domain = self._normalize_domain(url)
        now = datetime.now(timezone.utc)
        self._cache[domain] = now

        if not self._db_available:
            return

        try:
            from api.database import async_session
            from api.models import CrawlState
            from sqlalchemy import select

            async with async_session() as session:
                result = await session.execute(
                    select(CrawlState).where(CrawlState.domain == domain)
                )
                row = result.scalar_one_or_none()

                if row:
                    row.last_crawled_at = now
                    row.leads_found = leads_found
                    row.status = status
                    row.crawl_duration_s = duration_s
                else:
                    session.add(CrawlState(
                        domain=domain,
                        last_crawled_at=now,
                        leads_found=leads_found,
                        status=status,
                        crawl_duration_s=duration_s,
                    ))
                await session.commit()
        except Exception as e:
            logger.warning(f"  [incremental] Failed to persist crawl state for {domain}: {e}")

    async def mark_batch_crawled(self, results: List[dict]):
        """
        Batch update crawl state for multiple domains.
        Each item: {"url": str, "leads_found": int, "status": str, "duration_s": float}
        """
        for item in results:
            await self.mark_crawled(
                url=item["url"],
                leads_found=item.get("leads_found", 0),
                status=item.get("status", "completed"),
                duration_s=item.get("duration_s", 0.0),
            )

    def summary(self) -> dict:
        """Return a summary of crawl state."""
        now = datetime.now(timezone.utc)
        total = len(self._cache)
        stale = sum(1 for ts in self._cache.values()
                    if (ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts)
                    < now - timedelta(days=self.stale_days))
        return {
            "total_domains": total,
            "stale_domains": stale,
            "fresh_domains": total - stale,
            "stale_threshold_days": self.stale_days,
        }


async def update_lead_freshness_in_db(
    campaign_id: str,
    verified_emails: List[str],
    reverify_days: int = DEFAULT_REVERIFY_DAYS,
) -> int:
    """
    Update last_verified timestamp for leads whose emails were just verified.
    Also stamps last_crawled_at for all leads in the campaign.
    Returns the number of leads updated.
    """
    try:
        from api.database import async_session
        from api.models import Lead
        from sqlalchemy import select, update

        now = datetime.now(timezone.utc)
        updated = 0

        async with async_session() as session:
            # Stamp last_crawled_at on all campaign leads
            await session.execute(
                update(Lead)
                .where(Lead.campaign_id == campaign_id)
                .values(last_crawled_at=now)
            )

            # Stamp last_verified on verified emails
            if verified_emails:
                await session.execute(
                    update(Lead)
                    .where(
                        Lead.campaign_id == campaign_id,
                        Lead.email.in_(verified_emails),
                    )
                    .values(last_verified=now, email_verified=True)
                )
                updated = len(verified_emails)

            await session.commit()

        return updated
    except Exception as e:
        logger.warning(f"  [incremental] Failed to update lead freshness: {e}")
        return 0


async def get_stale_leads(
    campaign_id: str,
    reverify_days: int = DEFAULT_REVERIFY_DAYS,
) -> List[str]:
    """
    Return emails of leads in a campaign that need re-verification
    (last_verified is null or older than reverify_days).
    """
    try:
        from api.database import async_session
        from api.models import Lead
        from sqlalchemy import select, or_

        cutoff = datetime.now(timezone.utc) - timedelta(days=reverify_days)

        async with async_session() as session:
            result = await session.execute(
                select(Lead.email).where(
                    Lead.campaign_id == campaign_id,
                    Lead.email != "N/A",
                    Lead.email != "",
                    or_(
                        Lead.last_verified == None,
                        Lead.last_verified < cutoff,
                    ),
                )
            )
            return [row[0] for row in result.all()]
    except Exception as e:
        logger.warning(f"  [incremental] Failed to get stale leads: {e}")
        return []
