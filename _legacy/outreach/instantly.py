"""
Instantly.ai outreach integration.
Docs: https://developer.instantly.ai/
"""

import os
import logging
from typing import List, Optional

import aiohttp

from .base import (
    OutreachProvider, OutreachSequence, OutreachLead,
    CampaignStats, OutreachStatus,
)

logger = logging.getLogger(__name__)

API_BASE = "https://api.instantly.ai/api/v1"


class InstantlyProvider(OutreachProvider):
    """Instantly.ai cold email platform integration."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("INSTANTLY_API_KEY", "")
        if not self.api_key:
            logger.warning("No Instantly API key set — outreach calls will fail")

    def _params(self, extra: dict = None) -> dict:
        params = {"api_key": self.api_key}
        if extra:
            params.update(extra)
        return params

    async def _request(self, method: str, path: str, json_data: dict = None, params: dict = None) -> dict:
        url = f"{API_BASE}{path}"
        all_params = self._params(params)
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=json_data, params=all_params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    logger.error(f"Instantly API error {resp.status}: {body}")
                    raise Exception(f"Instantly API {resp.status}: {body}")
                return await resp.json()

    async def create_campaign(self, sequence: OutreachSequence) -> str:
        """Create a campaign in Instantly with the given sequence steps."""
        # Create campaign
        data = {
            "name": sequence.name,
            "from_email": sequence.from_email,
            "from_name": sequence.from_name,
        }
        result = await self._request("POST", "/campaign/create", json_data=data)
        campaign_id = result.get("id", "")

        # Add sequence steps
        if campaign_id and sequence.steps:
            sequences = []
            for step in sequence.steps:
                sequences.append({
                    "subject": step.subject,
                    "body": step.body,
                    "delay": step.delay_days,
                })
            await self._request("POST", "/campaign/set-sequences", json_data={
                "campaign_id": campaign_id,
                "sequences": [{"steps": sequences}],
            })

        logger.info(f"Created Instantly campaign: {campaign_id}")
        return campaign_id

    async def add_leads(self, campaign_id: str, leads: List[OutreachLead]) -> int:
        """Add leads to an Instantly campaign."""
        lead_list = []
        for lead in leads:
            entry = {
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company_name": lead.company,
            }
            # Add custom variables
            if lead.role:
                entry["personalization"] = lead.role
            entry.update(lead.custom_vars)
            lead_list.append(entry)

        # Instantly accepts up to 5000 leads per request
        added = 0
        for i in range(0, len(lead_list), 5000):
            batch = lead_list[i:i + 5000]
            await self._request("POST", "/lead/add", json_data={
                "campaign_id": campaign_id,
                "leads": batch,
            })
            added += len(batch)

        logger.info(f"Added {added} leads to Instantly campaign {campaign_id}")
        return added

    async def start_campaign(self, campaign_id: str) -> bool:
        await self._request("POST", "/campaign/activate", json_data={
            "campaign_id": campaign_id,
        })
        return True

    async def pause_campaign(self, campaign_id: str) -> bool:
        await self._request("POST", "/campaign/pause", json_data={
            "campaign_id": campaign_id,
        })
        return True

    async def get_stats(self, campaign_id: str) -> CampaignStats:
        data = await self._request("GET", "/analytics/campaign/summary", params={
            "campaign_id": campaign_id,
        })
        return CampaignStats(
            total_leads=data.get("total_leads", 0),
            emails_sent=data.get("sent", 0),
            opens=data.get("opened", 0),
            clicks=data.get("clicked", 0),
            replies=data.get("replied", 0),
            bounces=data.get("bounced", 0),
            unsubscribes=data.get("unsubscribed", 0),
            open_rate=data.get("open_rate", 0.0),
            reply_rate=data.get("reply_rate", 0.0),
        )

    async def list_campaigns(self) -> List[dict]:
        data = await self._request("GET", "/campaign/list")
        return data if isinstance(data, list) else []
