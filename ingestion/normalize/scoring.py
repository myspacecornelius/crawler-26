"""
Offer Confidence Scoring

Scores how confident we are that a crawled item is a real, active demo incentive.

This is NOT a "lead quality" scorer. The dimensions are:
- Completeness: are the key offer fields populated?
- Reward clarity: explicit dollar amount > vague "incentive available"
- Source quality: JSON-LD structured extraction > regex pattern match
- Offer validity: does it look like a real demo incentive with requirements?
- Recency: when was this last fetched/verified?

The score represents confidence that the offer is real and current,
NOT how attractive or valuable the offer is to users.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List

import yaml

logger = logging.getLogger(__name__)


class OfferScorer:
    """Scores raw offers on a 0.0–1.0 confidence scale."""

    def __init__(self, config_path: str = "ingestion/config/scoring.yaml"):
        self.config = self._load_config(config_path)
        self.weights = self.config.get("weights", {})

    def _load_config(self, path: str) -> dict:
        p = Path(path)
        if p.exists():
            with open(p) as f:
                return yaml.safe_load(f) or {}
        return {
            "weights": {
                "completeness": 0.20,
                "reward_clarity": 0.25,
                "source_quality": 0.20,
                "offer_validity": 0.20,
                "recency": 0.15,
            },
        }

    def score(self, offer: dict) -> float:
        """Score a single offer. Returns 0.0–1.0."""
        total = 0.0

        total += self._score_completeness(offer) * self.weights.get("completeness", 0.20)
        total += self._score_reward_clarity(offer) * self.weights.get("reward_clarity", 0.25)
        total += self._score_source_quality(offer) * self.weights.get("source_quality", 0.20)
        total += self._score_offer_validity(offer) * self.weights.get("offer_validity", 0.20)
        total += self._score_recency(offer) * self.weights.get("recency", 0.15)

        return round(max(0.0, min(1.0, total)), 2)

    def _score_completeness(self, offer: dict) -> float:
        """How many key fields are populated."""
        fields = ["title", "description", "vendor_domain", "reward_value", "cta_url"]
        present = sum(1 for f in fields if offer.get(f))
        return present / len(fields)

    def _score_reward_clarity(self, offer: dict) -> float:
        """How explicit is the reward.

        A clear "$75 Amazon gift card" is high confidence.
        A vague "incentive available" is low confidence.
        No mention of a reward at all = this probably isn't an offer.
        """
        val = str(offer.get("reward_value", "") or "")
        if not val:
            return 0.0
        # Explicit dollar amount
        if "$" in val:
            return 1.0
        # Named reward type without dollar amount
        reward_words = ["gift card", "visa", "amazon", "prepaid", "credit"]
        if any(rw in val.lower() for rw in reward_words):
            return 0.8
        # "free" something
        if "free" in val.lower():
            return 0.6
        # Some text we couldn't parse into a clear reward
        return 0.3

    def _score_source_quality(self, offer: dict) -> float:
        """How was the offer extracted?

        Uses the explicit extraction_method field set by page_extractor,
        not a heuristic based on text length.
        """
        method = offer.get("extraction_method", "")
        if method == "json_ld":
            return 1.0
        if method == "pattern_match":
            return 0.5
        if method == "manual":
            return 0.9
        # Unknown extraction method
        return 0.3

    def _score_offer_validity(self, offer: dict) -> float:
        """Does this look like a real demo incentive vs. a generic product page?

        This is the dimension that prevents the scorer from behaving like
        a lead-extractability scorer. We're checking whether the offer
        structurally resembles a demo incentive.
        """
        validity = 0.0
        text = f"{offer.get('title', '')} {offer.get('description', '')}".lower()

        # Has explicit reward = strong signal this is an incentive
        if offer.get("reward_value"):
            validity += 0.4

        # Title or description mentions demo/trial = good signal
        demo_terms = ["demo", "trial", "evaluation", "proof of concept", "pilot"]
        if any(t in text for t in demo_terms):
            validity += 0.3

        # Mentions qualification/requirements = very strong signal
        req_terms = ["schedule", "book", "qualify", "eligible", "business email", "company size"]
        if any(t in text for t in req_terms):
            validity += 0.2

        # Has a CTA URL = offer is actionable
        if offer.get("cta_url") and offer["cta_url"] != offer.get("source_url"):
            validity += 0.1

        return min(1.0, validity)

    def _score_recency(self, offer: dict) -> float:
        """Score based on when the offer was fetched."""
        fetched = offer.get("fetched_at")
        if not fetched:
            return 0.5
        try:
            dt = datetime.fromisoformat(fetched)
            age_hours = (datetime.now() - dt).total_seconds() / 3600
            if age_hours < 24:
                return 1.0
            if age_hours < 24 * 7:
                return 0.8
            if age_hours < 24 * 30:
                return 0.5
            return 0.2
        except (ValueError, TypeError):
            return 0.5

    def score_batch(self, offers: List[dict]) -> List[dict]:
        """Score all offers and sort by confidence descending."""
        for offer in offers:
            offer["confidence_score"] = self.score(offer)
        return sorted(offers, key=lambda o: o.get("confidence_score", 0), reverse=True)
