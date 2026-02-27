"""
CRAWL — Catch-All Detector & JS-Rendered Scraper
1. Detects if a domain is "catch-all" (accepts email to ANY address). 
   If so, any reasonable guess for a contact's email is technically valid.
2. For remaining leads without emails, uses Playwright to render 
   JS-heavy team/contact pages and scrape the fully rendered DOM
   for hidden or dynamically generated emails.
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import aiohttp
import aiosmtplib
import dns.asyncresolver
from playwright.async_api import async_playwright, Page

logger = logging.getLogger(__name__)

# Standard email regex
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,15}')

# Target pages to scrape for hidden emails
_TARGET_PATHS = ["/team", "/about", "/people", "/contact", "/us"]

# Emails to ignore
_IGNORE_PATTERNS = {
    "example.com", "email.com", "domain.com",
    "noreply", "no-reply", "donotreply",
    "sentry.io", "w3.org",
}

def _is_valid_email(email: str, target_domain: str) -> bool:
    if not email or "@" not in email:
        return False
    email = email.lower()
    if len(email) > 60 or len(email) < 5:
        return False
    for p in _IGNORE_PATTERNS:
        if p in email:
            return False
    return True

class CatchAllDetector:
    """
    Two-phase enrichment:
    1. SMTP Catch-all detection
    2. JS DOM scraping for heavily obfuscated sites
    """
    def __init__(self, smtp_timeout: float = 3.0, browser_timeout: int = 15000):
        self._smtp_timeout = smtp_timeout
        self._browser_timeout = browser_timeout
        self._resolver = dns.asyncresolver.Resolver()
        self._resolver.timeout = 2.0
        self._resolver.lifetime = 2.0
        self._stats = {
            "domains_checked": 0,
            "catchall_domains": 0,
            "js_pages_rendered": 0,
            "emails_found": 0,
            "leads_enriched_catchall": 0,
            "leads_enriched_js": 0,
        }
        self._mx_cache: Dict[str, list] = {}
        self._catchall_cache: Dict[str, bool] = {}
        
    async def _get_mx_records(self, domain: str) -> list:
        if domain in self._mx_cache:
            return self._mx_cache[domain]
        try:
            answers = await self._resolver.resolve(domain, 'MX')
            # Sort by preference
            records = sorted(answers, key=lambda r: r.preference)
            mx_list = [r.exchange.to_text().strip('.') for r in records]
            self._mx_cache[domain] = mx_list
            return mx_list
        except Exception:
            self._mx_cache[domain] = []
            return []

    async def _check_catch_all(self, domain: str) -> bool:
        """Connect to domain's MX and test a fake email to see if it's accepted."""
        if domain in self._catchall_cache:
            return self._catchall_cache[domain]
            
        mx_list = await self._get_mx_records(domain)
        if not mx_list:
            self._catchall_cache[domain] = False
            return False
            
        mx_host = mx_list[0]
        fake_email = f"alkdsjfhlakjsdhf892347@{domain}"
        
        try:
            smtp = aiosmtplib.SMTP(hostname=mx_host, port=25, timeout=self._smtp_timeout)
            await smtp.connect()
            await smtp.ehlo("gmail.com")
            await smtp.mail("hello@example.com")
            code, msg = await smtp.rcpt(fake_email)
            await smtp.quit()
            
            # 250 means accepted (catch-all)
            is_catch_all = (code == 250)
            self._catchall_cache[domain] = is_catch_all
            return is_catch_all
            
        except Exception as e:
            # Drop silently, standard timeout/refuse
            self._catchall_cache[domain] = False
            return False

    async def _scrape_js_page(self, url: str, target_domain: str, page: Page) -> Set[str]:
        """Render page with JS and pull emails from fully loaded DOM."""
        found = set()
        try:
            await page.goto(url, wait_until="networkidle", timeout=self._browser_timeout)
            self._stats["js_pages_rendered"] += 1
            
            # Wait a beat for final JS execution (obfuscation decoders)
            await asyncio.sleep(1.0)
            
            # Extract plain text content
            content = await page.content()
            for match in _EMAIL_RE.finditer(content):
                email = match.group().lower().rstrip(".")
                if _is_valid_email(email, target_domain):
                    found.add(email)
                    
            # Also extract mailto hrefs (in case JS builds them dynamically)
            mailtos = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('a[href^="mailto:"]'))
                    .map(a => a.href.replace('mailto:', '').split('?')[0].trim());
            }''')
            for m in mailtos:
                if _is_valid_email(m, target_domain):
                    found.add(m)
                    
        except Exception as e:
            logger.debug(f"  🕷️  JS scrape failed for {url}: {e}")
            
        return found

    async def enrich_batch(self, leads: list) -> list:
        from deep_crawl import _match_email_to_name
        
        no_email = [
            lead for lead in leads
            if not lead.email or lead.email in ("N/A", "N/A (invalid)")
        ]
        
        if not no_email:
            logger.info("  🛑  CATCH-ALL/JS: no leads need enrichment")
            return leads
            
        domain_leads: Dict[str, List] = {}
        for lead in no_email:
            if lead.website and lead.website not in ("N/A", ""):
                try:
                    parsed = urlparse(
                        lead.website if "://" in lead.website else f"https://{lead.website}"
                    )
                    domain = parsed.netloc.lower().replace("www.", "")
                    if domain:
                        domain_leads.setdefault(domain, []).append(lead)
                except Exception:
                    pass

        logger.info(
            f"  🛑  CATCH-ALL: checking {len(domain_leads)} domains "
            f"for {len(no_email)} leads..."
        )
        
        # Phase 1: Catch-All Detection
        # Check all domains concurrently
        domain_list = list(domain_leads.keys())
        tasks = [self._check_catch_all(domain) for domain in domain_list]
        catchall_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        still_missing_leads = []  # Leads that need JS scraping
        
        for domain, is_catch_all in zip(domain_list, catchall_results):
            if isinstance(is_catch_all, Exception):
                is_catch_all = False
                
            self._stats["domains_checked"] += 1
            domain_group = domain_leads[domain]
            
            if is_catch_all:
                self._stats["catchall_domains"] += 1
                logger.info(f"  🛑  {domain} is CATCH-ALL")
                # Since it's catch all, we can safely just guess standard first.last
                for lead in domain_group:
                    if lead.email and lead.email not in ("N/A", "N/A (invalid)"):
                        continue
                    
                    # Basic generation since any guess will deliver
                    first = lead.name.split()[0].lower()
                    last = lead.name.split()[-1].lower() if len(lead.name.split()) > 1 else ""
                    
                    email = f"{first}@{domain}" if not last else f"{first}.{last}@{domain}"
                    lead.email = email
                    lead.email_status = "catch_all_generated"
                    self._stats["leads_enriched_catchall"] += 1
                    logger.info(f"  🛑  Generated catch-all email for {lead.name}: {email}")
            else:
                # Not catch-all, needs JS scraping
                still_missing_leads.extend(domain_group)

        # Phase 2: JS Rendering via Playwright
        if still_missing_leads:
            js_domain_leads: Dict[str, List] = {}
            for lead in still_missing_leads:
                parsed = urlparse(
                    lead.website if "://" in lead.website else f"https://{lead.website}"
                )
                domain = parsed.netloc.lower().replace("www.", "")
                js_domain_leads.setdefault(domain, []).append(lead)
                
            logger.info(f"  🕷️  JS SCRAPE: rendering {len(js_domain_leads)} domains...")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                # Process sequentially so we don't blow up RAM, but could be chunked
                for domain, domain_group in js_domain_leads.items():
                    base_url = f"https://{domain}"
                    found_domain_emails = set()
                    
                    context = await browser.new_context()
                    page = await context.new_page()
                    
                    for path in _TARGET_PATHS:
                        url = f"{base_url}{path}"
                        emails = await self._scrape_js_page(url, domain, page)
                        found_domain_emails.update(emails)
                        
                        # Optimization: if we found enough emails for the leads we have, stop checking paths
                        if len(found_domain_emails) >= len(domain_group):
                            break
                            
                    await context.close()
                    self._stats["emails_found"] += len(found_domain_emails)
                    
                    # Match found emails to leads
                    if found_domain_emails:
                        logger.info(f"  🕷️  Found {len(found_domain_emails)} emails on {domain} via JS")
                        unmatched = list(found_domain_emails)
                        for lead in domain_group:
                            best_email = None
                            best_score = 0.0
                            for email in unmatched:
                                score = _match_email_to_name(email, lead.name)
                                if score > best_score:
                                    best_score = score
                                    best_email = email
                            
                            if best_email and best_score >= 0.3:
                                lead.email = best_email
                                lead.email_status = "js_scrape"
                                unmatched.remove(best_email)
                                self._stats["leads_enriched_js"] += 1
                                logger.info(f"  🕷️  JS Scraped email for {lead.name}: {best_email}")

                        # Second pass: JS emails might be generic (contact@, info@)
                        # Distribute remaining as fallbacks
                        for lead in domain_group:
                            if lead.email and lead.email not in ("N/A", "N/A (invalid)"):
                                continue
                            if unmatched:
                                best_email = unmatched[0]
                                lead.email = best_email
                                lead.email_status = "js_scrape"
                                unmatched.remove(best_email)
                                self._stats["leads_enriched_js"] += 1
                                logger.info(f"  🕷️  JS Scraped fallback email for {lead.name}: {best_email}")

                await browser.close()

        logger.info(
            f"  🛑  CATCH-ALL/JS complete: {self._stats['leads_enriched_catchall']} catch-all, "
            f"{self._stats['leads_enriched_js']} js-scraped "
            f"({self._stats['domains_checked']} domains checked, "
            f"{self._stats['catchall_domains']} were catch-all)"
        )
        return leads

    @property
    def stats(self) -> dict:
        return dict(self._stats)
