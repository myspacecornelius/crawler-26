"""
Load and validate vertical configuration files.

Each vertical (VC, PE, family office, etc.) is defined by a YAML config
that tells the engine what to scrape, how to score, and which patterns to use.
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


VERTICALS_DIR = Path(__file__).parent


@dataclass
class SeedSource:
    """A source of seed data (CSV file, GitHub list, etc.)."""
    type: str  # "csv", "github", "api"
    path: str = ""
    urls: List[str] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class ScoringConfig:
    """Scoring weights for lead prioritization."""
    has_email: int = 20
    has_linkedin: int = 10
    role_match_bonus: int = 15
    priority_roles: List[str] = field(default_factory=list)
    depriority_roles: List[str] = field(default_factory=list)


@dataclass
class VerticalConfig:
    """Complete configuration for a single industry vertical."""
    name: str
    slug: str
    description: str
    seed_sources: List[SeedSource] = field(default_factory=list)
    search_queries: List[str] = field(default_factory=list)
    team_page_keywords: List[str] = field(default_factory=lambda: [
        "team", "people", "about", "leadership", "partners",
        "professionals", "staff", "who-we-are", "our-team",
    ])
    role_keywords: List[str] = field(default_factory=lambda: [
        "partner", "director", "principal", "associate",
        "analyst", "managing", "founder", "ceo", "cto",
        "vice president", "vp", "head of",
    ])
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    adapters: List[str] = field(default_factory=list)
    default_check_size: str = "N/A"
    default_sectors: List[str] = field(default_factory=list)

    @property
    def config_path(self) -> Path:
        return VERTICALS_DIR / f"{self.slug}.yaml"


def load_vertical(slug: str) -> VerticalConfig:
    """Load a vertical config from its YAML file."""
    path = VERTICALS_DIR / f"{slug}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Vertical config not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    seed_sources = []
    for src in raw.get("seed_sources", []):
        seed_sources.append(SeedSource(
            type=src.get("type", "csv"),
            path=src.get("path", ""),
            urls=src.get("urls", []),
            headers=src.get("headers", {}),
        ))

    scoring_raw = raw.get("scoring", {})
    scoring = ScoringConfig(
        has_email=scoring_raw.get("has_email", 20),
        has_linkedin=scoring_raw.get("has_linkedin", 10),
        role_match_bonus=scoring_raw.get("role_match_bonus", 15),
        priority_roles=scoring_raw.get("priority_roles", []),
        depriority_roles=scoring_raw.get("depriority_roles", []),
    )

    return VerticalConfig(
        name=raw.get("name", slug),
        slug=slug,
        description=raw.get("description", ""),
        seed_sources=seed_sources,
        search_queries=raw.get("search_queries", []),
        team_page_keywords=raw.get("team_page_keywords", [
            "team", "people", "about", "leadership", "partners",
            "professionals", "staff", "who-we-are", "our-team",
        ]),
        role_keywords=raw.get("role_keywords", [
            "partner", "director", "principal", "associate",
            "analyst", "managing", "founder", "ceo", "cto",
            "vice president", "vp", "head of",
        ]),
        scoring=scoring,
        adapters=raw.get("adapters", []),
        default_check_size=raw.get("default_check_size", "N/A"),
        default_sectors=raw.get("default_sectors", []),
    )


def list_verticals() -> List[str]:
    """List all available vertical slugs."""
    slugs = []
    for f in sorted(VERTICALS_DIR.glob("*.yaml")):
        slugs.append(f.stem)
    return slugs
