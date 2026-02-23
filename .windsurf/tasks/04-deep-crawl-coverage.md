# Task 4: Improve Deep Crawl Coverage

## Scope
Increase per-fund contact extraction from the current average of ~5 contacts to 15-30+ for large firms. Currently many top-tier firms (a16z, Sequoia, Benchmark) return only 1-2 contacts despite having 50+ investment professionals. Fix pagination handling, try more team page URL patterns, and improve the HTML extraction heuristics.

## Files to Reference (use @ mentions in Cascade)
When starting this task, tell Cascade:
> Read these files first:
> @deep_crawl.py — the full file, but focus on:
>   - Lines 501-530: `_find_team_pages()` — discovers team page links from homepage
>   - Lines 652-720: `_crawl_fund()` — orchestrates per-fund crawling with timeout
>   - Lines 532-600: `_extract_from_page()` — extracts contacts from a single page
>   - Lines 240-370: `extract_name_role_pairs()` — the core name/role extraction from HTML
>   - Lines 744-800: `run()` — main loop with batched processing
> @adapters/base.py lines 21-50 — InvestorLead dataclass

## DO NOT MODIFY
- `engine.py` (except trivially if needed for a new CLI flag)
- `enrichment/` directory (handled by Tasks 1, 3)
- `output/` directory (handled by Task 1)
- `api/` directory (handled by Task 5)
- `dashboard/` directory (handled by Task 5)

## Current State

### What works
- Homepage → team page discovery via link text matching ("team", "people", "about us")
- `is_team_page_url()` catches common URL patterns (/team, /people, /about)
- Extracts names from `<h2>`, `<h3>`, `<h4>` headings
- Extracts roles from adjacent `<p>`, `<span>` elements
- Tries up to 5 team page URLs per fund
- 30-second hard timeout per fund
- Batched processing (10 funds per batch) prevents browser hangs

### What's broken/insufficient

1. **Stops after first successful page**: Line 700 has `break` after first page with contacts — so if /team has 3 people and /team/partners has 20 more, we only get 3.

2. **No pagination handling**: Many team pages use:
   - "Load More" / "Show All" buttons (JS-rendered)
   - `?page=2` / `?page=3` URL patterns
   - Infinite scroll
   Currently we only see what's in the initial DOM load.

3. **Missing team page patterns**: The fallback paths (line 678) are limited to `/team`, `/about`, `/people`, `/about-us`, `/our-team`. Missing:
   - `/team/` (trailing slash matters for some servers)
   - `/leadership`
   - `/who-we-are`
   - `/about/team`
   - `/company/team`
   - `/investors` (some funds list their own partners here)

4. **JS-rendered team pages not handled**: Many modern fund sites (a16z, Sequoia) render team grids via React/Next.js. The `domcontentloaded` wait doesn't wait for JS rendering. Need `networkidle` or explicit waits.

5. **Single-person detail pages**: Some sites (e.g., `jumpcap.com/team-members/michael-mcmahon/`) list one person per page. We find and visit these but it's very inefficient for sites with 30+ team members on individual pages.

## Requirements

### 1. Don't stop after first successful page
Remove the `break` at line 700. Instead, accumulate contacts from ALL team pages (up to the limit of 5), dedup by name before returning.

### 2. Add "Load More" / pagination handling
After extracting from a team page, check for:
- A button or link with text matching: "Load More", "Show More", "View All", "See All Team"
- If found, click it and wait 2 seconds, then re-extract
- Repeat up to 3 times
- Also check for `?page=2` style pagination links — if the page has `<a href="/team?page=2">`, visit pages 2-5

### 3. Expand team page URL patterns
Add to the fallback paths list:
```python
"/team/", "/leadership", "/who-we-are", "/about/team",
"/company/team", "/investors", "/partners", "/our-people",
"/about#team", "/about-us#team"
```

### 4. Wait for JS rendering on team pages
Change the team page `wait_until` from `"domcontentloaded"` to `"networkidle"` (line 686). Add a 1-second post-load delay to let lazy-loaded content appear.

### 5. Dedup contacts within a fund
Before returning contacts from `_crawl_fund()`, dedup by `contact.name.lower()` to avoid duplicates when multiple pages list the same person.

## Acceptance Criteria
- [ ] Re-crawl these 5 funds and verify improved extraction:
  - `a16z.com` → should get 20+ contacts (currently gets 1-2)
  - `sequoiacap.com` → should get 30+ (currently gets 17 from one sub-page)
  - `redpoint.com` → should get 30+ (currently gets 40 — baseline)
  - `greylock.com` → should get 10+ (currently gets 3)
  - `benchmark.com` → should get 5+ (currently gets 0)
- [ ] Test with: `venv/bin/python deep_crawl.py --targets data/test_targets.txt --limit 5 --headless`
  (create `data/test_targets.txt` with the 5 URLs above)
- [ ] Total contact yield across full 573-fund crawl increases from ~2,900 to 4,000+
- [ ] No fund takes longer than 45 seconds (current 30s timeout may need slight increase for pagination)
- [ ] All 167 existing tests still pass: `venv/bin/python -m pytest tests/ -x -q`

## Data Contracts
- **Input**: Fund URL → `_crawl_fund(browser, fund_url)` → `List[InvestorLead]`
- **Output**: More contacts per fund, deduped by name
- **No schema changes needed** — same InvestorLead dataclass, same CSV format
