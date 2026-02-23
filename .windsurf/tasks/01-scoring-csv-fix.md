# Task 1: Fix CSV Column Alignment & Scoring Pipeline

## Scope
Fix the lead scoring pipeline so scores are correctly computed, stored, and written to CSV. Add role-based weighting so Partner > Associate > Coordinator. The current output has broken score values — the CSV `Lead Score` column contains location strings like "San Francisco CA" instead of integers.

## Files to Reference (use @ mentions in Cascade)
When starting this task, tell Cascade:
> Read these files first:
> @enrichment/scoring.py — the LeadScorer class (scoring algorithm, tier assignment)
> @output/csv_writer.py — CSVWriter class (writes leads to CSV, field mapping at lines 60-76)
> @adapters/base.py lines 21-50 — the InvestorLead dataclass (the data model all leads use)
> @config/scoring.yaml — scoring weights, tiers, modifiers config
> @engine.py lines 309-394 — the _enrich_and_output method (where scoring + CSV writing happens)

## DO NOT MODIFY
- `deep_crawl.py`
- `enrichment/email_guesser.py`
- `enrichment/email_validator.py`
- `api/` directory
- `dashboard/` directory
- Any adapter files

## Current State (What's Broken)
1. **CSV column misalignment**: When you read the master CSV and parse column 11 (Lead Score), you get location values like "San Francisco CA", "New York NY" — not integer scores. This means the `InvestorLead.to_dict()` output keys don't line up with `CSVWriter.FIELDNAMES`.

2. **Scoring has no role weighting**: A Managing Partner and an Events Coordinator at the same fund get identical scores. The scoring dimensions are: stage match, sector match, check size, portfolio relevance, recency, and contact quality modifiers — but there's nothing for role seniority.

3. **InvestorLead.focus_areas is a list** but the CSV writer serializes it as-is. Commas inside focus_areas (e.g., `"Enterprise, SaaS, AI"`) break CSV column alignment when the field isn't properly quoted.

## Requirements
1. **Debug the CSV column issue**: Trace `InvestorLead.to_dict()` → `CSVWriter.write()` and find where columns shift. The likely cause is `focus_areas` being a list that serializes with commas, breaking the CSV structure. Fix the serialization so focus_areas is properly quoted or joined.

2. **Add role-based scoring modifier** to `LeadScorer.score()`:
   - Partner/GP/Managing Director: +15
   - Principal/VP/Director: +10
   - Associate/Analyst: +5
   - Coordinator/Admin/Assistant/Intern: -5
   - Unknown/N/A: +0
   Add this to `config/scoring.yaml` under `modifiers`.

3. **Verify round-trip**: After fixes, run `venv/bin/python -c "..."` to score a sample lead and confirm the CSV output has integer scores in the correct column.

## Acceptance Criteria
- [ ] `awk -F',' 'NR>1{print $11}' data/enriched/investor_leads_master.csv | head -20` shows integer scores (0-100), not locations
- [ ] Partners score higher than Associates at the same fund
- [ ] `focus_areas` with commas don't break CSV parsing
- [ ] All 167 existing tests still pass: `venv/bin/python -m pytest tests/ -x -q`

## Data Contracts
- **Input**: List of `InvestorLead` objects (defined in `adapters/base.py`)
- **Output**: CSV file at `data/enriched/investor_leads_master.csv` with columns: Name, Email, Role, Fund, Focus Areas, Stage, Check Size, Location, LinkedIn, Website, Lead Score, Tier, Source, Scraped At
- **Config**: `config/scoring.yaml` (YAML dict with weights, tiers, modifiers)
