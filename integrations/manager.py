"""
CRM manager — orchestrates lead export to CRM providers.
Mirrors the outreach/manager.py pattern for CRM integrations.
"""

import logging
from typing import Dict, List, Optional

from .crm_base import (
    CRMProvider, CRMContact, CRMPushSummary, CRMField,
    DEFAULT_FIELD_MAPPING,
)
from .hubspot import HubSpotProvider
from .salesforce import SalesforceProvider

logger = logging.getLogger(__name__)

PROVIDERS = {
    "hubspot": HubSpotProvider,
    "salesforce": SalesforceProvider,
}


def get_crm_provider(
    name: str,
    test_mode: bool = False,
    **kwargs,
) -> CRMProvider:
    """Get a CRM provider by name."""
    cls = PROVIDERS.get(name.lower())
    if not cls:
        raise ValueError(f"Unknown CRM provider '{name}'. Available: {list(PROVIDERS.keys())}")
    return cls(test_mode=test_mode, **kwargs)


def db_lead_to_crm_contact(lead, custom_fields: Optional[Dict] = None) -> Optional[CRMContact]:
    """
    Convert a database Lead object to a CRMContact.
    Returns None if the lead doesn't have a usable email.
    """
    email = getattr(lead, "email", "N/A")
    if not email or email == "N/A" or "@" not in email or "invalid" in email.lower():
        return None

    name = getattr(lead, "name", "")
    parts = name.split(None, 1) if name and name != "Unknown" else ["", ""]
    first_name = parts[0] if len(parts) >= 1 else ""
    last_name = parts[1] if len(parts) >= 2 else ""

    return CRMContact(
        email=email.split()[0],  # Strip annotations
        first_name=first_name,
        last_name=last_name,
        company=getattr(lead, "fund", "") or "",
        role=getattr(lead, "role", "") or "",
        phone=getattr(lead, "phone", "") or "",
        linkedin=getattr(lead, "linkedin", "") or "",
        website=getattr(lead, "website", "") or "",
        custom_fields={
            "sectors": getattr(lead, "sectors", "") or "",
            "check_size": getattr(lead, "check_size", "") or "",
            "stage": getattr(lead, "stage", "") or "",
            "lead_score": str(getattr(lead, "score", 0)),
            "lead_tier": getattr(lead, "tier", "COOL"),
            "source_url": getattr(lead, "source", "") or "",
            **(custom_fields or {}),
        },
    )


class CRMManager:
    """
    Manages the CRM push lifecycle:
    1. Convert DB leads to CRM contacts
    2. Apply field mapping
    3. Push to CRM provider
    4. Return results
    """

    def __init__(
        self,
        provider_name: str = "hubspot",
        test_mode: bool = False,
        **provider_kwargs,
    ):
        self.provider = get_crm_provider(provider_name, test_mode=test_mode, **provider_kwargs)
        self.provider_name = provider_name

    def prepare_contacts(
        self,
        db_leads: list,
        min_score: float = 0,
        tiers: Optional[List[str]] = None,
        custom_fields: Optional[Dict] = None,
    ) -> List[CRMContact]:
        """
        Filter and convert DB Lead objects to CRMContact objects.

        Args:
            db_leads: List of Lead ORM objects
            min_score: Minimum lead score to include
            tiers: Filter by tier (HOT, WARM, COOL)
            custom_fields: Extra fields to inject into every contact
        """
        contacts = []
        for lead in db_leads:
            score = getattr(lead, "score", 0) or 0
            if score < min_score:
                continue

            if tiers:
                tier = getattr(lead, "tier", "COOL")
                if tier not in tiers:
                    continue

            contact = db_lead_to_crm_contact(lead, custom_fields)
            if contact:
                contacts.append(contact)

        logger.info(
            f"Prepared {len(contacts)} CRM contacts (from {len(db_leads)} leads)"
        )
        return contacts

    async def push(
        self,
        contacts: List[CRMContact],
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> CRMPushSummary:
        """Push contacts to the configured CRM provider."""
        mapping = dict(DEFAULT_FIELD_MAPPING)
        if field_mapping:
            mapping.update(field_mapping)

        summary = await self.provider.push_leads(contacts, field_mapping=mapping)
        logger.info(
            f"CRM push to {self.provider_name}: "
            f"{summary.created} created, {summary.updated} updated, "
            f"{summary.failed} failed (of {summary.total})"
        )
        return summary

    async def get_fields(self) -> List[CRMField]:
        """Get available CRM fields for field mapping UI."""
        return await self.provider.get_fields()

    async def sync_status(self, crm_ids: List[str]) -> Dict[str, str]:
        """Check status of previously pushed contacts."""
        return await self.provider.sync_status(crm_ids)
