"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🕷️  CRAWL ENGINE v2 — Investor Lead Machine                ║
║                                                              ║
║   Config-driven, multi-site crawler with stealth,            ║
║   enrichment, scoring, and automated output.                 ║
║                                                              ║
║   Usage:                                                     ║
║     python engine.py                    # Crawl all sites    ║
║     python engine.py --site openvc      # Crawl one site     ║
║     python engine.py --dry-run          # Test without save  ║
║     python engine.py --headless         # No browser window  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import argparse
import sys
import time
from pathlib import Path
from datetime import datetime

import yaml
from playwright.async_api import async_playwright

# ── Internal modules ──
from adapters.openvc import OpenVCAdapter
from adapters.angelmatch import AngelMatchAdapter
from stealth.fingerprint import FingerprintManager
from stealth.behavior import HumanBehavior
from stealth.proxy import ProxyManager
from enrichment.email_validator import EmailValidator
from enrichment.scoring import LeadScorer
from output.csv_writer import CSVWriter
from output.webhook import WebhookNotifier


# ──────────────────────────────────────────────────
#  Adapter Registry
# ──────────────────────────────────────────────────

ADAPTER_MAP = {
    "openvc": OpenVCAdapter,
    "angelmatch": AngelMatchAdapter,
    # Add new adapters here as you build them:
    # "signal": SignalAdapter,
    # "crunchbase": CrunchbaseAdapter,
}


# ──────────────────────────────────────────────────
#  Engine
# ──────────────────────────────────────────────────

