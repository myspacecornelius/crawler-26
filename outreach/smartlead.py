"""
Smartlead.ai outreach integration.
Docs: https://api.smartlead.ai/reference
"""

import os
import logging
from typing import List, Optional

import aiohttp

from .base import (
    OutreachProvider, OutreachSequence, OutreachLead,
    CampaignStats,
)

logger = logging.getLogger(__name__)

API_BASE = "https://server.smartlead.ai/api/v1"


class SmartleadProvider(OutreachProvider):
    """Smartlead.ai cold email platform integration."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SMARTLEAD_API_KEY", "")
        if not self.api_key:
            logger.warning("No Smartlead API key set — outreach calls will fail")

    async def _request(self, method: str, path: str, json_data: dict = None, params: dict = None) -> dict:
        url = f"{API_BASE}{path}"
        all_params = {"api_key": self.api_key}
        if params:
            all_params.update(params)
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=json_data, params=all_params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    logger.error(f"Smartlead API error {resp.status}: {body}")
                    raise Exception(f"Smartlead API {resp.status}: {body}")
                return await resp.json()

    async def create_campaign(self, sequence: OutreachSequence) -> str:
        result = await self._request("POST", "/campaigns/create", json_data={
            "name": sequence.name,
        })
        campaign_id = str(result.get("id", ""))

        # Add sequence steps
        if campaign_id and sequence.steps:
            seq_list = []
            for step in sequence.steps:
                seq_list.append({
                    "seq_number": step.step_number,
                    "seq_delay_details": {"delay_in_days": step.delay_days},
                    "subject": step.subject,
                    "email_body": step.body,
                })
            await self._request("POST", f"/campaigns/{campaign_id}/sequences", json_data={
                "sequences": seq_list,
            })

        # Set sender account
        if sequence.from_email:
            await self._request("POST", f"/campaigns/{campaign_id}/settings", json_data={
                "from_email": sequence.from_email,
                "from_name": sequence.from_name,
            })

        logger.info(f"Created Smartlead campaign: {campaign_id}")
        return campaign_id

    async def add_leads(self, campaign_id: str, leads: List[OutreachLead]) -> int:
        lead_list = []
        for lead in leads:
            entry = {
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
            }
            if lead.custom_vars:
                entry.update(lead.custom_vars)
            lead_list.append(entry)

        result = await self._request("POST", f"/campaigns/{campaign_id}/leads", json_data={
            "lead_list": lead_list,
        })
        added = result.get("upload_count", len(lead_list))
        logger.info(f"Added {added} leads to Smartlead campaign {campaign_id}")
        return added

    async def start_campaign(self, campaign_id: str) -> bool:
        await self._request("POST", f"/campaigns/{campaign_id}/status", json_data={
            "status": "START",
        })
        return True

    async def pause_campaign(self, campaign_id: str) -> bool:
        await self._request("POST", f"/campaigns/{campaign_id}/status", json_data={
            "status": "PAUSED",
        })
        return True

    async def get_stats(self, campaign_id: str) -> CampaignStats:
        data = await self._request("GET", f"/campaigns/{campaign_id}/analytics")
        return CampaignStats(
            total_leads=data.get("total_leads", 0),
            emails_sent=data.get("sent_count", 0),
            opens=data.get("open_count", 0),
            clicks=data.get("click_count", 0),
            replies=data.get("reply_count", 0),
            bounces=data.get("bounce_count", 0),
            unsubscribes=data.get("unsubscribe_count", 0),
            open_rate=data.get("open_rate", 0.0),
            reply_rate=data.get("reply_rate", 0.0),
        )

    async def list_campaigns(self) -> List[dict]:
        data = await self._request("GET", "/campaigns")
        return data if isinstance(data, list) else []
