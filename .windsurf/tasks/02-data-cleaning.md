# Task 2: Data Cleaning & Filtering

## Scope
Remove non-person leads from the output, fix garbled/truncated roles, and ensure only real human contacts appear in the final CSV. Currently 579 rows are fund-level entries (Name == Fund Name like "Pear VC"), 51% of leads have N/A roles, and ~52 leads have garbled roles containing UI artifacts.

## Files to Reference (use @ mentions in Cascade)
When starting this task, tell Cascade:
> Read these files first:
> @deep_crawl.py lines 240-370 — extract_name_role_pairs() function and helpers (name/role extraction from HTML)
> @deep_crawl.py lines 532-600 — _extract_from_page() method (builds InvestorLead objects from extractions)
> @enrichment/email_guesser.py lines 41-78 — _COMPANY_WORDS and _is_person_name() (person name validation)
> @engine.py lines 158-205 — deep crawl merge logic (where fund-level rows get mixed in with person-level contacts)
> @engine.py lines 107-136 — _run_aggregator() merge (where seed database leads enter the pipeline)
> @adapters/base.py lines 21-50 — InvestorLead dataclass

## DO NOT MODIFY
- `enrichment/scoring.py` (handled by Task 1)
- `output/csv_writer.py` (handled by Task 1)
- `enrichment/email_validator.py` (handled by Task 3)
- `api/` directory
- `dashboard/` directory

## Current State (What's Broken)

### Problem 1: Fund-level rows polluting output
579 leads have `name == fund` (e.g., Name="Pear VC", Fund="Pear VC"). These come from the seed database (`sources/aggregator.py`) and represent the *fund itself*, not a person. They were never enriched with person-level data from deep crawl. They should be filtered out of the final output — or flagged as "fund-level" and excluded from person-contact exports.

### Problem 2: Garbled roles (UI artifact text)
Examples from the current CSV:
- `"Learn More ⟶"` (button text scraped as role)
- `"Experience No items found. Education No items found."` (Interplay.vc profile template)
- `"Explore our specialized investment areas in enterprise software"` (marketing copy)
- `"A differentiated investment partner for advisors and their clients."` (tagline)
- `"Co-founder of Andela Former Managing Director of Flutterwave More +"` (bio overflow)
- `"Chief Medical r"` (truncated — should be "Chief Medical Officer")

### Problem 3: N/A roles (51%)
1,446 leads have role="N/A". Many of these came from deep crawl pages where names were extracted but the role extraction heuristic didn't find a nearby role element. This is partially expected, but we should try harder — e.g., look at `<span>`, `<p>`, or sibling elements near the name `<h3>`/`<h4>`.

## Requirements
1. **Filter fund-level rows**: In `engine.py`'s `_enrich_and_output()` method (or a new post-processing step), remove leads where `lead.name.lower().strip() == lead.fund.lower().strip()` before writing to CSV. Keep them internally for metadata enrichment but don't export them as "leads."

2. **Fix garbled roles**: In `deep_crawl.py`'s `extract_name_role_pairs()`, add a `_clean_role_text()` post-processing step (or expand existing filtering) that:
   - Strips roles longer than 80 characters (these are always bio text, not titles)
   - Removes roles containing: "Learn More", "No items found", "Explore our", "More +", navigation arrows ("⟶", "→")
   - Fixes truncated roles ending in single letter + space (e.g., "Chief Medical r" → keep as-is but flag as truncated, or strip the trailing fragment)

3. **Improve role extraction coverage**: In `extract_name_role_pairs()`, when no role is found via the current heuristics, also check:
   - The element's parent for a `<span class="role">` or `<p class="title">` pattern
   - Any sibling element with a shorter text length (< 60 chars) that contains title keywords (Partner, Director, Associate, VP, Analyst, etc.)

## Acceptance Criteria
- [ ] Zero rows where Name == Fund Name in the final CSV
- [ ] Zero roles containing "Learn More", "No items found", "Explore our", "More +", "⟶"
- [ ] Zero roles longer than 80 characters
- [ ] Role coverage improves from 49% to at least 60%
- [ ] All 167 existing tests still pass: `venv/bin/python -m pytest tests/ -x -q`
- [ ] Run a quick test: `venv/bin/python -c "from deep_crawl import extract_name_role_pairs; from bs4 import BeautifulSoup; ..."` to validate extraction on a sample HTML snippet

## Data Contracts
- **Input**: Raw HTML from fund team pages → `extract_name_role_pairs(soup)` returns `[{"name": str, "role": str}, ...]`
- **Output**: Cleaned leads in `data/enriched/investor_leads_master.csv` with only person-level contacts
- **Validation**: `awk -F',' 'NR>1 && $1==$4' data/enriched/investor_leads_master.csv | wc -l` should return 0
