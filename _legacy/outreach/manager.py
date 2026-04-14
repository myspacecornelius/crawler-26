"""
Outreach manager — orchestrates lead export to outreach providers.
Converts InvestorLead objects to OutreachLead and manages campaign lifecycle.
"""

import logging
from typing import List, Optional

from .base import OutreachProvider, OutreachSequence, OutreachLead, CampaignStats
from .instantly import InstantlyProvider
from .smartlead import SmartleadProvider
from .templates import get_template

logger = logging.getLogger(__name__)

PROVIDERS = {
    "instantly": InstantlyProvider,
    "smartlead": SmartleadProvider,
}


def get_provider(name: str, api_key: Optional[str] = None) -> OutreachProvider:
    """Get an outreach provider by name."""
    cls = PROVIDERS.get(name.lower())
    if not cls:
        raise ValueError(f"Unknown provider '{name}'. Available: {list(PROVIDERS.keys())}")
    return cls(api_key=api_key)


def investor_lead_to_outreach(lead, custom_vars: dict = None) -> Optional[OutreachLead]:
    """
    Convert an InvestorLead to an OutreachLead.
    Returns None if the lead doesn't have a usable email.
    """
    email = getattr(lead, "email", "N/A")
    if not email or email == "N/A" or "@" not in email or "invalid" in email.lower():
        return None

    name = getattr(lead, "name", "")
    parts = name.split(None, 1) if name and name != "Unknown" else ["", ""]
    first_name = parts[0] if len(parts) >= 1 else ""
    last_name = parts[1] if len(parts) >= 2 else ""

    ol = OutreachLead(
        email=email.split()[0],  # Strip any annotations like "⚠️ (catch-all)"
        first_name=first_name,
        last_name=last_name,
        company=getattr(lead, "fund", ""),
        role=getattr(lead, "role", ""),
        linkedin=getattr(lead, "linkedin", ""),
        custom_vars={
            "sectors": getattr(lead, "sectors", ""),
            "website": getattr(lead, "website", ""),
            "score": str(getattr(lead, "lead_score", 0)),
            **(custom_vars or {}),
        },
    )
    return ol


class OutreachManager:
    """
    Manages the full outreach lifecycle:
    1. Convert leads to outreach format
    2. Create campaign with sequence template
    3. Upload leads
    4. Start campaign
    5. Track stats
    """

    def __init__(self, provider_name: str = "instantly", api_key: Optional[str] = None):
        self.provider = get_provider(provider_name, api_key)
        self.provider_name = provider_name

    def prepare_leads(
        self,
        investor_leads: list,
        min_score: int = 0,
        tiers: Optional[List[str]] = None,
        custom_vars: dict = None,
    ) -> List[OutreachLead]:
        """
        Filter and convert InvestorLead objects to OutreachLead.
        
        Args:
            investor_leads: List of InvestorLead objects
            min_score: Minimum lead score to include
            tiers: Filter by tier (HOT, WARM, COOL)
            custom_vars: Extra template variables to inject
        """
        outreach_leads = []
        for lead in investor_leads:
            # Score filter
            score = getattr(lead, "lead_score", 0)
            if score < min_score:
                continue

            # Tier filter
            if tiers:
                tier = getattr(lead, "lead_tier", "COOL")
                if tier not in tiers:
                    continue

            ol = investor_lead_to_outreach(lead, custom_vars)
            if ol:
                outreach_leads.append(ol)

        logger.info(f"Prepared {len(outreach_leads)} leads for outreach (from {len(investor_leads)} total)")
        return outreach_leads

    async def launch_campaign(
        self,
        name: str,
        vertical: str,
        leads: List[OutreachLead],
        sequence: Optional[OutreachSequence] = None,
        from_email: str = "",
        from_name: str = "",
    ) -> dict:
        """
        Create and launch a full outreach campaign.
        
        Returns dict with campaign_id, leads_added, status.
        """
        # Use vertical template if no custom sequence provided
        if not sequence:
            sequence = get_template(vertical)

        if from_email:
            sequence.from_email = from_email
        if from_name:
            sequence.from_name = from_name

        # Create campaign
        campaign_id = await self.provider.create_campaign(sequence)

        # Add leads
        added = await self.provider.add_leads(campaign_id, leads)

        result = {
            "campaign_id": campaign_id,
            "provider": self.provider_name,
            "leads_added": added,
            "steps": len(sequence.steps),
            "status": "ready",
        }

        logger.info(f"Campaign '{name}' ready: {added} leads, {len(sequence.steps)} steps on {self.provider_name}")
        return result

    async def start(self, campaign_id: str) -> bool:
        return await self.provider.start_campaign(campaign_id)

    async def pause(self, campaign_id: str) -> bool:
        return await self.provider.pause_campaign(campaign_id)

    async def stats(self, campaign_id: str) -> CampaignStats:
        return await self.provider.get_stats(campaign_id)
