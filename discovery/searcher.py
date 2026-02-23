import asyncio
import re
import urllib.parse
from urllib.parse import urlparse
from typing import List, Set
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
import time
import os
import yaml

from stealth.fingerprint import FingerprintManager
from stealth.behavior import HumanBehavior
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class Searcher:
    """
    Automates Google searches to discover VC fund domains.
    Uses stealth injection and human-like browsing to avoid CAPTCHAs.
    """

    def __init__(self, config_path: str = "config/search.yaml"):
        # Load config directly
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f).get("discovery", {})
            
        self.queries = self.config.get("queries", [])
        self.ignore_domains = set(self.config.get("ignore_domains", []))
        self.target_count = self.config.get("target_domains_count", 350)
        self.behavior = HumanBehavior()
        self.fingerprints = FingerprintManager()

    def _is_valid_domain(self, url: str) -> bool:
        """Checks if a URL belongs to a valid VC fund (not an aggregator/social site)."""
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            
            for ignored in self.ignore_domains:
                if ignored in domain:
                    return False
            
            if domain.endswith(".jp") or domain.endswith(".cn"): return False
            if "google" in domain or "bing" in domain: return False
            
            return True
        except:
            return False

    def _get_base_url(self, url: str) -> str:
        """Extracts just the protocol + domain from a URL."""
        try:
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}"
        except:
            return url

    async def _extract_ddg_results(self, page: Page) -> List[str]:
        """Extract organic search results from DuckDuckGo."""
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        found_urls = []
        for a in soup.find_all("a"):
            href = a.get("href")
            if not href: continue
            
            # If it's a redirect link
            if "uddg=" in href:
                try:
                    parsed = urlparse(href)
                    qs = urllib.parse.parse_qs(parsed.query)
                    if "uddg" in qs:
                        real_url = urllib.parse.unquote(qs["uddg"][0])
                        if real_url.startswith("http"):
                            found_urls.append(real_url)
                except: pass
            # If it's a direct link
            elif href.startswith("http") and "duckduckgo.com" not in href:
                found_urls.append(href)
                
        return found_urls

    async def discover(self) -> Set[str]:
        """Executes search queries and returns a set of unique VC domains."""
        discovered_domains = set()
        logger.info(f"🔍 Starting discovery engine for {self.target_count} target domains")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            fp = self.fingerprints.generate()
            ctx = await browser.new_context(
                **self.fingerprints.get_context_kwargs(fp)
            )
            page = await ctx.new_page()
            await self.fingerprints.apply_js_overrides(page)

            for query in self.queries:
                if len(discovered_domains) >= self.target_count:
                    break
                    
                logger.info(f"🔎 Querying DDG: {query}")
                encoded_query = urllib.parse.quote_plus(query)
                search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
                
                try:
                    await page.goto(search_url, wait_until="networkidle")
                    import random
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                    
                    if "Robot Check" in await page.title():
                        logger.error("🚨 DDG CAPTCHA triggered. Cooling down...")
                        await asyncio.sleep(60)
                        break
                    
                    urls = await self._extract_ddg_results(page)
                    new_count = 0
                    for url in urls:
                        if self._is_valid_domain(url):
                            base_url = self._get_base_url(url)
                            if base_url not in discovered_domains:
                                discovered_domains.add(base_url)
                                new_count += 1
                                
                    logger.info(f"➕ Found {new_count} valid VC domains. (Total: {len(discovered_domains)}/{self.target_count})")
                    await asyncio.sleep(random.uniform(5.0, 10.0))
                    
                except Exception as e:
                    logger.error(f"❌ Error during query '{query}': {str(e)}")
                    
            await browser.close()
            
        return discovered_domains

if __name__ == "__main__":
    searcher = Searcher()
    
    os.makedirs("data", exist_ok=True)
    domains = asyncio.run(searcher.discover())
    
    # Save results to a text file
    with open("data/target_funds.txt", "w") as f:
        for domain in sorted(domains):
            f.write(domain + "\n")
            
    logger.info(f"💾 Saved {len(domains)} target domains to data/target_funds.txt")
