"""
CRAWL — V2 Architecture Tests
Covers the forensic fixes: Source Aggregator, HTTP discovery, adapter fixes.
Run with: venv/bin/python3 -m pytest tests/test_v2.py -v
"""

import asyncio
import inspect
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters.base import InvestorLead, BaseSiteAdapter


# ──────────────────────────────────────────────────
#  Source Aggregator
# ──────────────────────────────────────────────────

class TestSourceAggregator:
    def test_seed_db_loads(self):
        from sources.seed_db import load_seed_leads
        leads = load_seed_leads()
        assert len(leads) >= 200, f"Seed DB only has {len(leads)} leads — need 200+"

    def test_seed_leads_have_websites(self):
        from sources.seed_db import load_seed_leads
        leads = load_seed_leads()
        with_website = [l for l in leads if l.website and l.website != "N/A"]
        ratio = len(with_website) / len(leads)
        assert ratio > 0.9, f"Only {ratio:.0%} of seed leads have a website"

    def test_seed_leads_have_fund_name(self):
        from sources.seed_db import load_seed_leads
        leads = load_seed_leads()
        with_fund = [l for l in leads if l.fund and l.fund != "N/A"]
        assert len(with_fund) == len(leads), "Some seed leads are missing fund name"

    def test_seed_leads_are_investor_leads(self):
        from sources.seed_db import load_seed_leads
        leads = load_seed_leads()
        for lead in leads[:5]:
            assert isinstance(lead, InvestorLead)

    def test_seed_leads_no_duplicates(self):
        from sources.seed_db import load_seed_leads
        leads = load_seed_leads()
        names = [l.name.lower() for l in leads]
        assert len(names) == len(set(names)), "Duplicate names in seed DB"

    def test_aggregator_importable(self):
        from sources.aggregator import SourceAggregator, generate_target_funds
        assert SourceAggregator is not None
        assert generate_target_funds is not None

    def test_aggregator_runs(self):
        async def run():
            from sources.aggregator import SourceAggregator
            agg = SourceAggregator()
            # Mock GitHub to avoid network calls in tests
            with patch("sources.github_lists.fetch_github_vc_lists", new=AsyncMock(return_value=[])):
                leads = await agg.aggregate()
            assert len(leads) >= 200
        asyncio.run(run())

    def test_aggregator_deduplicates(self):
        async def run():
            from sources.aggregator import SourceAggregator
            agg = SourceAggregator()
            with patch("sources.github_lists.fetch_github_vc_lists", new=AsyncMock(return_value=[])):
                leads = await agg.aggregate()
            names = [l.name.lower() for l in leads]
            assert len(names) == len(set(names))
        asyncio.run(run())

    def test_generate_target_funds(self):
        import tempfile
        async def run():
            from sources.aggregator import generate_target_funds
            leads = [
                InvestorLead(name="Test VC", website="https://testvc.com"),
                InvestorLead(name="No Site", website="N/A"),
                InvestorLead(name="Pricing Bug", website="/pricing"),
            ]
            with tempfile.TemporaryDirectory() as tmpdir:
                path = os.path.join(tmpdir, "targets.txt")
                sites = await generate_target_funds(leads, path)
                assert "https://testvc.com" in sites
                assert "N/A" not in sites
                assert "/pricing" not in sites
        asyncio.run(run())

    def test_engine_imports_aggregator(self):
        import engine
        assert hasattr(engine, "SourceAggregator")
        assert hasattr(engine, "generate_target_funds")
        assert hasattr(engine, "http_discover")

    def test_engine_has_run_aggregator(self):
        import engine
        assert hasattr(engine.CrawlEngine, "_run_aggregator")


# ──────────────────────────────────────────────────
#  HTTP Discovery
# ──────────────────────────────────────────────────

