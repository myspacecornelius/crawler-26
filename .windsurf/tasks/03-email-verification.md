# Task 3: Wire SMTP Email Verification Into Pipeline

## Scope
Connect the existing SMTP RCPT TO verification code into the main enrichment pipeline so that ALL guessed emails get deliverability-checked before export. Currently 96% of emails (2,096 of 2,184) are unverified `first.last@domain.com` guesses. Add a `Verified` column to CSV output and make SMTP verification run by default (not behind a flag).

## Files to Reference (use @ mentions in Cascade)
When starting this task, tell Cascade:
> Read these files first:
> @enrichment/email_validator.py — the full file. Focus on `verify_smtp()` at lines 138-228 (RCPT TO logic), `_resolve_mx_host()` at lines 121-136, and `_catch_all_cache` at line 38
> @engine.py lines 309-394 — `_enrich_and_output()` method. Lines 355-370 have the SMTP verification block currently behind `--verify_smtp` flag
> @enrichment/email_guesser.py lines 200-260 — `guess_batch()` to understand how guessed emails are assigned
> @adapters/base.py lines 21-50 — InvestorLead dataclass (note: there is NO `email_verified` field currently — you'll need to add one or use a convention)
> @output/csv_writer.py — FIELDNAMES list at lines 22-26 (you'll add "Email Status" column)

## DO NOT MODIFY
- `deep_crawl.py` (handled by Task 2)
- `enrichment/scoring.py` (handled by Task 1)
- `api/` directory (handled by Task 5)
- `dashboard/` directory (handled by Task 5)

## Current State

### What exists
- `EmailValidator.verify_smtp(email)` is fully implemented — it does MX resolution, SMTP HELO, MAIL FROM, RCPT TO, and catch-all detection
- It returns `{"deliverable": bool|None, "smtp_code": int, "catch_all": bool}`
- There's MX host caching (`_mx_host_cache`) and catch-all caching (`_catch_all_cache`) for efficiency
- The engine has an SMTP block at lines 355-370 but it's behind `--verify_smtp` flag and runs sequentially (slow)

### What's broken/missing
1. **Not running by default**: SMTP verification only runs with `--verify_smtp` CLI flag, which nobody uses
2. **Sequential execution**: The current implementation verifies one email at a time — for 2,000+ emails this would take hours
3. **No status column in CSV**: Results aren't persisted — even if you run verification, the CSV just appends "⚠️ (undeliverable)" to the email string instead of having a clean status column
4. **No batch concurrency**: Need `asyncio.Semaphore`-bounded concurrent SMTP checks (e.g., 20 concurrent connections)
5. **No rate limiting per domain**: Sending 50 RCPT TO checks to the same MX server in quick succession will get you blocked

## Requirements

### 1. Make SMTP verification run by default (with opt-out)
- Change the flag from `--verify_smtp` (opt-in) to `--skip-smtp` (opt-out)
- In `_enrich_and_output()`, run SMTP verification unless `--skip-smtp` is set

### 2. Add concurrent batch SMTP verification
Create a new method `EmailValidator.verify_smtp_batch(emails: list[str], concurrency: int = 20) -> dict[str, dict]`:
- Uses `asyncio.Semaphore(concurrency)` to limit parallel connections
- Groups emails by domain and adds a 1-second delay between checks to the same MX server
- Returns `{email: {"deliverable": bool|None, "smtp_code": int, "catch_all": bool}}`
- Logs progress every 100 emails

### 3. Add email status tracking
- Add `email_status: str = "unknown"` field to `InvestorLead` dataclass in `adapters/base.py`
  - Values: "verified" | "undeliverable" | "catch_all" | "unknown" | "scraped" | "guessed"
- Add "Email Status" to `CSVWriter.FIELDNAMES` and the write mapping
- Set status based on SMTP results:
  - `deliverable=True, catch_all=False` → "verified"
  - `deliverable=True, catch_all=True` → "catch_all"
  - `deliverable=False` → "undeliverable"
  - `deliverable=None` → "unknown"
- Emails scraped directly from pages should be marked "scraped" before verification

### 4. Update engine enrichment flow
In `_enrich_and_output()`:
1. Mark pre-existing scraped emails as status="scraped"
2. After email guessing, mark guessed emails as status="guessed"
3. Run SMTP batch verification on all emails with status in ("scraped", "guessed")
4. Update status based on SMTP results
5. Print summary: X verified, Y undeliverable, Z catch-all, W unknown
6. **Do NOT mangle the email string** — keep `lead.email` clean (just the address), put status in `lead.email_status`

## Acceptance Criteria
- [ ] Running `venv/bin/python engine.py --deep --headless --force-recrawl` now includes SMTP verification automatically
- [ ] CSV has clean "Email Status" column with values: verified/undeliverable/catch_all/unknown/scraped/guessed
- [ ] Email column contains only clean email addresses (no "⚠️ (undeliverable)" appended)
- [ ] SMTP verification processes 2,000+ emails in under 10 minutes (concurrent, not sequential)
- [ ] Rate limiting: no more than 5 RCPT TO checks per MX server per second
- [ ] All 167 existing tests still pass: `venv/bin/python -m pytest tests/ -x -q`

## Data Contracts
- **Input**: List of `InvestorLead` objects with `.email` field populated
- **Output**: Same leads with `.email_status` set, written to CSV with "Email Status" column
- **SMTP API**: `verify_smtp_batch(emails) → {email: {deliverable, smtp_code, catch_all}}`

## Performance Notes
- ~2,000 emails across ~400 unique domains
- Most domains share a few common MX providers (Google Workspace, Microsoft 365)
- MX host caching is critical — resolve once per domain, reuse for all emails
- Catch-all detection should happen once per domain, not per email
- Expect: ~60% verified, ~15% undeliverable, ~15% catch-all, ~10% unknown (timeout/refused)
