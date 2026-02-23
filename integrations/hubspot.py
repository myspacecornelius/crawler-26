"""
HubSpot CRM integration — Contacts API v3.
Docs: https://developers.hubspot.com/docs/api/crm/contacts

Requires: HUBSPOT_API_KEY environment variable (private app access token).
"""

import os
import logging
from typing import Dict, List, Optional

import aiohttp

from .crm_base import (
    CRMProvider, CRMContact, CRMPushResult, CRMPushSummary,
    CRMField, PushStatus, DEFAULT_FIELD_MAPPING,
)

logger = logging.getLogger(__name__)

API_BASE = "https://api.hubapi.com"

# HubSpot standard contact property names
HUBSPOT_FIELD_MAP: Dict[str, str] = {
    "email": "email",
    "firstname": "firstname",
    "lastname": "lastname",
    "company": "company",
    "jobtitle": "jobtitle",
    "phone": "phone",
    "linkedin_url": "hs_linkedin_url",
    "website": "website",
}


class HubSpotProvider(CRMProvider):
    """HubSpot CRM integration using Contacts API v3."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        test_mode: bool = False,
    ):
        self.api_key = api_key or os.getenv("HUBSPOT_API_KEY", "")
        self.test_mode = test_mode
        if not self.api_key and not self.test_mode:
            logger.warning("No HubSpot API key set — CRM calls will fail")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _map_contact(
        self,
        contact: CRMContact,
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> dict:
        """Convert CRMContact to HubSpot properties dict."""
        # Build canonical → value mapping from the contact
        canonical = {
            "email": contact.email,
            "firstname": contact.first_name,
            "lastname": contact.last_name,
            "company": contact.company,
            "jobtitle": contact.role,
            "phone": contact.phone,
            "linkedin_url": contact.linkedin,
            "website": contact.website,
        }

        # Apply user field mapping overrides (Lead field → CRM field)
        mapping = dict(DEFAULT_FIELD_MAPPING)
        if field_mapping:
            mapping.update(field_mapping)

        # Resolve to HubSpot property names
        properties: Dict[str, str] = {}
        for lead_attr, canonical_name in mapping.items():
            hs_prop = HUBSPOT_FIELD_MAP.get(canonical_name, canonical_name)
            value = canonical.get(canonical_name, "")
            if not value and hasattr(contact, lead_attr):
                value = getattr(contact, lead_attr, "")
            if value:
                properties[hs_prop] = str(value)

        # Include custom fields directly
        for k, v in contact.custom_fields.items():
            if v:
                properties[k] = str(v)

        return properties

    async def push_leads(
        self,
        contacts: List[CRMContact],
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> CRMPushSummary:
        """Push contacts to HubSpot using batch create/update."""
        if self.test_mode:
            return self._test_push(contacts)

        results: List[CRMPushResult] = []
        errors: List[str] = []

        # HubSpot batch endpoint accepts up to 100 contacts per request
        for i in range(0, len(contacts), 100):
            batch = contacts[i:i + 100]
            inputs = []
            for c in batch:
                props = self._map_contact(c, field_mapping)
                inputs.append({"properties": props})

            payload = {"inputs": inputs}

            try:
                async with aiohttp.ClientSession() as session:
                    # Try batch create first
                    async with session.post(
                        f"{API_BASE}/crm/v3/objects/contacts/batch/create",
                        json=payload,
                        headers=self._headers(),
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        body = await resp.json()

                        if resp.status == 201:
                            for item in body.get("results", []):
                                props = item.get("properties", {})
                                results.append(CRMPushResult(
                                    email=props.get("email", ""),
                                    success=True,
                                    crm_id=item.get("id"),
                                    created=True,
                                ))
                        elif resp.status == 409:
                            # Contacts already exist — fall back to upsert
                            upsert_results = await self._upsert_batch(
                                session, batch, field_mapping
                            )
                            results.extend(upsert_results)
                        else:
                            err = body.get("message", f"HTTP {resp.status}")
                            errors.append(err)
                            for c in batch:
                                results.append(CRMPushResult(
                                    email=c.email, success=False, error=err
                                ))
            except Exception as e:
                err = str(e)
                errors.append(err)
                for c in batch:
                    results.append(CRMPushResult(
                        email=c.email, success=False, error=err
                    ))

        created = sum(1 for r in results if r.success and r.created)
        updated = sum(1 for r in results if r.success and not r.created)
        failed = sum(1 for r in results if not r.success)

        if failed == len(results):
            status = PushStatus.FAILED
        elif failed > 0:
            status = PushStatus.PARTIAL
        else:
            status = PushStatus.COMPLETED

        return CRMPushSummary(
            provider="hubspot",
            total=len(contacts),
            created=created,
            updated=updated,
            failed=failed,
            status=status,
            results=results,
            errors=errors,
        )

    async def _upsert_batch(
        self,
        session: aiohttp.ClientSession,
        contacts: List[CRMContact],
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> List[CRMPushResult]:
        """Update existing contacts by email lookup."""
        results = []
        for contact in contacts:
            props = self._map_contact(contact, field_mapping)
            email = contact.email
            try:
                # Search for existing contact by email
                search_payload = {
                    "filterGroups": [{
                        "filters": [{
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email,
                        }]
                    }],
                    "limit": 1,
                }
                async with session.post(
                    f"{API_BASE}/crm/v3/objects/contacts/search",
                    json=search_payload,
                    headers=self._headers(),
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    data = await resp.json()
                    existing = data.get("results", [])

                if existing:
                    contact_id = existing[0]["id"]
                    # Update
                    async with session.patch(
                        f"{API_BASE}/crm/v3/objects/contacts/{contact_id}",
                        json={"properties": props},
                        headers=self._headers(),
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as resp:
                        if resp.status == 200:
                            results.append(CRMPushResult(
                                email=email, success=True,
                                crm_id=contact_id, created=False,
                            ))
                        else:
                            body = await resp.text()
                            results.append(CRMPushResult(
                                email=email, success=False, error=body,
                            ))
                else:
                    # Create single
                    async with session.post(
                        f"{API_BASE}/crm/v3/objects/contacts",
                        json={"properties": props},
                        headers=self._headers(),
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as resp:
                        if resp.status in (200, 201):
                            body = await resp.json()
                            results.append(CRMPushResult(
                                email=email, success=True,
                                crm_id=body.get("id"), created=True,
                            ))
                        else:
                            body = await resp.text()
                            results.append(CRMPushResult(
                                email=email, success=False, error=body,
                            ))
            except Exception as e:
                results.append(CRMPushResult(
                    email=email, success=False, error=str(e),
                ))
        return results

    async def sync_status(self, crm_ids: List[str]) -> Dict[str, str]:
        """Check if contacts still exist in HubSpot."""
        if self.test_mode:
            return {cid: "active" for cid in crm_ids}

        statuses: Dict[str, str] = {}
        async with aiohttp.ClientSession() as session:
            for cid in crm_ids:
                try:
                    async with session.get(
                        f"{API_BASE}/crm/v3/objects/contacts/{cid}",
                        headers=self._headers(),
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status == 200:
                            statuses[cid] = "active"
                        elif resp.status == 404:
                            statuses[cid] = "deleted"
                        else:
                            statuses[cid] = "unknown"
                except Exception:
                    statuses[cid] = "error"
        return statuses

    async def get_fields(self) -> List[CRMField]:
        """Fetch available contact properties from HubSpot."""
        if self.test_mode:
            return self._test_fields()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_BASE}/crm/v3/properties/contacts",
                    headers=self._headers(),
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"HubSpot get_fields error: {resp.status}")
                        return self._test_fields()
                    data = await resp.json()

            fields = []
            for prop in data.get("results", []):
                if prop.get("hidden"):
                    continue
                fields.append(CRMField(
                    name=prop["name"],
                    label=prop.get("label", prop["name"]),
                    field_type=prop.get("type", "string"),
                    required=prop.get("name") == "email",
                    options=[
                        o.get("value", "") for o in prop.get("options", [])
                    ] if prop.get("options") else [],
                ))
            return fields
        except Exception as e:
            logger.error(f"HubSpot get_fields exception: {e}")
            return self._test_fields()

    # ── Test mode helpers ──────────────────────────

    def _test_push(self, contacts: List[CRMContact]) -> CRMPushSummary:
        results = []
        for i, c in enumerate(contacts):
            results.append(CRMPushResult(
                email=c.email,
                success=True,
                crm_id=f"hs_test_{i+1}",
                created=True,
            ))
        return CRMPushSummary(
            provider="hubspot",
            total=len(contacts),
            created=len(contacts),
            updated=0,
            failed=0,
            status=PushStatus.COMPLETED,
            results=results,
        )

    @staticmethod
    def _test_fields() -> List[CRMField]:
        return [
            CRMField(name="email", label="Email", field_type="string", required=True),
            CRMField(name="firstname", label="First Name", field_type="string"),
            CRMField(name="lastname", label="Last Name", field_type="string"),
            CRMField(name="company", label="Company", field_type="string"),
            CRMField(name="jobtitle", label="Job Title", field_type="string"),
            CRMField(name="phone", label="Phone", field_type="string"),
            CRMField(name="hs_linkedin_url", label="LinkedIn URL", field_type="string"),
            CRMField(name="website", label="Website", field_type="string"),
            CRMField(name="lifecyclestage", label="Lifecycle Stage", field_type="enum",
                     options=["subscriber", "lead", "marketingqualifiedlead",
                              "salesqualifiedlead", "opportunity", "customer"]),
            CRMField(name="hs_lead_status", label="Lead Status", field_type="enum",
                     options=["NEW", "OPEN", "IN_PROGRESS", "CONNECTED", "UNQUALIFIED"]),
        ]
