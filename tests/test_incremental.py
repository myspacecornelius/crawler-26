"""
Tests for incremental crawl / delta updates (cm-10).
Covers: CrawlStateManager, stale filtering, CLI flags, engine wiring.
Run with: venv/bin/python -m pytest tests/test_incremental.py -v
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enrichment.incremental import CrawlStateManager, DEFAULT_STALE_DAYS, DEFAULT_REVERIFY_DAYS


# ──────────────────────────────────────────────────
#  CrawlStateManager — domain normalization
# ──────────────────────────────────────────────────

class TestDomainNormalization:
    def test_normalize_url(self):
        mgr = CrawlStateManager()
        assert mgr._normalize_domain("https://www.acme.vc/team") == "acme.vc"

    def test_normalize_bare_domain(self):
        mgr = CrawlStateManager()
        assert mgr._normalize_domain("acme.vc") == "acme.vc"

    def test_normalize_http(self):
        mgr = CrawlStateManager()
        assert mgr._normalize_domain("http://fund.com") == "fund.com"

    def test_normalize_www(self):
        mgr = CrawlStateManager()
        assert mgr._normalize_domain("https://www.fund.com") == "fund.com"

    def test_normalize_trailing_slash(self):
        mgr = CrawlStateManager()
        assert mgr._normalize_domain("https://fund.com/") == "fund.com"


# ──────────────────────────────────────────────────
#  CrawlStateManager — staleness logic
# ──────────────────────────────────────────────────

class TestStaleness:
    def test_never_crawled_is_stale(self):
        mgr = CrawlStateManager(stale_days=7)
        assert mgr.is_stale("https://never-seen.com") is True

    def test_recently_crawled_is_fresh(self):
        mgr = CrawlStateManager(stale_days=7)
        mgr._cache["fresh.com"] = datetime.now(timezone.utc) - timedelta(hours=1)
        assert mgr.is_stale("https://fresh.com") is False

    def test_old_crawl_is_stale(self):
        mgr = CrawlStateManager(stale_days=7)
        mgr._cache["old.com"] = datetime.now(timezone.utc) - timedelta(days=10)
        assert mgr.is_stale("https://old.com") is True

    def test_exactly_at_threshold(self):
        mgr = CrawlStateManager(stale_days=7)
        mgr._cache["edge.com"] = datetime.now(timezone.utc) - timedelta(days=7, seconds=1)
        assert mgr.is_stale("https://edge.com") is True

    def test_custom_stale_days(self):
        mgr = CrawlStateManager(stale_days=1)
        mgr._cache["recent.com"] = datetime.now(timezone.utc) - timedelta(days=2)
        assert mgr.is_stale("https://recent.com") is True

    def test_naive_datetime_handled(self):
        """SQLite returns naive datetimes; should still work."""
        mgr = CrawlStateManager(stale_days=7)
        mgr._cache["naive.com"] = datetime.now() - timedelta(hours=1)
        assert mgr.is_stale("https://naive.com") is False


# ──────────────────────────────────────────────────
#  CrawlStateManager — filter_stale
# ──────────────────────────────────────────────────

class TestFilterStale:
    def test_all_new(self):
        mgr = CrawlStateManager(stale_days=7)
        stale, fresh = mgr.filter_stale(["https://a.com", "https://b.com"])
        assert len(stale) == 2
        assert len(fresh) == 0

    def test_mixed(self):
        mgr = CrawlStateManager(stale_days=7)
        mgr._cache["a.com"] = datetime.now(timezone.utc) - timedelta(hours=1)
        mgr._cache["b.com"] = datetime.now(timezone.utc) - timedelta(days=10)
        stale, fresh = mgr.filter_stale(["https://a.com", "https://b.com", "https://c.com"])
        assert "https://a.com" in fresh
        assert "https://b.com" in stale
        assert "https://c.com" in stale

    def test_all_fresh(self):
        mgr = CrawlStateManager(stale_days=7)
        mgr._cache["a.com"] = datetime.now(timezone.utc)
        mgr._cache["b.com"] = datetime.now(timezone.utc)
        stale, fresh = mgr.filter_stale(["https://a.com", "https://b.com"])
        assert len(stale) == 0
        assert len(fresh) == 2

    def test_empty_list(self):
        mgr = CrawlStateManager()
        stale, fresh = mgr.filter_stale([])
        assert stale == []
        assert fresh == []


# ──────────────────────────────────────────────────
#  CrawlStateManager — mark_crawled (in-memory)
# ──────────────────────────────────────────────────

class TestMarkCrawled:
    def test_mark_updates_cache(self):
        async def run():
            mgr = CrawlStateManager(stale_days=7)
            assert mgr.is_stale("https://new.com") is True
            await mgr.mark_crawled("https://new.com", leads_found=5)
            assert mgr.is_stale("https://new.com") is False
        asyncio.run(run())

    def test_mark_batch(self):
        async def run():
            mgr = CrawlStateManager(stale_days=7)
            batch = [
                {"url": "https://a.com", "leads_found": 3},
                {"url": "https://b.com", "leads_found": 7},
            ]
            await mgr.mark_batch_crawled(batch)
            assert mgr.is_stale("https://a.com") is False
            assert mgr.is_stale("https://b.com") is False
        asyncio.run(run())


# ──────────────────────────────────────────────────
#  Summary
# ──────────────────────────────────────────────────

class TestSummary:
    def test_summary_empty(self):
        mgr = CrawlStateManager(stale_days=7)
        s = mgr.summary()
        assert s["total_domains"] == 0
        assert s["stale_domains"] == 0
        assert s["fresh_domains"] == 0

    def test_summary_mixed(self):
        mgr = CrawlStateManager(stale_days=7)
        mgr._cache["fresh.com"] = datetime.now(timezone.utc)
        mgr._cache["stale.com"] = datetime.now(timezone.utc) - timedelta(days=10)
        s = mgr.summary()
        assert s["total_domains"] == 2
        assert s["stale_domains"] == 1
        assert s["fresh_domains"] == 1
        assert s["stale_threshold_days"] == 7


# ──────────────────────────────────────────────────
#  Defaults
# ──────────────────────────────────────────────────

class TestDefaults:
    def test_default_stale_days(self):
        assert DEFAULT_STALE_DAYS == 7

    def test_default_reverify_days(self):
        assert DEFAULT_REVERIFY_DAYS == 14


# ──────────────────────────────────────────────────
#  Engine Wiring
# ──────────────────────────────────────────────────

class TestEngineWiring:
    def test_engine_has_incremental_flag(self):
        import engine
        with patch("sys.argv", ["engine.py", "--incremental", "--dry-run"]):
            args = engine.parse_args()
        assert hasattr(args, "incremental")
        assert args.incremental is True

    def test_engine_has_stale_days_flag(self):
        import engine
        with patch("sys.argv", ["engine.py", "--stale-days", "3", "--dry-run"]):
            args = engine.parse_args()
        assert args.stale_days == 3

    def test_engine_default_stale_days(self):
        import engine
        with patch("sys.argv", ["engine.py", "--dry-run"]):
            args = engine.parse_args()
        assert args.stale_days == 7

    def test_engine_imports_incremental(self):
        import engine
        assert hasattr(engine, "CrawlStateManager")
        assert hasattr(engine, "update_lead_freshness_in_db")

    def test_engine_has_crawl_state(self):
        import engine
        with patch("sys.argv", ["engine.py", "--dry-run"]):
            args = engine.parse_args()
        eng = engine.CrawlEngine(args)
        assert hasattr(eng, "crawl_state")
        assert isinstance(eng.crawl_state, CrawlStateManager)


# ──────────────────────────────────────────────────
#  DB Model
# ──────────────────────────────────────────────────

class TestDBModel:
    def test_crawl_state_model_exists(self):
        from api.models import CrawlState
        assert CrawlState.__tablename__ == "crawl_state"

    def test_crawl_state_columns(self):
        from api.models import CrawlState
        cols = {c.name for c in CrawlState.__table__.columns}
        expected = {"id", "domain", "last_crawled_at", "leads_found", "status", "crawl_duration_s"}
        assert expected.issubset(cols), f"Missing: {expected - cols}"

    def test_lead_has_freshness_columns(self):
        from api.models import Lead
        cols = {c.name for c in Lead.__table__.columns}
        assert "last_verified" in cols
        assert "last_crawled_at" in cols