class TestHTTPDiscovery:
    def test_importable(self):
        from sources.http_discovery import http_discover, _is_valid_vc_domain, _extract_urls_from_html
        assert http_discover is not None

    def test_is_valid_vc_domain_rejects_aggregators(self):
        from sources.http_discovery import _is_valid_vc_domain, DEFAULT_IGNORE
        assert _is_valid_vc_domain("https://crunchbase.com/org/x", DEFAULT_IGNORE) is False
        assert _is_valid_vc_domain("https://linkedin.com/in/x", DEFAULT_IGNORE) is False
        assert _is_valid_vc_domain("https://duckduckgo.com", DEFAULT_IGNORE) is False
        assert _is_valid_vc_domain("https://tracxn.com", DEFAULT_IGNORE) is False

    def test_is_valid_vc_domain_accepts_real_vcs(self):
        from sources.http_discovery import _is_valid_vc_domain, DEFAULT_IGNORE
        assert _is_valid_vc_domain("https://www.sequoiacap.com/team", DEFAULT_IGNORE) is True
        assert _is_valid_vc_domain("https://a16z.com", DEFAULT_IGNORE) is True
        assert _is_valid_vc_domain("https://greylock.com", DEFAULT_IGNORE) is True

    def test_extract_urls_from_html(self):
        from sources.http_discovery import _extract_urls_from_html
        html = '''
        <a href="/l/?uddg=https%3A%2F%2Fsequoiacap.com%2Fteam&rut=abc">Sequoia</a>
        <a href="https://example.com/page">Example</a>
        '''
        urls = _extract_urls_from_html(html)
        assert any("sequoiacap.com" in u for u in urls)
        assert any("example.com" in u for u in urls)

    def test_extract_urls_ignores_ddg_internal(self):
        from sources.http_discovery import _extract_urls_from_html
        html = '<a href="https://duckduckgo.com/feedback">Feedback</a>'
        urls = _extract_urls_from_html(html)
        assert len(urls) == 0


# ──────────────────────────────────────────────────
#  Infinite Scroll Fix (Virtual DOM)
# ──────────────────────────────────────────────────

class TestInfiniteScrollFix:
    def test_extract_from_page_has_silent_param(self):
        sig = inspect.signature(BaseSiteAdapter._extract_from_page)
        assert "silent" in sig.parameters, "_extract_from_page missing 'silent' parameter"

    def test_infinite_scroll_calls_extract_periodically(self):
        """_handle_infinite_scroll must call _extract_from_page during scrolling, not just at end."""
        source = inspect.getsource(BaseSiteAdapter._handle_infinite_scroll)
        assert "extract_interval" in source
        assert "silent=True" in source
        assert "stale_rounds" in source

    def test_extract_interval_in_openvc_config(self):
        with open("config/sites.yaml") as f:
            config = yaml.safe_load(f)
        openvc = config["sites"]["openvc"]["pagination"]
        assert "extract_interval" in openvc
        assert openvc["extract_interval"] <= 5

    def test_diagnostic_output_on_zero_cards(self):
        """When 0 cards found, _extract_from_page should log diagnostic info."""
        source = inspect.getsource(BaseSiteAdapter._extract_from_page)
        assert "DIAGNOSTIC" in source


# ──────────────────────────────────────────────────
#  AngelMatch Fixes
# ──────────────────────────────────────────────────

class TestAngelMatchFixes:
    def test_angelmatch_website_selector_excludes_pricing(self):
        with open("config/sites.yaml") as f:
            config = yaml.safe_load(f)
        am = config["sites"]["angelmatch"]["selectors"]
        assert "/pricing" in am.get("website", ""), "Website selector should exclude /pricing links"

    def test_angelmatch_linkedin_selector_uses_href(self):
        with open("config/sites.yaml") as f:
            config = yaml.safe_load(f)
        am = config["sites"]["angelmatch"]["selectors"]
        assert "linkedin.com/in/" in am.get("linkedin", "")

    def test_angelmatch_button_selector_has_fallbacks(self):
        with open("config/sites.yaml") as f:
            config = yaml.safe_load(f)
        am = config["sites"]["angelmatch"]["pagination"]
        selector = am.get("button_selector", "")
        assert "," in selector, "Button selector should have multiple fallbacks separated by commas"


