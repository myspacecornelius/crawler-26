"""
Base outreach provider interface and data models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class OutreachStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class EmailStep:
    """A single step in an outreach sequence."""
    subject: str
    body: str  # HTML or plain text
    delay_days: int = 0  # Days to wait after previous step
    step_number: int = 1


@dataclass
class OutreachSequence:
    """A multi-step email outreach sequence."""
    name: str
    steps: List[EmailStep] = field(default_factory=list)
    from_email: str = ""
    from_name: str = ""
    reply_to: str = ""
    tracking: bool = True


@dataclass
class OutreachLead:
    """A lead to be added to an outreach campaign."""
    email: str
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    role: str = ""
    linkedin: str = ""
    custom_vars: dict = field(default_factory=dict)


@dataclass
class CampaignStats:
    """Stats returned from outreach providers."""
    total_leads: int = 0
    emails_sent: int = 0
    opens: int = 0
    clicks: int = 0
    replies: int = 0
    bounces: int = 0
    unsubscribes: int = 0
    open_rate: float = 0.0
    reply_rate: float = 0.0


class OutreachProvider(ABC):
    """Abstract base class for outreach integrations."""

    @abstractmethod
    async def create_campaign(self, sequence: OutreachSequence) -> str:
        """Create a campaign/sequence. Returns campaign ID."""
        ...

    @abstractmethod
    async def add_leads(self, campaign_id: str, leads: List[OutreachLead]) -> int:
        """Add leads to a campaign. Returns count added."""
        ...

    @abstractmethod
    async def start_campaign(self, campaign_id: str) -> bool:
        """Activate/start a campaign."""
        ...

    @abstractmethod
    async def pause_campaign(self, campaign_id: str) -> bool:
        """Pause a campaign."""
        ...

    @abstractmethod
    async def get_stats(self, campaign_id: str) -> CampaignStats:
        """Get campaign analytics."""
        ...

    @abstractmethod
    async def list_campaigns(self) -> List[dict]:
        """List all campaigns."""
        ...
