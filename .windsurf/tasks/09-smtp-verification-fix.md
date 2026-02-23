# Agent Brief: Fix SMTP Verification — 0% Verified Rate

## Objective
The SMTP batch verification in `enrichment/email_validator.py` returns "unknown" for 100% of emails. Diagnose and fix so that deliverable emails are correctly tagged as "verified" and undeliverable ones as "undeliverable."

## Scope
**Single file:** `enrichment/email_validator.py`

**Do NOT modify:** `deep_crawl.py`, `engine.py`, `email_guesser.py`, any API files

## Current Architecture

### EmailValidator (`enrichment/email_validator.py`)
- `verify_smtp(email)` — single email SMTP RCPT TO check
- `verify_smtp_batch(emails)` — batch wrapper with concurrency
- Called by engine.py after email guessing to tag email_status as verified/undeliverable/catch_all/unknown

### Current Behavior
From the last crawl run:
```
📬  SMTP verification on 62 emails...
📬  SMTP batch complete: 62/62 emails checked
📬  SMTP summary: 0 verified, 0 undeliverable, 0 catch-all, 62 unknown
```
Every single email comes back as "unknown" — meaning `verify_smtp` is returning `{"deliverable": None}` for all of them.

## Diagnosed Problems

### Problem 1: Likely DNS resolution or socket timeout
The SMTP check needs to:
1. Resolve MX records for the domain
2. Open a TCP connection to the MX server on port 25
3. Send HELO, MAIL FROM, RCPT TO
4. Interpret the response code

If step 1-2 fails (DNS timeout, port 25 blocked by ISP/firewall, connection refused), the result falls through to "unknown."

**Diagnosis steps:**
1. Read the `verify_smtp` method implementation carefully
2. Check if there's proper error handling vs silent catch-all
3. Check timeout values — too short timeouts on residential networks cause 100% failure
4. Check if the HELO domain is set to something reasonable (many SMTP servers reject connections from `localhost`)

### Problem 2: Port 25 may be blocked
Many ISPs and cloud providers (AWS, GCP, residential) block outbound port 25. This would cause every SMTP connection to timeout.

**Fix options (implement in priority order):**
1. Try port 587 as fallback when port 25 fails
2. Add a "can we do SMTP at all?" self-test at startup that checks one known-good domain (e.g., gmail.com MX)
3. If SMTP is completely blocked, log a clear warning and skip rather than returning "unknown" for everything
4. Consider adding an optional SMTP proxy/relay configuration via environment variable `SMTP_PROXY_HOST`

### Problem 3: Missing or bad HELO/EHLO domain
```python
# The HELO domain should be a real-looking domain, not "localhost"
# Many mail servers reject connections from suspicious HELO domains
```

**Fix:** Use a configurable HELO domain (env var `SMTP_HELO_DOMAIN`) defaulting to something like `mail.leadfactory.io` or auto-detect from the machine's hostname.

### Problem 4: Timeout too aggressive
Residential connections to SMTP servers can take 5-10 seconds. If the timeout is set to 2-3 seconds, most connections will fail.

**Fix:** Ensure connection timeout is at least 10 seconds, and the overall operation timeout is at least 15 seconds per email.

## Implementation Plan

### Step 1: Add SMTP self-test
Add a method that runs once at startup:
```python
async def smtp_self_test(self) -> bool:
    """Test if outbound SMTP (port 25) is available from this network."""
    # Try connecting to a known MX (e.g., gmail-smtp-in.l.google.com:25)
    # Return True if TCP connection succeeds, False if blocked
```

### Step 2: Fix verify_smtp
- Increase timeouts to 10s connect / 15s total
- Use a proper HELO domain
- Try port 587 as fallback
- Add detailed logging for each failure mode (DNS fail, connection refused, timeout, SMTP error code)

### Step 3: Add diagnostic logging
Every SMTP check should log the failure reason at DEBUG level so we can trace exactly where things break:
```
DEBUG: SMTP gmail.com → MX: gmail-smtp-in.l.google.com → connect OK → HELO OK → RCPT TO: 250 OK → deliverable=True
DEBUG: SMTP badomain.xyz → MX: none → deliverable=None (no MX)
DEBUG: SMTP acme.vc → MX: mail.acme.vc → connect TIMEOUT (10s) → deliverable=None
```

### Step 4: Graceful degradation
If `smtp_self_test()` fails, print a clear warning:
```
⚠️  Outbound SMTP (port 25) appears blocked on this network.
    SMTP verification will be skipped. Emails tagged as "guessed" only.
    To enable: use a network that allows port 25, or set SMTP_PROXY_HOST env var.
```

## Testing

Create `tests/test_smtp_fix.py` with:
1. Test `smtp_self_test` returns a boolean
2. Test `verify_smtp` with a known-invalid email format returns `deliverable=False`
3. Test `verify_smtp` timeout handling (mock socket to simulate timeout)
4. Test that port 587 fallback is attempted when port 25 fails
5. Test HELO domain configuration from env var
6. Test graceful degradation warning message

Run with: `venv/bin/python -m pytest tests/test_smtp_fix.py -v`

## Environment Variables
- `SMTP_HELO_DOMAIN` — HELO identity (default: auto-detect hostname)
- `SMTP_PROXY_HOST` — optional SMTP relay for networks that block port 25
- `SMTP_TIMEOUT` — connection timeout in seconds (default: 10)

## Acceptance Criteria
- [ ] SMTP self-test added and runs at first verification call
- [ ] verify_smtp timeouts increased to 10s/15s
- [ ] HELO domain configurable and defaults to something reasonable
- [ ] Port 587 fallback when port 25 fails
- [ ] Detailed DEBUG logging for each SMTP step
- [ ] Graceful degradation when SMTP is blocked
- [ ] All new tests pass
- [ ] Existing tests still pass: `venv/bin/python -m pytest tests/ -v`
