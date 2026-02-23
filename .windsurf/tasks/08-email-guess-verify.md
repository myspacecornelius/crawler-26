# Agent Brief: SMTP-Verified Email Pattern Discovery

## Objective
The email guesser currently generates a single `first.last@domain` guess per contact and never SMTP-verifies it. For domains where the real pattern is `first@domain` or `flast@domain`, the guessed email is wrong. Fix the pipeline to SMTP-verify the top candidates per domain and lock in the correct pattern.

## Scope
**Primary file:** `enrichment/email_guesser.py`
**Secondary file:** `enrichment/email_validator.py` (read-only reference for SMTP methods)

**Do NOT modify:** `deep_crawl.py`, `engine.py`, any API files, any router files

## Current Architecture

### EmailGuesser (`enrichment/email_guesser.py`)
- `_PATTERNS` (line ~25): 8 patterns ordered by prevalence
- `_DEFAULT_PATTERN` (line ~38): `{first}.{last}@{domain}` — used when no pattern is learned
- `_PatternCache`: learns patterns from contacts that already have scraped emails (almost never triggered because team pages rarely display emails)
- `guess_batch()` pipeline:
  1. Phase 1: Learn patterns from existing scraped emails (almost always empty)
  2. Phase 2: Apply learned patterns (almost never fires)
  3. Phase 3: Check domain MX → apply default pattern (this is where 99% of guesses come from)
- **No SMTP verification is done by the guesser** — it only checks MX records (domain-level)

### EmailValidator (`enrichment/email_validator.py`)
- `verify_smtp(email)` — SMTP RCPT TO check for a single email. Returns `{"deliverable": bool|None, "catch_all": bool}`
- `verify_smtp_batch(emails)` — batch SMTP check with concurrency control
- These are called AFTER guessing by the engine, but only to tag existing guesses — never to discover the correct pattern

## Diagnosed Problems

### Problem 1: Only guesses one pattern, never verifies
The guesser applies `first.last@domain` and moves on. If the real pattern is `first@domain`, the guess is wrong and SMTP later tags it "unknown."

**Fix:** For each new domain, SMTP-verify the top 3 pattern candidates for ONE contact. Whichever candidate is deliverable, lock that pattern in the `_PatternCache` for all contacts at that domain.

### Problem 2: Pattern learning only from scraped emails
```python
# Phase 1: Learn patterns from existing emails
for lead in leads:
    if lead.email and lead.email not in ("N/A", "N/A (invalid)") and "@" in lead.email:
        self._pattern_cache.learn(domain, lead.email, lead.name)
```
Team pages almost never display emails, so the cache stays empty.

**Fix:** After Phase 1, add a new Phase 1.5: "Pattern Discovery via SMTP." Pick one contact per unknown domain, generate top 3 candidates, SMTP-verify them. Lock in the first deliverable pattern.

### Problem 3: `_is_person_name` blocklist includes "partner"
```python
_COMPANY_WORDS = { ..., "partner", ... }
```
The word "partner" is in `_COMPANY_WORDS`, which means any name extraction error that concatenates the role (e.g., "John Smith Partner") gets rejected. More importantly, it can false-positive on legitimate names.

**Fix:** Remove "partner" from `_COMPANY_WORDS`. It's already too broadly matching. The `looks_like_name` function in deep_crawl.py handles the real filtering.

## Implementation Plan

### Step 1: Add SMTP pattern discovery method
Add a new method to `EmailGuesser`:
```python
async def _discover_domain_pattern(self, name: str, domain: str) -> Optional[str]:
    """SMTP-verify top 3 candidates for one contact to discover domain's email pattern."""
    candidates = generate_candidates(name, domain)[:3]  # first.last, first, flast
    for candidate in candidates:
        result = await self.validator.verify_smtp(candidate)
        if result.get("deliverable") is True:
            pattern = detect_pattern(candidate, name)
            if pattern:
                self._pattern_cache._patterns[domain] = pattern
                self._stats["patterns_discovered"] += 1
                return candidate
    return None
```

### Step 2: Insert Phase 1.5 into guess_batch
After Phase 1 (learn from scraped) and before Phase 2 (apply cached), add:
```python
# Phase 1.5: Discover patterns via SMTP for unknown domains
# Pick one contact per domain, probe top 3 patterns
domains_to_probe = {}
for lead in no_email:
    if not _is_person_name(lead.name):
        continue
    domain = _extract_domain(lead.website)
    if domain and not self._pattern_cache.get(domain) and domain not in domains_to_probe:
        domains_to_probe[domain] = lead

logger.info(f"  🔍  Probing {len(domains_to_probe)} domains for email patterns via SMTP...")
for domain, lead in domains_to_probe.items():
    await self._discover_domain_pattern(lead.name, domain)
```

### Step 3: Fix _COMPANY_WORDS
Remove "partner" from `_COMPANY_WORDS` set.

### Step 4: Add stats tracking
Add `"patterns_discovered"` to `self._stats` dict initialization.

## Testing

Create `tests/test_email_discovery.py` with:
1. Test that `generate_candidates` produces correct patterns for a sample name
2. Test that `_is_person_name("John Partner")` returns True after fix (currently False)
3. Test that `_discover_domain_pattern` is callable and returns None when SMTP unavailable
4. Test that Phase 1.5 is integrated into `guess_batch` (mock SMTP to return deliverable for `first@domain`)
5. Test pattern cache propagation: after discovering `first@domain` for one contact, all other contacts at that domain should use the same pattern

Run with: `venv/bin/python -m pytest tests/test_email_discovery.py -v`

## Concurrency / Rate Limiting Notes
- SMTP probing should respect the existing `self._sem` semaphore (concurrency=10)
- Limit to probing 3 candidates per domain (not all 8 patterns)
- Add a 0.5s delay between SMTP probes to avoid triggering rate limits
- If all 3 probes fail (unknown/timeout), fall back to default pattern (current behavior)

## Acceptance Criteria
- [ ] New `_discover_domain_pattern` method added
- [ ] Phase 1.5 (SMTP pattern discovery) integrated into `guess_batch`
- [ ] "partner" removed from `_COMPANY_WORDS`
- [ ] `patterns_discovered` stat tracked and logged
- [ ] All new tests pass
- [ ] Existing tests still pass: `venv/bin/python -m pytest tests/ -v`
