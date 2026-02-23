"""
CRAWL — Portfolio Intelligence Tests
Covers: portfolio scraper extraction, API model, engine wiring.
Run with: venv/bin/python3 -m pytest tests/test_portfolio.py -v
"""

import asyncio
import os
import sys
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup

from enrichment.portfolio_scraper import (
    PortfolioCompanyData,
    PortfolioScraper,
    extract_portfolio_companies,
    _looks_like_company_name,
    _clean_company_name,
    _extract_year,
    _detect_stage,
)


# ──────────────────────────────────────────────────
#  Unit Tests — Helpers
# ──────────────────────────────────────────────────

class TestHelpers:
    def test_looks_like_company_name_valid(self):
        assert _looks_like_company_name("Stripe") is True
        assert _looks_like_company_name("Airbnb") is True
        assert _looks_like_company_name("OpenAI") is True

    def test_looks_like_company_name_rejects_noise(self):
        assert _looks_like_company_name("") is False
        assert _looks_like_company_name("Load More") is False
        assert _looks_like_company_name("Privacy Policy") is False
        assert _looks_like_company_name("x") is False

    def test_looks_like_company_name_rejects_long_sentences(self):
        assert _looks_like_company_name(
            "This is a very long sentence that should not be a company name at all ever"
        ) is False

    def test_clean_company_name(self):
        assert _clean_company_name("  Stripe  ") == "Stripe"
        assert _clean_company_name("Airbnb.") == "Airbnb"
        assert _clean_company_name("OpenAI,") == "OpenAI"

    def test_extract_year(self):
        assert _extract_year("Invested in 2023") == 2023
        assert _extract_year("Series A, 2021") == 2021
        assert _extract_year("No year here") is None
        assert _extract_year("Founded 1999") is None  # Too old

    def test_detect_stage(self):
        assert _detect_stage("Series A round") == "Series A"
        assert _detect_stage("seed investment") == "Seed"
        assert _detect_stage("growth equity") == "Growth"
        assert _detect_stage("no stage info") == ""


# ──────────────────────────────────────────────────
#  Unit Tests — Extraction
# ──────────────────────────────────────────────────

class TestExtraction:
    def test_extract_from_heading_cards(self):
        """Strategy 1: structured cards with headings."""
        html = """
        <html><body>
        <div class="portfolio-grid">
            <div class="company-card">
                <h3>Stripe</h3>
                <span class="sector">Fintech</span>
                <p>Series C, 2021</p>
                <a href="https://stripe.com">Visit</a>
            </div>
            <div class="company-card">
                <h3>Figma</h3>
                <span class="sector">Design</span>
                <p>Series B</p>
                <a href="https://figma.com">Visit</a>
            </div>
            <div class="company-card">
                <h3>Notion</h3>
                <span class="category">Productivity</span>
            </div>
        </div>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        companies = extract_portfolio_companies(
            soup, "https://fund.com/portfolio", "TestFund", "https://fund.com"
        )
        names = {c.company_name for c in companies}
        assert "Stripe" in names
        assert "Figma" in names
        assert "Notion" in names
        # Check metadata extraction
        stripe = next(c for c in companies if c.company_name == "Stripe")
        assert stripe.fund_name == "TestFund"
        assert stripe.url == "https://stripe.com"

    def test_extract_from_logo_images(self):
        """Strategy 2: grid of logos with alt text."""
        html = """
        <html><body>
        <div class="logo-grid">
            <a href="https://openai.com"><img alt="OpenAI" src="openai.png"></a>
            <a href="https://anthropic.com"><img alt="Anthropic" src="anthropic.png"></a>
            <img alt="logo" src="generic.png">
        </div>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        companies = extract_portfolio_companies(
            soup, "https://fund.com/portfolio", "TestFund", "https://fund.com"
        )
        names = {c.company_name for c in companies}
        assert "OpenAI" in names
        assert "Anthropic" in names
        # "logo" should be filtered out
        assert "logo" not in names

    def test_extract_from_link_list(self):
        """Strategy 3: simple list of external links."""
        html = """
        <html><body>
        <ul>
            <li><a href="https://vercel.com">Vercel</a></li>
            <li><a href="https://linear.app">Linear</a></li>
            <li><a href="https://fund.com/about">About Us</a></li>
        </ul>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        companies = extract_portfolio_companies(
            soup, "https://fund.com/portfolio", "TestFund", "https://fund.com"
        )
        names = {c.company_name for c in companies}
        assert "Vercel" in names
        assert "Linear" in names
        # Internal link "About Us" should be excluded (not external)
        assert "About Us" not in names

    def test_deduplication(self):
        """Same company appearing in multiple strategies should be deduplicated."""
        html = """
        <html><body>
        <div><h3>Stripe</h3></div>
        <div><h4>Stripe</h4></div>
        <a href="https://stripe.com"><img alt="Stripe" src="s.png"></a>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        companies = extract_portfolio_companies(
            soup, "https://fund.com/portfolio", "TestFund", "https://fund.com"
        )
        stripe_count = sum(1 for c in companies if c.company_name == "Stripe")
        assert stripe_count == 1

    def test_empty_page(self):
        html = "<html><body><p>Nothing here</p></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        companies = extract_portfolio_companies(
            soup, "https://fund.com/portfolio", "TestFund", "https://fund.com"
        )
        assert companies == []


