"""
CRAWL — GitHub VC List Fetcher
Fetches curated VC lists from known GitHub repositories via raw HTTP (no browser).
Parses markdown tables and bullet lists to extract VC names and websites.
"""

import re
import logging
from typing import List
from datetime import datetime

import aiohttp

from adapters.base import InvestorLead

logger = logging.getLogger(__name__)

# Known GitHub raw URLs containing curated VC lists
GITHUB_SOURCES = [
    {
        "name": "awesome-vc (mckaywrigley)",
        "url": "https://raw.githubusercontent.com/mckaywrigley/awesome-vc/main/README.md",
    },
    {
        "name": "awesome-venture-capital",
        "url": "https://raw.githubusercontent.com/byjonah/awesome-venture-capital/main/README.md",
    },
    {
        "name": "vc-firms (jbkunst)",
        "url": "https://raw.githubusercontent.com/jbkunst/vc-firms/main/README.md",
    },
]


def _parse_markdown_links(text: str) -> List[dict]:
    """Extract [name](url) patterns from markdown text."""
    # Match markdown links: [Name](https://example.com)
    pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    matches = re.findall(pattern, text)
    results = []
    for name, url in matches:
        name = name.strip()
        # Skip navigation/badge links
        if len(name) < 3 or name.lower() in ("link", "website", "here", "source"):
            continue
        if "badge" in url or "shields.io" in url or "github.com" in url:
            continue
        results.append({"name": name, "website": url})
    return results


def _parse_markdown_table(text: str) -> List[dict]:
    """Extract rows from markdown tables with Name and URL columns."""
    results = []
    lines = text.split("\n")
    header_idx = -1
    name_col = -1
    url_col = -1

    for i, line in enumerate(lines):
        if "|" in line and ("name" in line.lower() or "firm" in line.lower() or "fund" in line.lower()):
            cols = [c.strip().lower() for c in line.split("|")]
            for j, col in enumerate(cols):
                if any(kw in col for kw in ("name", "firm", "fund", "company")):
                    name_col = j
                if any(kw in col for kw in ("url", "website", "link", "site")):
                    url_col = j
            if name_col >= 0:
                header_idx = i
                break

    if header_idx < 0:
        return results

    for line in lines[header_idx + 2:]:  # skip header + separator
        if "|" not in line:
            break
        cols = [c.strip() for c in line.split("|")]
        if name_col < len(cols):
            name = cols[name_col].strip()
            # Extract URL from markdown link in cell
            link_match = re.search(r'\[([^\]]*)\]\(([^\)]+)\)', name)
            if link_match:
                name = link_match.group(1)
                url = link_match.group(2)
            elif url_col >= 0 and url_col < len(cols):
                url = cols[url_col].strip()
                link_match = re.search(r'\[([^\]]*)\]\(([^\)]+)\)', url)
                if link_match:
                    url = link_match.group(2)
            else:
                url = ""

            if name and len(name) > 2:
                results.append({"name": name, "website": url if url.startswith("http") else ""})

    return results


def _parse_bullet_list(text: str) -> List[dict]:
    """Extract VC entries from bullet-point lists with links."""
    results = []
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith(("-", "*", "+")):
            continue
        # Try to find a markdown link
        link_match = re.search(r'\[([^\]]+)\]\((https?://[^\)]+)\)', line)
        if link_match:
            name = link_match.group(1).strip()
            url = link_match.group(2).strip()
            if len(name) > 2 and "badge" not in url and "shields.io" not in url:
                results.append({"name": name, "website": url})
    return results


async def _fetch_and_parse(session: aiohttp.ClientSession, source: dict) -> List[InvestorLead]:
    """Fetch a single GitHub source and parse into leads."""
    leads = []
    try:
        async with session.get(source["url"], timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                logger.debug(f"  GitHub {source['name']}: HTTP {resp.status}")
                return leads

            text = await resp.text()

            # Try all parsers
            entries = []
            entries.extend(_parse_markdown_table(text))
            entries.extend(_parse_markdown_links(text))
            entries.extend(_parse_bullet_list(text))

            # Dedup within this source
            seen = set()
            for entry in entries:
                key = entry["name"].lower().strip()
                if key in seen:
                    continue
                seen.add(key)

                leads.append(InvestorLead(
                    name=entry["name"],
                    fund=entry["name"],
                    website=entry.get("website", "N/A") or "N/A",
                    source=f"github:{source['name']}",
                    scraped_at=datetime.now().isoformat(),
                ))

            logger.debug(f"  GitHub {source['name']}: {len(leads)} entries parsed")

    except Exception as e:
        logger.debug(f"  GitHub {source['name']}: fetch failed: {e}")

    return leads


async def fetch_github_vc_lists() -> List[InvestorLead]:
    """Fetch VC lists from all known GitHub sources."""
    all_leads = []

    async with aiohttp.ClientSession(
        headers={"User-Agent": "Mozilla/5.0 (compatible; CrawlBot/1.0)"}
    ) as session:
        tasks = [_fetch_and_parse(session, src) for src in GITHUB_SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_leads.extend(result)

    logger.info(f"  🐙  GitHub VC lists: {len(all_leads)} total entries from {len(GITHUB_SOURCES)} sources")
    return all_leads


# Need asyncio for gather
import asyncio