# ──────────────────────────────────────────────────
#  Broken Adapters Disabled
# ──────────────────────────────────────────────────

class TestBrokenAdaptersDisabled:
    def test_visible_vc_disabled(self):
        with open("config/sites.yaml") as f:
            config = yaml.safe_load(f)
        assert config["sites"]["visible_vc"]["enabled"] is False

    def test_landscape_vc_disabled(self):
        with open("config/sites.yaml") as f:
            config = yaml.safe_load(f)
        assert config["sites"]["landscape_vc"]["enabled"] is False

    def test_wellfound_disabled(self):
        with open("config/sites.yaml") as f:
            config = yaml.safe_load(f)
        assert config["sites"]["wellfound"]["enabled"] is False


# ──────────────────────────────────────────────────
#  GitHub Lists Parser
# ──────────────────────────────────────────────────

class TestGitHubListsParser:
    def test_parse_markdown_links(self):
        from sources.github_lists import _parse_markdown_links
        text = "- [Sequoia Capital](https://www.sequoiacap.com) - Legendary VC"
        results = _parse_markdown_links(text)
        assert len(results) >= 1
        assert results[0]["name"] == "Sequoia Capital"
        assert "sequoiacap.com" in results[0]["website"]

    def test_parse_markdown_links_skips_badges(self):
        from sources.github_lists import _parse_markdown_links
        text = "[![badge](https://shields.io/badge.svg)](https://github.com)"
        results = _parse_markdown_links(text)
        assert len(results) == 0

    def test_parse_bullet_list(self):
        from sources.github_lists import _parse_bullet_list
        text = """
- [Accel](https://www.accel.com) - Global VC
- [Benchmark](https://www.benchmark.com) - Early stage
* Just text no link
"""
        results = _parse_bullet_list(text)
        assert len(results) == 2
        names = {r["name"] for r in results}
        assert "Accel" in names
        assert "Benchmark" in names


# ──────────────────────────────────────────────────
#  Email Guesser Integration
# ──────────────────────────────────────────────────

class TestEmailGuesserIntegration:
    def test_seed_leads_have_websites_for_guesser(self):
        """The email guesser needs real websites. Seed leads must provide them."""
        from sources.seed_db import load_seed_leads
        from enrichment.email_guesser import _extract_domain
        leads = load_seed_leads()
        resolvable = 0
        for lead in leads:
            domain = _extract_domain(lead.website)
            if domain:
                resolvable += 1
        ratio = resolvable / len(leads)
        assert ratio > 0.85, (
            f"Only {ratio:.0%} of seed leads have a guesser-resolvable website"
        )

    def test_guesser_works_with_seed_website(self):
        from enrichment.email_guesser import generate_candidates, _extract_domain
        domain = _extract_domain("https://www.sequoiacap.com")
        assert domain == "sequoiacap.com"
        candidates = generate_candidates("John Smith", domain)
        assert "john@sequoiacap.com" in candidates
        assert "john.smith@sequoiacap.com" in candidates


# ──────────────────────────────────────────────────
#  End-to-end Lead Volume Estimate
# ──────────────────────────────────────────────────

class TestLeadVolumeProjection:
    def test_seed_db_provides_minimum_200_leads(self):
        from sources.seed_db import load_seed_leads
        leads = load_seed_leads()
        assert len(leads) >= 200, f"Seed DB has {len(leads)} leads — need 200+ minimum"

    def test_seed_db_provides_minimum_200_target_funds(self):
        """Most seed leads should have websites that can be crawled."""
        from sources.seed_db import load_seed_leads
        leads = load_seed_leads()
        websites = {l.website for l in leads if l.website and l.website != "N/A"}
        assert len(websites) >= 200, f"Only {len(websites)} unique websites in seed DB"