class CrawlEngine:
    """
    Main orchestrator. Wires together:
    - Site configs → Adapters
    - Stealth layer (fingerprints, human behavior, proxies)
    - Enrichment pipeline (email validation, lead scoring)
    - Output (CSV, webhooks)
    """

    def __init__(self, args):
        self.args = args
        self.config = self._load_config("config/sites.yaml")
        self.fingerprint_mgr = FingerprintManager()
        self.behavior = HumanBehavior(speed_factor=1.0)
        self.proxy_mgr = ProxyManager("config/proxies.yaml")
        self.email_validator = EmailValidator()
        self.scorer = LeadScorer("config/scoring.yaml")
        self.csv_writer = CSVWriter("data")
        self.webhook = WebhookNotifier(
            webhook_url=args.webhook or "",
            platform=args.webhook_platform or "discord",
        )
        self.all_leads = []

    def _load_config(self, path: str) -> dict:
        with open(path) as f:
            return yaml.safe_load(f)

    async def run(self):
        """Execute the full crawl pipeline."""
        start_time = time.time()
        self._print_banner()

        sites = self.config.get("sites", {})
        defaults = self.config.get("defaults", {})

        # Filter to specific site if requested
        if self.args.site:
            if self.args.site not in sites:
                print(f"\n  ❌  Site '{self.args.site}' not found in config.")
                print(f"  Available: {', '.join(sites.keys())}")
                return
            sites = {self.args.site: sites[self.args.site]}

        async with async_playwright() as p:
            for site_name, site_config in sites.items():
                if not site_config.get("enabled", True):
                    print(f"\n  ⏭️  Skipping {site_name} (disabled)")
                    continue

                adapter_name = site_config.get("adapter", "")
                adapter_class = ADAPTER_MAP.get(adapter_name)

                if not adapter_class:
                    print(f"\n  ⚠️  No adapter found for '{adapter_name}', skipping {site_name}")
                    continue

                try:
                    leads = await self._crawl_site(p, site_name, site_config, adapter_class, defaults)
                    self.all_leads.extend(leads)
                except Exception as e:
                    print(f"\n  ❌  Error crawling {site_name}: {e}")
                    if self.args.verbose:
                        import traceback
                        traceback.print_exc()

        # ── Post-crawl pipeline ──
        if self.all_leads:
            await self._enrich_and_output()
        else:
            print("\n  ⚠️  No leads collected. Check your site configs and selectors.")

        # ── Stats ──
        elapsed = time.time() - start_time
        self._print_summary(elapsed)

    async def _crawl_site(self, playwright, site_name, site_config, adapter_class, defaults):
        """Crawl a single site with a fresh browser context."""
        print(f"\n  🌐  Initializing browser for {site_name}...")

        # Generate a fresh fingerprint for this site
        fingerprint = self.fingerprint_mgr.generate()
        context_kwargs = self.fingerprint_mgr.get_context_kwargs(fingerprint)

        # Check for proxy
        proxy = self.proxy_mgr.get_proxy(site_name)

        # Determine headless mode
        headless = self.args.headless or defaults.get("headless", False)

        # Launch browser
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context(
            **context_kwargs,
            **({"proxy": proxy} if proxy else {}),
        )

        # Apply JS fingerprint overrides
        page = await context.new_page()
        await self.fingerprint_mgr.apply_js_overrides(page)

        # Run the adapter
        adapter = adapter_class(site_config, stealth_module=self.behavior)
        leads = await adapter.run(page)

        # Take a screenshot if configured
        if defaults.get("screenshots", False):
            ss_dir = Path(defaults.get("screenshot_dir", "data/screenshots"))
            ss_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(
                path=str(ss_dir / f"{site_name}_{timestamp}.png"),
                full_page=True,
            )
            print(f"  📸  Screenshot saved")

        await browser.close()
        return leads

    async def _enrich_and_output(self):
        """Run enrichment and output pipeline on collected leads."""
        print(f"\n{'='*60}")
        print(f"  🧠  ENRICHMENT PIPELINE")
        print(f"{'='*60}\n")

        # ── Email validation ──
        print(f"  📧  Validating {len(self.all_leads)} emails...")
        for lead in self.all_leads:
            result = self.email_validator.validate(lead.email)
            if result["quality"] == "invalid":
                lead.email = "N/A (invalid)"
            elif result["is_disposable"]:
                lead.email = f"{lead.email} ⚠️ (disposable)"

        # ── Lead scoring ──
        print(f"  📊  Scoring leads...")
        self.all_leads = self.scorer.score_batch(self.all_leads)

        # ── Delta detection ──
        deltas = self.csv_writer.detect_deltas(self.all_leads)

        # ── Output ──
        if not self.args.dry_run:
            print(f"\n  💾  Writing output...")
            master_path = self.csv_writer.write_master(self.all_leads)

            # Webhook notifications
            hot_count = sum(1 for l in self.all_leads if l.lead_score >= 80)
            await self.webhook.notify_hot_leads(self.all_leads)
            await self.webhook.notify_crawl_complete(
                total=len(self.all_leads),
                new=len(deltas),
                hot=hot_count,
            )
        else:
            print(f"\n  🧪  DRY RUN — no files written")

    def _print_banner(self):
        print()
        print("  ╔══════════════════════════════════════════╗")
        print("  ║   🕷️  CRAWL ENGINE v2                    ║")
        print("  ║   Investor Lead Machine                  ║")
        print("  ╚══════════════════════════════════════════╝")
        print()
        print(f"  ⏰  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  🎯  Sites: {self.args.site or 'ALL'}")
        print(f"  👻  Stealth: ON")
        print(f"  🔒  Proxy: {'ON' if self.proxy_mgr.enabled else 'OFF'}")
        print(f"  🖥️  Headless: {'YES' if self.args.headless else 'NO'}")
        print()

    def _print_summary(self, elapsed: float):
        print(f"\n{'='*60}")
        print(f"  📊  CRAWL SUMMARY")
        print(f"{'='*60}")
        print(f"  ⏱️  Duration: {elapsed:.1f}s")
        print(f"  📝  Total leads: {len(self.all_leads)}")

        if self.all_leads:
            scorer_stats = self.scorer.stats
            print(f"  📈  Avg score: {scorer_stats.get('avg_score', 0)}")
            print(f"  🔴  HOT leads: {scorer_stats.get('hot_count', 0)}")
            print(f"  🟡  WARM leads: {scorer_stats.get('warm_count', 0)}")

        fp_stats = self.fingerprint_mgr.stats
        print(f"  🎭  Fingerprints used: {fp_stats['total_fingerprints_generated']}")
        print(f"  🔒  Proxy requests: {self.proxy_mgr.stats['total_requests_proxied']}")
        print()

        # Top 5 leads preview
        if self.all_leads:
            print(f"  🏆  TOP 5 LEADS:")
            print(f"  {'─'*50}")
            for lead in self.all_leads[:5]:
                areas = ", ".join(lead.focus_areas[:2]) if lead.focus_areas else "N/A"
                print(f"  {lead.tier}  {lead.name} ({lead.fund})")
                print(f"       📧 {lead.email} | 🎯 {areas}")
                print(f"       💰 {lead.check_size} | Score: {lead.lead_score}")
                print()


# ──────────────────────────────────────────────────
#  CLI
# ──────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="🕷️ CRAWL — Investor Lead Machine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--site", type=str, default="",
        help="Crawl a specific site only (e.g. openvc, angelmatch)",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run browser in headless mode (no visible window)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run crawl but don't write output files",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show detailed error tracebacks",
    )
    parser.add_argument(
        "--webhook", type=str, default="",
        help="Discord/Slack webhook URL for notifications",
    )
    parser.add_argument(
        "--webhook-platform", type=str, default="discord",
        choices=["discord", "slack"],
        help="Webhook platform (default: discord)",
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    engine = CrawlEngine(args)
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
