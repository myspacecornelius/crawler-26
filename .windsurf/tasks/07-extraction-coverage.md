# Agent Brief: Improve Team Member Extraction Coverage

## Objective
The `extract_name_role_pairs()` function in `deep_crawl.py` currently misses 40-70% of team members on most VC fund websites. Fix the extraction heuristics to achieve 90%+ coverage on well-structured team pages.

## Scope
**Single file:** `deep_crawl.py`
**Single function:** `extract_name_role_pairs()` (lines ~250-427) and its helpers

**Do NOT modify:** engine.py, email_guesser.py, any API files, any test files outside your new test file

## Current Architecture

The function has two strategies:
- **Strategy 1** (lines ~359-390): Find `div/li/article` containers with `h2-h5` headings + sibling with ROLE_KEYWORDS match
- **Strategy 2** (lines ~392-417): Fallback — same structure but relaxed role requirement (only if Strategy 1 found nothing)

## Diagnosed Problems (fix ALL of these)

### Problem 1: Only searches h2-h5 headings
```python
heading = container.find(["h2", "h3", "h4", "h5"])
```
Many VC sites put names in `<h6>`, `<strong>`, `<a>`, `<span class="name">`, or styled `<p>` tags.

**Fix:** Expand to `["h2", "h3", "h4", "h5", "h6", "strong"]` AND add a new strategy that finds elements by CSS class patterns.

### Problem 2: Container size limit of 2000 chars drops grid layouts
```python
if len(container.get_text()) > 2000:
    continue
```
Grid layouts wrapping all team members in one `<div>` get skipped entirely.

**Fix:** Remove or raise to 20000. The heading-level search inside the container is already scoped, so the size cap is counterproductive.

### Problem 3: Only checks immediate sibling for role text
```python
for sibling in [heading.find_next_sibling(), heading.find_next()]:
```
Only looks at first sibling. Many sites nest role text 2-3 levels deep.

**Fix:** Search up to 3 siblings deep, and also search within the heading's parent container for role-like text.

### Problem 4: Role sibling limited to p/span/div/small/em tags
```python
if sibling and sibling.name in ["p", "span", "div", "small", "em"]:
```
Misses `<strong>`, `<a>`, `<h6>`, `<label>`, `<dd>`, `<figcaption>`, `<cite>`.

**Fix:** Expand the allowed tag list or remove the tag restriction entirely (just check text content).

### Problem 5: Strategy 1 requires ROLE_KEYWORDS match — drops non-standard titles
```python
any(kw in candidate.lower() for kw in ROLE_KEYWORDS)
```
"Investor", "Team Member", "Operator", "Board Observer" etc. don't match.

**Fix:** Add missing keywords to `ROLE_KEYWORDS`: `"investor", "member", "operator", "observer", "mentor", "board", "team", "staff", "manager", "counsel", "secretary", "treasurer", "controller", "intern", "resident"`

### Problem 6: Need a new Strategy 0 — CSS class-based extraction
Many modern sites use semantic CSS classes like `team-member`, `person-card`, `staff-bio`, `team-grid__item`.

**Add:** Before Strategy 1, scan for elements whose `class` or `id` attributes contain team-related patterns (`team`, `member`, `person`, `staff`, `bio`, `people`). Extract name from the first heading-like child, role from first non-heading child text.

## ROLE_KEYWORDS reference (current, at line ~41)
```python
ROLE_KEYWORDS = [
    "partner", "principal", "associate", "analyst", "founder",
    "managing", "director", "vice president", "vp", "ceo",
    "cto", "cfo", "coo", "general partner", "venture partner",
    "operating partner", "senior associate", "investment",
    "head of", "chief", "chairman", "advisory", "advisor",
    "eir", "entrepreneur in residence", "scout", "fellow"
]
```

## Existing Helper Functions (do not break these)
- `looks_like_name(text)` — validates person names (keep as-is, it works well)
- `_role_is_actually_a_name(role_text)` — guards against off-by-one (keep as-is)
- `_clean_role_text(raw)` — cleans garbled role text (keep as-is)

## Testing

Create `tests/test_extraction_coverage.py` with:
1. Test HTML snippets representing 5+ different real-world layouts:
   - Standard h3 name + p role in div cards
   - CSS class-based (`<div class="team-member">`)
   - Grid layout (one large container with many members)
   - Name in `<strong>` or `<a>` tag
   - Role nested 2 levels deep
   - Name without any role text (on a `/team` URL)
2. For each snippet, assert the expected number of names extracted
3. Test that `ROLE_KEYWORDS` catches the expanded title set

Run with: `venv/bin/python -m pytest tests/test_extraction_coverage.py -v`

## Acceptance Criteria
- [ ] All 5 diagnosed problems fixed
- [ ] New Strategy 0 (CSS class-based) added before Strategy 1
- [ ] ROLE_KEYWORDS expanded with at least 10 new terms
- [ ] Container size cap raised to 20000 or removed
- [ ] Heading search includes h6 and strong
- [ ] Sibling search goes 3 levels deep
- [ ] Role tag whitelist expanded
- [ ] All new tests pass
- [ ] Existing tests still pass: `venv/bin/python -m pytest tests/ -v`
