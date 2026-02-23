"""
API routes for CRM push integrations (HubSpot, Salesforce).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

from ..auth import get_current_user_id

router = APIRouter(prefix="/crm", tags=["crm"])


# ── Request / Response schemas ─────────────────────

class CRMPushRequest(BaseModel):
    provider: str = Field(description="CRM provider: hubspot | salesforce")
    campaign_id: str = Field(description="LeadFactory campaign ID to pull leads from")
    test_mode: bool = Field(default=False, description="If true, validate but don't hit real CRM API")
    min_score: float = Field(default=0, description="Minimum lead score to include")
    tiers: Optional[List[str]] = Field(default=None, description="Filter by tier: HOT, WARM, COOL")
    field_mapping: Optional[Dict[str, str]] = Field(
        default=None,
        description="Custom field mapping: {lead_field: crm_field}. Overrides defaults.",
    )
    custom_fields: Optional[Dict[str, str]] = Field(
        default=None,
        description="Extra static fields to set on every CRM record",
    )
    # Provider credentials (optional — falls back to env vars)
    api_key: Optional[str] = Field(default=None, description="HubSpot API key (private app token)")
    sf_client_id: Optional[str] = Field(default=None, description="Salesforce client ID")
    sf_client_secret: Optional[str] = Field(default=None, description="Salesforce client secret")
    sf_instance_url: Optional[str] = Field(default=None, description="Salesforce instance URL")
    sf_access_token: Optional[str] = Field(default=None, description="Pre-obtained Salesforce access token")


class CRMPushResultItem(BaseModel):
    email: str
    success: bool
    crm_id: Optional[str] = None
    error: Optional[str] = None
    created: bool = True


class CRMPushResponse(BaseModel):
    provider: str
    total: int
    created: int
    updated: int
    failed: int
    status: str
    results: List[CRMPushResultItem]
    errors: List[str]


class CRMStatusRequest(BaseModel):
    provider: str
    crm_ids: List[str]
    test_mode: bool = False
    api_key: Optional[str] = None
    sf_client_id: Optional[str] = None
    sf_client_secret: Optional[str] = None
    sf_instance_url: Optional[str] = None
    sf_access_token: Optional[str] = None


class CRMFieldItem(BaseModel):
    name: str
    label: str
    field_type: str
    required: bool
    options: List[str]


class CRMFieldMappingItem(BaseModel):
    lead_field: str
    crm_field: str


# ── Helpers ────────────────────────────────────────

def _provider_kwargs(data, provider: str) -> dict:
    """Extract provider-specific kwargs from the request."""
    if provider == "hubspot":
        kw = {}
        if data.api_key:
            kw["api_key"] = data.api_key
        return kw
    elif provider == "salesforce":
        kw = {}
        if data.sf_client_id:
            kw["client_id"] = data.sf_client_id
        if data.sf_client_secret:
            kw["client_secret"] = data.sf_client_secret
        if data.sf_instance_url:
            kw["instance_url"] = data.sf_instance_url
        if data.sf_access_token:
            kw["access_token"] = data.sf_access_token
        return kw
    return {}


# ── Endpoints ──────────────────────────────────────

@router.post("/push", response_model=CRMPushResponse)
async def push_to_crm(
    data: CRMPushRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Push leads from a campaign to a CRM provider.

    Supports HubSpot (Contacts API v3) and Salesforce (REST API).
    Set test_mode=true to validate without hitting real APIs.
    """
    from ..database import async_session
    from ..models import Campaign, Lead
    from sqlalchemy import select
    from integrations.manager import CRMManager

    if data.provider not in ("hubspot", "salesforce"):
        raise HTTPException(status_code=400, detail=f"Unsupported CRM provider: {data.provider}")

    # Verify campaign belongs to user
    async with async_session() as session:
        result = await session.execute(
            select(Campaign).where(
                Campaign.id == data.campaign_id,
                Campaign.user_id == user_id,
            )
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Fetch leads
        result = await session.execute(
            select(Lead).where(Lead.campaign_id == data.campaign_id)
        )
        db_leads = result.scalars().all()

    if not db_leads:
        raise HTTPException(status_code=400, detail="No leads in this campaign")

    # Build CRM manager
    try:
        kwargs = _provider_kwargs(data, data.provider)
        manager = CRMManager(
            provider_name=data.provider,
            test_mode=data.test_mode,
            **kwargs,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Prepare contacts
    contacts = manager.prepare_contacts(
        db_leads,
        min_score=data.min_score,
        tiers=data.tiers,
        custom_fields=data.custom_fields,
    )

    if not contacts:
        raise HTTPException(
            status_code=400,
            detail="No leads with valid emails match the criteria",
        )

    # Push
    try:
        summary = await manager.push(contacts, field_mapping=data.field_mapping)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"CRM provider error: {str(e)}")

    return CRMPushResponse(
        provider=summary.provider,
        total=summary.total,
        created=summary.created,
        updated=summary.updated,
        failed=summary.failed,
        status=summary.status.value,
        results=[
            CRMPushResultItem(
                email=r.email,
                success=r.success,
                crm_id=r.crm_id,
                error=r.error,
                created=r.created,
            )
            for r in summary.results
        ],
        errors=summary.errors,
    )


@router.post("/status")
async def crm_sync_status(
    data: CRMStatusRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Check the status of previously-pushed CRM records."""
    from integrations.manager import CRMManager

    try:
        kwargs = _provider_kwargs(data, data.provider)
        manager = CRMManager(
            provider_name=data.provider,
            test_mode=data.test_mode,
            **kwargs,
        )
        statuses = await manager.sync_status(data.crm_ids)
        return {"provider": data.provider, "statuses": statuses}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"CRM provider error: {str(e)}")


@router.get("/fields/{provider}")
async def get_crm_fields(
    provider: str,
    test_mode: bool = True,
    api_key: Optional[str] = None,
    sf_access_token: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
):
    """
    Get available CRM fields for the given provider.
    Useful for building field-mapping UI.
    """
    from integrations.manager import CRMManager

    kwargs = {}
    if provider == "hubspot" and api_key:
        kwargs["api_key"] = api_key
    elif provider == "salesforce" and sf_access_token:
        kwargs["access_token"] = sf_access_token

    try:
        manager = CRMManager(provider_name=provider, test_mode=test_mode, **kwargs)
        fields = await manager.get_fields()
        return {
            "provider": provider,
            "fields": [
                CRMFieldItem(
                    name=f.name,
                    label=f.label,
                    field_type=f.field_type,
                    required=f.required,
                    options=f.options,
                )
                for f in fields
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"CRM provider error: {str(e)}")


@router.get("/field-mapping/defaults")
async def get_default_field_mapping(
    user_id: str = Depends(get_current_user_id),
):
    """Return the default Lead → CRM field mapping."""
    from integrations.crm_base import DEFAULT_FIELD_MAPPING
    return {
        "mapping": [
            CRMFieldMappingItem(lead_field=k, crm_field=v)
            for k, v in DEFAULT_FIELD_MAPPING.items()
        ]
    }
