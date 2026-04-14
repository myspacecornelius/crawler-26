"""
Tests for CRM integration module (HubSpot + Salesforce).
Tests use test_mode=True so no real API calls are made.
Run with: python3 -m pytest tests/test_crm.py -v
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from integrations.crm_base import (
    CRMProvider, CRMContact, CRMPushResult, CRMPushSummary,
    CRMField, PushStatus, DEFAULT_FIELD_MAPPING,
)
from integrations.hubspot import HubSpotProvider, HUBSPOT_FIELD_MAP
from integrations.salesforce import SalesforceProvider, SALESFORCE_FIELD_MAP
from integrations.manager import CRMManager, get_crm_provider, db_lead_to_crm_contact


# ── Fixtures ───────────────────────────────────────

def make_contacts(n=3):
    """Create a list of test CRMContact objects."""
    contacts = []
    for i in range(n):
        contacts.append(CRMContact(
            email=f"test{i+1}@example.com",
            first_name=f"First{i+1}",
            last_name=f"Last{i+1}",
            company=f"Company{i+1}",
            role=f"Partner",
            phone=f"555-000{i+1}",
            linkedin=f"https://linkedin.com/in/test{i+1}",
            website=f"https://company{i+1}.com",
            custom_fields={"sectors": "SaaS, Fintech"},
        ))
    return contacts


class FakeDBLead:
    """Mimics the Lead ORM model for testing."""
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "John Doe")
        self.email = kwargs.get("email", "john@example.com")
        self.fund = kwargs.get("fund", "Acme Capital")
        self.role = kwargs.get("role", "Managing Partner")
        self.phone = kwargs.get("phone", "555-1234")
        self.linkedin = kwargs.get("linkedin", "https://linkedin.com/in/johndoe")
        self.website = kwargs.get("website", "https://acme.vc")
        self.sectors = kwargs.get("sectors", "SaaS, AI")
        self.check_size = kwargs.get("check_size", "$1M-$5M")
        self.stage = kwargs.get("stage", "Series A")
        self.score = kwargs.get("score", 85.0)
        self.tier = kwargs.get("tier", "HOT")
        self.source = kwargs.get("source", "https://acme.vc/team")


# ── CRM Base Tests ─────────────────────────────────

class TestCRMBase:
    def test_crm_contact_creation(self):
        c = CRMContact(email="a@b.com", first_name="A", last_name="B")
        assert c.email == "a@b.com"
        assert c.custom_fields == {}

    def test_push_status_enum(self):
        assert PushStatus.COMPLETED.value == "completed"
        assert PushStatus.PARTIAL.value == "partial"
        assert PushStatus.FAILED.value == "failed"

    def test_default_field_mapping(self):
        assert "email" in DEFAULT_FIELD_MAPPING
        assert "first_name" in DEFAULT_FIELD_MAPPING
        assert DEFAULT_FIELD_MAPPING["email"] == "email"

    def test_push_result_dataclass(self):
        r = CRMPushResult(email="a@b.com", success=True, crm_id="123", created=True)
        assert r.success
        assert r.crm_id == "123"

    def test_push_summary_dataclass(self):
        s = CRMPushSummary(provider="hubspot", total=5, created=3, updated=1, failed=1)
        assert s.total == 5
        assert s.status == PushStatus.COMPLETED

    def test_crm_field_dataclass(self):
        f = CRMField(name="email", label="Email", field_type="string", required=True)
        assert f.required
        assert f.options == []


# ── HubSpot Provider Tests ─────────────────────────

class TestHubSpotProvider:
    def test_init_test_mode(self):
        provider = HubSpotProvider(test_mode=True)
        assert provider.test_mode is True

    def test_init_with_api_key(self):
        provider = HubSpotProvider(api_key="test-key-123")
        assert provider.api_key == "test-key-123"

    def test_map_contact(self):
        provider = HubSpotProvider(test_mode=True)
        contact = CRMContact(
            email="test@example.com",
            first_name="Jane",
            last_name="Doe",
            company="Acme VC",
            role="Partner",
        )
        props = provider._map_contact(contact)
        assert props["email"] == "test@example.com"
        assert props["firstname"] == "Jane"
        assert props["lastname"] == "Doe"
        assert props["company"] == "Acme VC"
        assert props["jobtitle"] == "Partner"

    def test_map_contact_custom_fields(self):
        provider = HubSpotProvider(test_mode=True)
        contact = CRMContact(
            email="test@example.com",
            custom_fields={"hs_lead_status": "NEW", "custom_prop": "value"},
        )
        props = provider._map_contact(contact)
        assert props["hs_lead_status"] == "NEW"
        assert props["custom_prop"] == "value"

    def test_map_contact_custom_mapping(self):
        provider = HubSpotProvider(test_mode=True)
        contact = CRMContact(email="t@e.com", first_name="A", company="B")
        mapping = {"email": "email", "first_name": "firstname", "company": "my_custom_company"}
        props = provider._map_contact(contact, field_mapping=mapping)
        assert "my_custom_company" in props or "company" in props

    def test_push_leads_test_mode(self):
        async def run():
            provider = HubSpotProvider(test_mode=True)
            contacts = make_contacts(5)
            summary = await provider.push_leads(contacts)
            assert summary.provider == "hubspot"
            assert summary.total == 5
            assert summary.created == 5
            assert summary.updated == 0
            assert summary.failed == 0
            assert summary.status == PushStatus.COMPLETED
            assert len(summary.results) == 5
            for i, r in enumerate(summary.results):
                assert r.success
                assert r.crm_id == f"hs_test_{i+1}"
                assert r.email == f"test{i+1}@example.com"
        asyncio.run(run())

    def test_sync_status_test_mode(self):
        async def run():
            provider = HubSpotProvider(test_mode=True)
            statuses = await provider.sync_status(["id1", "id2", "id3"])
            assert statuses == {"id1": "active", "id2": "active", "id3": "active"}
        asyncio.run(run())

    def test_get_fields_test_mode(self):
        async def run():
            provider = HubSpotProvider(test_mode=True)
            fields = await provider.get_fields()
            assert len(fields) > 0
            names = [f.name for f in fields]
            assert "email" in names
            assert "firstname" in names
            assert "lastname" in names
            assert "company" in names
            email_field = next(f for f in fields if f.name == "email")
            assert email_field.required
        asyncio.run(run())

    def test_push_empty_list(self):
        async def run():
            provider = HubSpotProvider(test_mode=True)
            summary = await provider.push_leads([])
            assert summary.total == 0
            assert summary.created == 0
        asyncio.run(run())


# ── Salesforce Provider Tests ──────────────────────

class TestSalesforceProvider:
    def test_init_test_mode(self):
        provider = SalesforceProvider(test_mode=True)
        assert provider.test_mode is True

    def test_init_with_credentials(self):
        provider = SalesforceProvider(
            client_id="cid",
            client_secret="csecret",
            instance_url="https://test.salesforce.com",
        )
        assert provider.client_id == "cid"
        assert provider.instance_url == "https://test.salesforce.com"

    def test_map_contact(self):
        provider = SalesforceProvider(test_mode=True)
        contact = CRMContact(
            email="test@example.com",
            first_name="Jane",
            last_name="Doe",
            company="Acme VC",
            role="VP",
        )
        fields = provider._map_contact(contact)
        assert fields["Email"] == "test@example.com"
        assert fields["FirstName"] == "Jane"
        assert fields["LastName"] == "Doe"
        assert fields["Company"] == "Acme VC"
        assert fields["Title"] == "VP"

    def test_map_contact_requires_company_lastname(self):
        provider = SalesforceProvider(test_mode=True)
        contact = CRMContact(email="test@example.com")
        fields = provider._map_contact(contact)
        assert "Company" in fields
        assert "LastName" in fields
        assert fields["Company"] == "Unknown"
        assert fields["LastName"] == "test"

    def test_map_contact_custom_fields(self):
        provider = SalesforceProvider(test_mode=True)
        contact = CRMContact(
            email="test@example.com",
            last_name="Doe",
            company="Acme",
            custom_fields={"LeadSource": "Web", "Description": "From LeadFactory"},
        )
        fields = provider._map_contact(contact)
        assert fields["LeadSource"] == "Web"
        assert fields["Description"] == "From LeadFactory"

    def test_push_leads_test_mode(self):
        async def run():
            provider = SalesforceProvider(test_mode=True)
            contacts = make_contacts(5)
            summary = await provider.push_leads(contacts)
            assert summary.provider == "salesforce"
            assert summary.total == 5
            assert summary.created == 5
            assert summary.updated == 0
            assert summary.failed == 0
            assert summary.status == PushStatus.COMPLETED
            assert len(summary.results) == 5
            for i, r in enumerate(summary.results):
                assert r.success
                assert r.crm_id == f"00Q_test_{i+1:04d}"
        asyncio.run(run())

    def test_sync_status_test_mode(self):
        async def run():
            provider = SalesforceProvider(test_mode=True)
            statuses = await provider.sync_status(["001", "002"])
            assert statuses == {"001": "Open - Not Contacted", "002": "Open - Not Contacted"}
        asyncio.run(run())

    def test_get_fields_test_mode(self):
        async def run():
            provider = SalesforceProvider(test_mode=True)
            fields = await provider.get_fields()
            assert len(fields) > 0
            names = [f.name for f in fields]
            assert "Email" in names
            assert "FirstName" in names
            assert "Company" in names
            company_field = next(f for f in fields if f.name == "Company")
            assert company_field.required
        asyncio.run(run())

    def test_push_empty_list(self):
        async def run():
            provider = SalesforceProvider(test_mode=True)
            summary = await provider.push_leads([])
            assert summary.total == 0
        asyncio.run(run())


# ── CRM Manager Tests ─────────────────────────────

class TestCRMManager:
    def test_get_crm_provider_hubspot(self):
        provider = get_crm_provider("hubspot", test_mode=True)
        assert isinstance(provider, HubSpotProvider)

    def test_get_crm_provider_salesforce(self):
        provider = get_crm_provider("salesforce", test_mode=True)
        assert isinstance(provider, SalesforceProvider)

    def test_get_crm_provider_unknown(self):
        with pytest.raises(ValueError, match="Unknown CRM provider"):
            get_crm_provider("zoho")

    def test_db_lead_to_crm_contact(self):
        lead = FakeDBLead()
        contact = db_lead_to_crm_contact(lead)
        assert contact is not None
        assert contact.email == "john@example.com"
        assert contact.first_name == "John"
        assert contact.last_name == "Doe"
        assert contact.company == "Acme Capital"
        assert contact.role == "Managing Partner"
        assert contact.custom_fields["sectors"] == "SaaS, AI"

    def test_db_lead_to_crm_contact_no_email(self):
        lead = FakeDBLead(email="N/A")
        assert db_lead_to_crm_contact(lead) is None

    def test_db_lead_to_crm_contact_invalid_email(self):
        lead = FakeDBLead(email="invalid_no_at")
        assert db_lead_to_crm_contact(lead) is None

    def test_db_lead_to_crm_contact_empty_email(self):
        lead = FakeDBLead(email="")
        assert db_lead_to_crm_contact(lead) is None

    def test_prepare_contacts(self):
        manager = CRMManager(provider_name="hubspot", test_mode=True)
        leads = [
            FakeDBLead(score=90, tier="HOT"),
            FakeDBLead(name="Low Score", email="low@test.com", score=10, tier="COOL"),
            FakeDBLead(name="No Email", email="N/A", score=80, tier="WARM"),
        ]
        contacts = manager.prepare_contacts(leads, min_score=50)
        assert len(contacts) == 1
        assert contacts[0].email == "john@example.com"

    def test_prepare_contacts_tier_filter(self):
        manager = CRMManager(provider_name="hubspot", test_mode=True)
        leads = [
            FakeDBLead(score=90, tier="HOT"),
            FakeDBLead(name="Warm Lead", email="warm@test.com", score=70, tier="WARM"),
            FakeDBLead(name="Cool Lead", email="cool@test.com", score=60, tier="COOL"),
        ]
        contacts = manager.prepare_contacts(leads, tiers=["HOT", "WARM"])
        assert len(contacts) == 2

    def test_push_hubspot(self):
        async def run():
            manager = CRMManager(provider_name="hubspot", test_mode=True)
            contacts = make_contacts(3)
            summary = await manager.push(contacts)
            assert summary.provider == "hubspot"
            assert summary.total == 3
            assert summary.created == 3
            assert summary.status == PushStatus.COMPLETED
        asyncio.run(run())

    def test_push_salesforce(self):
        async def run():
            manager = CRMManager(provider_name="salesforce", test_mode=True)
            contacts = make_contacts(3)
            summary = await manager.push(contacts)
            assert summary.provider == "salesforce"
            assert summary.total == 3
            assert summary.created == 3
        asyncio.run(run())

    def test_push_with_field_mapping(self):
        async def run():
            manager = CRMManager(provider_name="hubspot", test_mode=True)
            contacts = make_contacts(2)
            mapping = {"email": "email", "company": "custom_company_field"}
            summary = await manager.push(contacts, field_mapping=mapping)
            assert summary.total == 2
            assert summary.created == 2
        asyncio.run(run())

    def test_get_fields_hubspot(self):
        async def run():
            manager = CRMManager(provider_name="hubspot", test_mode=True)
            fields = await manager.get_fields()
            assert len(fields) > 0
            assert any(f.name == "email" for f in fields)
        asyncio.run(run())

    def test_get_fields_salesforce(self):
        async def run():
            manager = CRMManager(provider_name="salesforce", test_mode=True)
            fields = await manager.get_fields()
            assert len(fields) > 0
            assert any(f.name == "Email" for f in fields)
        asyncio.run(run())

    def test_sync_status(self):
        async def run():
            manager = CRMManager(provider_name="hubspot", test_mode=True)
            statuses = await manager.sync_status(["id1", "id2"])
            assert all(v == "active" for v in statuses.values())
        asyncio.run(run())

    def test_full_pipeline(self):
        """End-to-end: DB leads -> prepare -> push -> verify."""
        async def run():
            manager = CRMManager(provider_name="hubspot", test_mode=True)
            db_leads = [
                FakeDBLead(name="Alice Smith", email="alice@fund.com", score=95, tier="HOT"),
                FakeDBLead(name="Bob Jones", email="bob@fund.com", score=80, tier="WARM"),
                FakeDBLead(name="No Email", email="N/A", score=90, tier="HOT"),
                FakeDBLead(name="Low Score", email="low@fund.com", score=10, tier="COOL"),
            ]
            contacts = manager.prepare_contacts(db_leads, min_score=50, tiers=["HOT", "WARM"])
            assert len(contacts) == 2

            summary = await manager.push(contacts)
            assert summary.total == 2
            assert summary.created == 2
            assert summary.failed == 0
            assert summary.status == PushStatus.COMPLETED

            crm_ids = [r.crm_id for r in summary.results]
            statuses = await manager.sync_status(crm_ids)
            assert len(statuses) == 2
        asyncio.run(run())


# ── Field Mapping Tests ────────────────────────────

class TestFieldMapping:
    def test_hubspot_field_map_covers_defaults(self):
        """Every canonical field in DEFAULT_FIELD_MAPPING has a HubSpot mapping."""
        for canonical in DEFAULT_FIELD_MAPPING.values():
            assert canonical in HUBSPOT_FIELD_MAP, f"Missing HubSpot mapping for '{canonical}'"

    def test_salesforce_field_map_covers_defaults(self):
        """Every canonical field in DEFAULT_FIELD_MAPPING has a Salesforce mapping."""
        for canonical in DEFAULT_FIELD_MAPPING.values():
            assert canonical in SALESFORCE_FIELD_MAP, f"Missing Salesforce mapping for '{canonical}'"

    def test_hubspot_email_maps_to_email(self):
        assert HUBSPOT_FIELD_MAP["email"] == "email"

    def test_salesforce_email_maps_to_Email(self):
        assert SALESFORCE_FIELD_MAP["email"] == "Email"
