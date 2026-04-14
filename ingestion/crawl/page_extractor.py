"""
Page Extractor — HTML → raw offer data.

Extracts demo incentive offers from a web page using:
1. JSON-LD / Schema.org structured data (filtered for demo incentive signals)
2. Text pattern matching for reward amounts + CTA links

Every raw offer dict includes an `extraction_method` field so the scorer
can weight structured data higher than pattern matches.
"""

import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Signals that a JSON-LD item is about a demo incentive,
# not just a generic product description.
DEMO_INCENTIVE_SIGNALS = [
    "demo", "gift card", "incentive", "reward", "trial",
    "free", "evaluation", "credit", "prepaid", "visa",
    "amazon", "bonus", "perk",
]

# Patterns that suggest a reward value
REWARD_PATTERNS = [
    r'\$\d+[\d,]*\s*(?:gift\s*card|visa|amazon|prepaid|reward)',
    r'(?:gift\s*card|visa|amazon|prepaid)\s*(?:worth\s*)?\$\d+[\d,]*',
    r'\$\d+[\d,]*\s*(?:credit|off|discount)',
    r'(?:free|complimentary)\s+(?:trial|license|subscription|plan|tier)',
    r'(?:get|receive|earn)\s+\$\d+[\d,]*',
]

# CTA link patterns
CTA_PATTERNS = [
    r'book.*demo', r'schedule.*demo', r'request.*demo', r'get.*demo',
    r'start.*trial', r'free.*trial', r'sign.*up', r'get.*started',
    r'claim.*offer', r'redeem', r'register',
]


def extract_offers_from_page(html: str, source_url: str, domain: str) -> List[dict]:
    """
    Extract offer data from page HTML.
    Returns list of raw offer dicts.
    """
    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(separator=" ")
    offers = []

    # Strategy 1: JSON-LD structured data
    ld_offers = _extract_from_json_ld(soup, source_url, domain)
    offers.extend(ld_offers)

    # Strategy 2: Pattern-based extraction from page text
    if not offers:
        pattern_offers = _extract_from_patterns(soup, page_text, source_url, domain)
        offers.extend(pattern_offers)

    return offers


def _has_incentive_signal(text: str) -> bool:
    """Check if text contains signals that this is a demo incentive, not just a product."""
    lower = text.lower()
    return any(sig in lower for sig in DEMO_INCENTIVE_SIGNALS)


def _extract_from_json_ld(soup: BeautifulSoup, source_url: str, domain: str) -> List[dict]:
    """Extract offers from JSON-LD markup, but ONLY if they look like demo incentives.
    
    Most SaaS pages have JSON-LD Product/SoftwareApplication markup that describes
    the software itself. We only want items that mention demos, rewards, or trials.
    """
    offers = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                _type = item.get("@type", "")
                if _type in ("Product", "Offer", "SoftwareApplication"):
                    offer = _parse_ld_offer(item, source_url, domain)
                    if offer:
                        offers.append(offer)
                if "@graph" in item:
                    for node in item["@graph"]:
                        if isinstance(node, dict) and node.get("@type") in ("Product", "Offer"):
                            offer = _parse_ld_offer(node, source_url, domain)
                            if offer:
                                offers.append(offer)
        except (json.JSONDecodeError, TypeError):
            continue
    return offers


def _parse_ld_offer(item: dict, source_url: str, domain: str) -> Optional[dict]:
    """Parse a JSON-LD item into a raw offer dict.
    
    Returns None if the item doesn't look like a demo incentive.
    This is the key filter that prevents generic product pages from
    being treated as offers.
    """
    name = item.get("name", "")
    desc = item.get("description", "")
    if not name:
        return None

    # Check that this is actually a demo incentive, not just a product page
    combined = f"{name} {desc}"
    if not _has_incentive_signal(combined):
        return None

    return {
        "title": name.strip(),
        "description": desc.strip() if desc else None,
        "vendor_domain": domain,
        "source_url": source_url,
        "reward_value": item.get("price") or item.get("offers", {}).get("price"),
        "cta_url": item.get("url") or source_url,
        "extraction_method": "json_ld",
        "raw_text": combined,
        "fetched_at": datetime.now().isoformat(),
    }


def _extract_from_patterns(
    soup: BeautifulSoup, page_text: str, source_url: str, domain: str
) -> List[dict]:
    """Extract offers using reward-amount patterns in page text."""
    offers = []

    # Find reward mentions
    reward_matches = []
    for pattern in REWARD_PATTERNS:
        for match in re.finditer(pattern, page_text, re.IGNORECASE):
            reward_matches.append(match.group())

    if not reward_matches:
        return []

    # Find CTA URLs
    cta_url = source_url
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        href = a["href"]
        if any(re.search(p, text, re.IGNORECASE) for p in CTA_PATTERNS):
            cta_url = href if href.startswith("http") else source_url
            break

    # Build offer from best reward match
    title_el = soup.find("h1") or soup.find("h2")
    title = title_el.get_text(strip=True) if title_el else f"Demo Offer — {domain}"

    # Get meta description as fallback
    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = meta_desc["content"] if meta_desc and meta_desc.get("content") else None

    offers.append({
        "title": title[:200],
        "description": description,
        "vendor_domain": domain,
        "source_url": source_url,
        "reward_value": reward_matches[0] if reward_matches else None,
        "cta_url": cta_url,
        "extraction_method": "pattern_match",
        "raw_text": page_text[:2000],
        "fetched_at": datetime.now().isoformat(),
    })

    return offers
