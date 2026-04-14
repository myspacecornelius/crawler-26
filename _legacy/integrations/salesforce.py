"""
Salesforce CRM integration — REST API with OAuth2.
Docs: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/

Requires env vars:
  SALESFORCE_CLIENT_ID
  SALESFORCE_CLIENT_SECRET
  SALESFORCE_INSTANCE_URL  (e.g. https://yourorg.my.salesforce.com)
  SALESFORCE_USERNAME      (for JWT/password flow)
  SALESFORCE_PASSWORD       (for password flow, optional)
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

API_VERSION = "v59.0"

# Salesforce standard Lead field names
SALESFORCE_FIELD_MAP: Dict[str, str] = {
    "email": "Email",
    "firstname": "FirstName",
    "lastname": "LastName",
    "company": "Company",
    "jobtitle": "Title",
    "phone": "Phone",
    "linkedin_url": "LinkedIn_URL__c",
    "website": "Website",
}


class SalesforceProvider(CRMProvider):
    """Salesforce CRM integration using REST API."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        instance_url: Optional[str] = None,
        access_token: Optional[str] = None,
        test_mode: bool = False,
    ):
        self.client_id = client_id or os.getenv("SALESFORCE_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("SALESFORCE_CLIENT_SECRET", "")
        self.instance_url = (
            instance_url or os.getenv("SALESFORCE_INSTANCE_URL", "")
        ).rstrip("/")
        self._access_token = access_token or ""
        self.test_mode = test_mode

        if not self.test_mode and not self._access_token and not self.client_id:
            logger.warning("No Salesforce credentials set — CRM calls will fail")

    async def _get_access_token(self) -> str:
        """Obtain OAuth2 access token using client_credentials or password flow."""
        if self._access_token:
            return self._access_token

        token_url = f"{self.instance_url}/services/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        # Fall back to password flow if username/password are set
        username = os.getenv("SALESFORCE_USERNAME", "")
        password = os.getenv("SALESFORCE_PASSWORD", "")
        if username and password:
            payload["grant_type"] = "password"
            payload["username"] = username
            payload["password"] = password

        async with aiohttp.ClientSession() as session:
            async with session.post(
                token_url,
                data=payload,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise Exception(f"Salesforce OAuth error {resp.status}: {body}")
                data = await resp.json()

        self._access_token = data["access_token"]
        # Update instance URL if returned (login flow)
        if "instance_url" in data:
            self.instance_url = data["instance_url"].rstrip("/")

        return self._access_token

    def _headers(self, token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _map_contact(
        self,
        contact: CRMContact,
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> dict:
        """Convert CRMContact to Salesforce Lead fields dict."""
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

        mapping = dict(DEFAULT_FIELD_MAPPING)
        if field_mapping:
            mapping.update(field_mapping)

        fields: Dict[str, str] = {}
        for lead_attr, canonical_name in mapping.items():
            sf_field = SALESFORCE_FIELD_MAP.get(canonical_name, canonical_name)
            value = canonical.get(canonical_name, "")
            if not value and hasattr(contact, lead_attr):
                value = getattr(contact, lead_attr, "")
            if value:
                fields[sf_field] = str(value)

        # Salesforce requires Company and LastName on Lead
        if "Company" not in fields or not fields["Company"]:
            fields["Company"] = contact.company or "Unknown"
        if "LastName" not in fields or not fields["LastName"]:
            fields["LastName"] = contact.last_name or contact.email.split("@")[0]

        # Custom fields
        for k, v in contact.custom_fields.items():
            if v:
                fields[k] = str(v)

        return fields

    async def push_leads(
        self,
        contacts: List[CRMContact],
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> CRMPushSummary:
        """Push contacts as Salesforce Lead objects."""
        if self.test_mode:
            return self._test_push(contacts)

        token = await self._get_access_token()
        base_url = f"{self.instance_url}/services/data/{API_VERSION}"

        results: List[CRMPushResult] = []
        errors: List[str] = []

        # Use Composite API for batches (up to 200 sub-requests)
        for i in range(0, len(contacts), 200):
            batch = contacts[i:i + 200]
            composite_requests = []
            for idx, contact in enumerate(batch):
                sf_fields = self._map_contact(contact, field_mapping)
                composite_requests.append({
                    "method": "POST",
                    "url": f"/services/data/{API_VERSION}/sobjects/Lead",
                    "referenceId": f"lead_{i + idx}",
                    "body": sf_fields,
                })

            payload = {"compositeRequest": composite_requests}

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{base_url}/composite",
                        json=payload,
                        headers=self._headers(token),
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        body = await resp.json()

                        if resp.status == 200:
                            for j, sub in enumerate(body.get("compositeResponse", [])):
                                contact = batch[j]
                                if sub.get("httpStatusCode") in (200, 201):
                                    sub_body = sub.get("body", {})
                                    results.append(CRMPushResult(
                                        email=contact.email,
                                        success=True,
                                        crm_id=sub_body.get("id"),
                                        created=True,
                                    ))
                                else:
                                    err_msgs = sub.get("body", [])
                                    err = err_msgs[0].get("message", "Unknown error") if isinstance(err_msgs, list) and err_msgs else str(err_msgs)
                                    # Check for duplicate — try upsert
                                    if "DUPLICATE" in str(err).upper():
                                        upsert_result = await self._upsert_single(
                                            session, token, base_url, contact, field_mapping
                                        )
                                        results.append(upsert_result)
                                    else:
                                        results.append(CRMPushResult(
                                            email=contact.email,
                                            success=False,
                                            error=err,
                                        ))
                                        errors.append(f"{contact.email}: {err}")
                        else:
                            err = body.get("message", f"HTTP {resp.status}")
                            if isinstance(body, list):
                                err = body[0].get("message", str(body)) if body else str(resp.status)
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
            provider="salesforce",
            total=len(contacts),
            created=created,
            updated=updated,
            failed=failed,
            status=status,
            results=results,
            errors=errors,
        )

    async def _upsert_single(
        self,
        session: aiohttp.ClientSession,
        token: str,
        base_url: str,
        contact: CRMContact,
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> CRMPushResult:
        """Upsert a single Lead by Email external ID."""
        sf_fields = self._map_contact(contact, field_mapping)
        email = contact.email
        try:
            async with session.patch(
                f"{base_url}/sobjects/Lead/Email/{email}",
                json=sf_fields,
                headers=self._headers(token),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status in (200, 201, 204):
                    body = await resp.json() if resp.status != 204 else {}
                    return CRMPushResult(
                        email=email,
                        success=True,
                        crm_id=body.get("id", ""),
                        created=resp.status == 201,
                    )
                else:
                    body = await resp.text()
                    return CRMPushResult(
                        email=email, success=False, error=body,
                    )
        except Exception as e:
            return CRMPushResult(email=email, success=False, error=str(e))

    async def sync_status(self, crm_ids: List[str]) -> Dict[str, str]:
        """Check Lead status in Salesforce."""
        if self.test_mode:
            return {cid: "Open - Not Contacted" for cid in crm_ids}

        token = await self._get_access_token()
        base_url = f"{self.instance_url}/services/data/{API_VERSION}"
        statuses: Dict[str, str] = {}

        async with aiohttp.ClientSession() as session:
            for cid in crm_ids:
                try:
                    async with session.get(
                        f"{base_url}/sobjects/Lead/{cid}?fields=Status",
                        headers=self._headers(token),
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            statuses[cid] = data.get("Status", "unknown")
                        elif resp.status == 404:
                            statuses[cid] = "deleted"
                        else:
                            statuses[cid] = "unknown"
                except Exception:
                    statuses[cid] = "error"
        return statuses

    async def get_fields(self) -> List[CRMField]:
        """Fetch available Lead fields from Salesforce describe."""
        if self.test_mode:
            return self._test_fields()

        try:
            token = await self._get_access_token()
            base_url = f"{self.instance_url}/services/data/{API_VERSION}"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{base_url}/sobjects/Lead/describe",
                    headers=self._headers(token),
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Salesforce describe error: {resp.status}")
                        return self._test_fields()
                    data = await resp.json()

            fields = []
            for f in data.get("fields", []):
                if not f.get("createable"):
                    continue
                field_type = f.get("type", "string")
                type_map = {
                    "string": "string", "email": "string", "url": "string",
                    "phone": "string", "textarea": "string",
                    "double": "number", "int": "number", "currency": "number",
                    "date": "date", "datetime": "date",
                    "boolean": "boolean",
                    "picklist": "enum", "multipicklist": "enum",
                }
                fields.append(CRMField(
                    name=f["name"],
                    label=f.get("label", f["name"]),
                    field_type=type_map.get(field_type, "string"),
                    required=not f.get("nillable", True) and not f.get("defaultedOnCreate", False),
                    options=[
                        pv.get("value", "") for pv in f.get("picklistValues", [])
                        if pv.get("active")
                    ] if field_type in ("picklist", "multipicklist") else [],
                ))
            return fields
        except Exception as e:
            logger.error(f"Salesforce get_fields exception: {e}")
            return self._test_fields()

    # ── Test mode helpers ──────────────────────────

    def _test_push(self, contacts: List[CRMContact]) -> CRMPushSummary:
        results = []
        for i, c in enumerate(contacts):
            results.append(CRMPushResult(
                email=c.email,
                success=True,
                crm_id=f"00Q_test_{i+1:04d}",
                created=True,
            ))
        return CRMPushSummary(
            provider="salesforce",
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
            CRMField(name="Email", label="Email", field_type="string", required=False),
            CRMField(name="FirstName", label="First Name", field_type="string"),
            CRMField(name="LastName", label="Last Name", field_type="string", required=True),
            CRMField(name="Company", label="Company", field_type="string", required=True),
            CRMField(name="Title", label="Title", field_type="string"),
            CRMField(name="Phone", label="Phone", field_type="string"),
            CRMField(name="Website", label="Website", field_type="string"),
            CRMField(name="Status", label="Lead Status", field_type="enum",
                     options=["Open - Not Contacted", "Working - Contacted",
                              "Closed - Converted", "Closed - Not Converted"]),
            CRMField(name="LeadSource", label="Lead Source", field_type="enum",
                     options=["Web", "Phone Inquiry", "Partner Referral", "Other"]),
            CRMField(name="Description", label="Description", field_type="string"),
        ]
