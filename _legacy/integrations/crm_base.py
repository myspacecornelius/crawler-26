"""
Abstract CRM provider interface and shared data models.
Mirrors the outreach/base.py pattern for CRM push integrations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class PushStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class CRMContact:
    """A single contact/lead to push to a CRM."""
    email: str
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    role: str = ""
    phone: str = ""
    linkedin: str = ""
    website: str = ""
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CRMPushResult:
    """Result from pushing a single contact to CRM."""
    email: str
    success: bool
    crm_id: Optional[str] = None
    error: Optional[str] = None
    created: bool = True  # True = created, False = updated


@dataclass
class CRMPushSummary:
    """Aggregated results from a batch push operation."""
    provider: str = ""
    total: int = 0
    created: int = 0
    updated: int = 0
    failed: int = 0
    status: PushStatus = PushStatus.COMPLETED
    results: List[CRMPushResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class CRMField:
    """Describes a field available in the CRM."""
    name: str
    label: str
    field_type: str = "string"  # string, number, date, boolean, enum
    required: bool = False
    options: List[str] = field(default_factory=list)


# Default mapping: LeadFactory Lead field → CRM-agnostic canonical name
DEFAULT_FIELD_MAPPING: Dict[str, str] = {
    "email": "email",
    "first_name": "firstname",
    "last_name": "lastname",
    "company": "company",
    "role": "jobtitle",
    "phone": "phone",
    "linkedin": "linkedin_url",
    "website": "website",
}


class CRMProvider(ABC):
    """Abstract base class for CRM integrations."""

    @abstractmethod
    async def push_leads(
        self,
        contacts: List[CRMContact],
        field_mapping: Optional[Dict[str, str]] = None,
    ) -> CRMPushSummary:
        """
        Push a list of contacts to the CRM.
        field_mapping maps CRMContact attribute names → CRM field names.
        Returns a summary with per-contact results.
        """
        ...

    @abstractmethod
    async def sync_status(self, crm_ids: List[str]) -> Dict[str, str]:
        """
        Check the status of previously-pushed contacts.
        Returns {crm_id: status_string}.
        """
        ...

    @abstractmethod
    async def get_fields(self) -> List[CRMField]:
        """
        Return the list of available fields in the CRM
        so the UI can build a field-mapping interface.
        """
        ...
