"""
Tests for discovery/multi_searcher.py
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from discovery.multi_searcher import (
    DuckDuckGoEngine,
    GoogleSerpAPIEngine,
    BingSearchEngine,
    BraveSearchEngine,
    _is_valid_vc_domain,
    _get_base_url,
    _build_engines,
    multi_discover,
    DEFAULT_IGNORE,
)


# ── Domain Validation ────────────────────────────

class TestDomainValidation:
    def test_valid_vc_domain(self):
        assert _is_valid_vc_domain("https://example-ventures.com/team", DEFAULT_IGNORE)

    def test_reject_aggregator(self):
        assert not _is_valid_vc_domain("https://crunchbase.com/org/test", DEFAULT_IGNORE)

    def test_reject_social(self):
        assert not _is_valid_vc_domain("https://linkedin.com/in/user", DEFAULT_IGNORE)

    def test_reject_country_tld(self):
        assert not _is_valid_vc_domain("https://venture.cn", DEFAULT_IGNORE)

    def test_reject_gov_edu(self):
        assert not _is_valid_vc_domain("https://investor.gov.uk/team", DEFAULT_IGNORE)

    def test_reject_short_domain(self):
        assert not _is_valid_vc_domain("https://a.b", DEFAULT_IGNORE)


class TestBaseUrl:
    def test_strips_path(self):
        assert _get_base_url("https://example.com/team/page") == "https://example.com"

    def test_preserves_scheme(self):
        assert _get_base_url("http://example.com/foo") == "http://example.com"


# ── Engine Construction ──────────────────────────

class TestBuildEngines:
    def test_ddg_on_by_default(self):
        engines = _build_engines({})
        assert len(engines) >= 1
        assert engines[0].name == "duckduckgo"

    def test_api_engine_skipped_without_key(self):
        config = {"google": {"enabled": True}}  # no api_key
        engines = _build_engines(config)
        names = [e.name for e in engines]
        assert "google" not in names

    def test_api_engine_active_with_key(self):
        config = {"google": {"enabled": True, "api_key": "test-key"}}
        engines = _build_engines(config)
        names = [e.name for e in engines]
        assert "google" in names

    def test_disabled_engine_skipped(self):
        config = {"duckduckgo": {"enabled": False}}
        engines = _build_engines(config)
        # DDG disabled, should fallback
        assert len(engines) >= 1  # always at least one engine

    def test_env_var_key(self):
        with patch.dict("os.environ", {"BING_API_KEY": "env-key"}):
            config = {"bing": {"enabled": True}}
            engines = _build_engines(config)
            names = [e.name for e in engines]
            assert "bing" in names


# ── DuckDuckGo Engine ────────────────────────────

class TestDuckDuckGoEngine:
    def test_extract_uddg_urls(self):
        html = '''
        <a href="?uddg=https%3A%2F%2Fexample-ventures.com%2Fteam">Example</a>
        <a href="?uddg=https%3A%2F%2Fsequoiacap.com%2Fpeople">Sequoia</a>
        '''
        urls = DuckDuckGoEngine._extract_urls(html)
        assert "https://example-ventures.com/team" in urls
        assert "https://sequoiacap.com/people" in urls

    def test_extract_direct_links(self):
        html = '<a href="https://a16z.com/team">a16z team</a>'
        urls = DuckDuckGoEngine._extract_urls(html)
        assert "https://a16z.com/team" in urls


# ── Multi-Discover Orchestrator ──────────────────

class TestMultiDiscover:
    @pytest.mark.asyncio
    async def test_basic_flow(self):
        """Verify orchestrator runs and returns a set of domains."""
        queries = ["test query 1", "test query 2"]

        with patch.object(
            DuckDuckGoEngine, "search",
            new_callable=AsyncMock,
            return_value=[
                "https://example-vc.com/team",
                "https://test-capital.com/about",
                "https://linkedin.com/in/user",  # should be filtered
            ],
        ):
            domains = await multi_discover(
                queries,
                target_count=10,
                engine_config={"duckduckgo": {"enabled": True}},
            )

        assert "https://example-vc.com" in domains
        assert "https://test-capital.com" in domains
        # LinkedIn should be filtered out
        assert not any("linkedin.com" in d for d in domains)

    @pytest.mark.asyncio
    async def test_dedup_across_engines(self):
        """Verify domains are deduplicated across engines."""
        queries = ["test"]
        duplicate_url = "https://same-fund.com/team"

        with patch.object(
            DuckDuckGoEngine, "search",
            new_callable=AsyncMock,
            return_value=[duplicate_url, duplicate_url, duplicate_url],
        ):
            domains = await multi_discover(
                queries,
                target_count=100,
                engine_config={"duckduckgo": {"enabled": True}},
            )

        # Should only appear once
        matching = [d for d in domains if "same-fund.com" in d]
        assert len(matching) == 1

    @pytest.mark.asyncio
    async def test_stops_at_target_count(self):
        """Verify discovery stops when target is reached."""
        queries = [f"query {i}" for i in range(50)]
        call_count = 0

        async def mock_search(session, query):
            nonlocal call_count
            call_count += 1
            return [f"https://fund-{call_count}.com/team"]

        with patch.object(DuckDuckGoEngine, "search", side_effect=mock_search):
            domains = await multi_discover(
                queries,
                target_count=3,
                engine_config={"duckduckgo": {"enabled": True}},
            )

        assert len(domains) >= 3
        assert call_count < len(queries)  # should stop early