# ──────────────────────────────────────────────────
#  Data Model Tests
# ──────────────────────────────────────────────────

class TestDataModel:
    def test_portfolio_company_data_fields(self):
        c = PortfolioCompanyData(
            fund_name="a16z",
            company_name="Stripe",
            sector="Fintech",
            stage="Series C",
            url="https://stripe.com",
            year=2021,
        )
        assert c.fund_name == "a16z"
        assert c.company_name == "Stripe"
        assert c.sector == "Fintech"
        assert c.stage == "Series C"
        assert c.url == "https://stripe.com"
        assert c.year == 2021

    def test_to_dict(self):
        c = PortfolioCompanyData(fund_name="a16z", company_name="Stripe")
        d = c.to_dict()
        assert "fund_name" in d
        assert "company_name" in d
        assert d["company_name"] == "Stripe"


# ──────────────────────────────────────────────────
#  SQLAlchemy Model Tests
# ──────────────────────────────────────────────────

class TestSQLAlchemyModel:
    def test_portfolio_company_model_exists(self):
        from api.models import PortfolioCompany
        assert PortfolioCompany.__tablename__ == "portfolio_companies"

    def test_portfolio_company_model_columns(self):
        from api.models import PortfolioCompany
        cols = {c.name for c in PortfolioCompany.__table__.columns}
        expected = {"id", "fund_name", "company_name", "sector", "stage", "url", "year", "scraped_at"}
        assert expected.issubset(cols), f"Missing columns: {expected - cols}"

    def test_portfolio_company_unique_index(self):
        from api.models import PortfolioCompany
        indexes = {idx.name for idx in PortfolioCompany.__table__.indexes}
        assert "ix_portfolio_fund_company" in indexes


# ──────────────────────────────────────────────────
#  Pydantic Schema Tests
# ──────────────────────────────────────────────────

class TestSchemas:
    def test_portfolio_response_schema_exists(self):
        from api.schemas import PortfolioCompanyResponse, PortfolioCompanyList
        assert PortfolioCompanyResponse is not None
        assert PortfolioCompanyList is not None

    def test_portfolio_response_fields(self):
        from api.schemas import PortfolioCompanyResponse
        fields = set(PortfolioCompanyResponse.model_fields.keys())
        expected = {"id", "fund_name", "company_name", "sector", "stage", "url", "year", "scraped_at"}
        assert expected.issubset(fields)


# ──────────────────────────────────────────────────
#  Engine Wiring Tests
# ──────────────────────────────────────────────────

class TestEngineWiring:
    def test_engine_has_portfolio_flag(self):
        import engine
        with patch("sys.argv", ["engine.py", "--portfolio", "--dry-run"]):
            args = engine.parse_args()
        assert hasattr(args, "portfolio")
        assert args.portfolio is True

    def test_engine_imports_portfolio_scraper(self):
        import engine
        assert hasattr(engine, "PortfolioScraper")

    def test_engine_has_run_portfolio_scrape_method(self):
        import engine
        assert hasattr(engine.CrawlEngine, "_run_portfolio_scrape")

    def test_portfolio_flag_triggers_scrape(self):
        """When --portfolio is set, run() should call _run_portfolio_scrape."""
        import inspect
        import engine
        source = inspect.getsource(engine.CrawlEngine.run)
        assert "_run_portfolio_scrape" in source


# ──────────────────────────────────────────────────
#  API Router Tests
# ──────────────────────────────────────────────────

class TestAPIRouter:
    def test_portfolio_router_exists(self):
        from api.routers.portfolio import router
        assert router is not None
        assert router.prefix == "/funds"

    def test_portfolio_router_registered(self):
        try:
            from api.main import app
        except (ModuleNotFoundError, ImportError):
            import pytest
            pytest.skip("api.main dependencies not installed (e.g. stripe)")
        routes = [r.path for r in app.routes]
        assert any("/funds/" in r and "portfolio" in r for r in routes), (
            f"Portfolio endpoint not found in routes: {routes}"
        )

    def test_portfolio_endpoint_path(self):
        from api.routers.portfolio import router
        paths = [r.path for r in router.routes]
        # Router prefix is /funds, so route path includes it
        assert any("portfolio" in p and "fund" in p for p in paths), (
            f"Portfolio endpoint not found in router paths: {paths}"
        )


# ──────────────────────────────────────────────────
#  Scraper Class Tests
# ──────────────────────────────────────────────────

class TestScraperClass:
    def test_portfolio_scraper_init(self):
        scraper = PortfolioScraper(max_concurrent=5, headless=True)
        assert scraper.max_concurrent == 5
        assert scraper.headless is True
        assert scraper.all_companies == []

    def test_portfolio_paths_defined(self):
        from enrichment.portfolio_scraper import PORTFOLIO_PATHS
        assert len(PORTFOLIO_PATHS) >= 5
        assert "/portfolio" in PORTFOLIO_PATHS
        assert "/companies" in PORTFOLIO_PATHS
        assert "/investments" in PORTFOLIO_PATHS
