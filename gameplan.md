# 🕷️ CRAWL — The Investor Lead Machine

> _"Don't wait to be discovered. Discover them first."_

---

## 🎯 Mission

Build an **autonomous, intelligent web crawling engine** that harvests investor leads from public directories, enriches them with context, and outputs ready-to-pitch contact sheets — all while flying under the radar with human-like behavior.

This isn't just a scraper. It's a **pipeline**.

```
┌─────────────┐     ┌───────────────┐     ┌─────────────────┐     ┌──────────────┐
│  🌐 CRAWL   │ ──▸ │  🧹 CLEAN     │ ──▸ │  🧠 ENRICH      │ ──▸ │  📊 OUTPUT   │
│  Multi-site  │     │  Dedup, norm  │     │  LinkedIn, fund  │     │  CSV / Sheets│
│  stealth nav │     │  validate     │     │  stage, thesis   │     │  Airtable    │
└─────────────┘     └───────────────┘     └─────────────────┘     └──────────────┘
```

---

## 🏗️ Architecture

### Phase 1 — Foundation (engine.py → engine v2)

The current `engine.py` is a solid skeleton. Upgrade it into a proper multi-source crawler:

- [ ] **Config-driven targets** — YAML file with site definitions (URL, selectors, pagination strategy)
- [ ] **Site adapters** — Pluggable adapter classes per directory (OpenVC, AngelMatch, Signal, Crunchbase, etc.)
- [ ] **Selector registry** — Central mapping of site → CSS/XPath selectors, easy to update when sites change
- [ ] **Pagination engine** — Auto-detect and handle: infinite scroll, "Load More" buttons, numbered pages, cursor-based APIs
- [ ] **Session management** — Cookie persistence, login flows for gated directories

```python
# sites.yaml (example)
sites:
  openvc:
    url: "https://openvc.app/investors"
    adapter: "openvc"
    selectors:
      card: ".investor-card"
      name: "h3.name"
      email: "a[href^='mailto:']"
      focus: ".investment-focus span"
    pagination:
      type: "infinite_scroll"
      scroll_count: 20
  
  angelmatch:
    url: "https://angelmatch.io/investors"
    adapter: "angelmatch"
    # ...
```

### Phase 2 — Stealth & Anti-Detection

Getting blocked = game over. Build the ghost layer:

- [ ] **Fingerprint rotation** — Randomized browser fingerprints (viewport, fonts, WebGL, canvas)
- [ ] **Proxy pool** — Rotating residential proxies (BrightData / SmartProxy integration)
- [ ] **Human behavior simulation**
  - Random mouse movements & jitter
  - Variable scroll speeds
  - Gaussian-distributed delays (no uniform `random.randint`)
  - Tab switching, focus/blur events
- [ ] **Request throttling** — Adaptive rate limiting based on response codes
- [ ] **Captcha detection** — Pause and alert (or integrate 2Captcha/CapSolver for auto-solve)

```python
# Human-like delay distribution
import numpy as np

def human_delay():
    """Returns a delay sampled from human reaction time distribution."""
    return max(0.5, np.random.normal(loc=2.5, sec=1.2))
```

### Phase 3 — Data Enrichment Pipeline

Raw names + emails aren't enough. Build context:

- [ ] **Email validation** — MX record check + SMTP verification (don't waste pitches on dead emails)
- [ ] **LinkedIn enrichment** — Match name → LinkedIn profile → title, fund, connections
- [ ] **Fund intelligence** — Pull fund size, stage preference, sector focus, recent investments
- [ ] **Portfolio analysis** — What companies has this investor backed? Any overlap with your space?
- [ ] **Scoring algorithm** — Rank leads by fit:

```
LEAD SCORE = (stage_match × 30) + (sector_match × 25) + (check_size_fit × 20) 
           + (portfolio_relevance × 15) + (recency × 10)
```

| Score Range | Priority   | Action                    |
|-------------|------------|---------------------------|
| 80–100      | 🔴 HOT    | Warm intro or direct cold |
| 60–79       | 🟡 WARM   | Research then reach out   |
| 40–59       | 🟢 COOL   | Add to drip sequence      |
| 0–39        | ⚪ COLD   | Archive for later         |

### Phase 4 — Output & Integration

Make the data immediately actionable:

- [ ] **Master CSV** — Deduplicated, scored, sorted by priority
- [ ] **Google Sheets sync** — Auto-push to a shared fundraising tracker
- [ ] **Airtable integration** — CRM-style view with status tracking (Researched → Contacted → Responded → Meeting)
- [ ] **Notion export** — Formatted investor profiles with fund details
- [ ] **Email draft generator** — Template-based cold emails personalized per investor (their portfolio, thesis, recent activity)

### Phase 5 — Monitoring & Automation

Set it and ~~forget it~~ monitor it:

- [ ] **Cron scheduling** — Daily/weekly crawl runs
- [ ] **Delta detection** — Only flag NEW investors since last run
- [ ] **Discord/Slack webhooks** — Real-time alerts when high-score leads are found
- [ ] **Dashboard** — Simple web UI showing crawl stats, lead counts, pipeline health

---

## 📁 Target Directory

### Tier 1 — High Value / Easy Access

| Source | Type | Gated? | Data Quality |
|--------|------|--------|-------------|
| OpenVC | Angel/VC directory | No | ⭐⭐⭐⭐ |
| AngelMatch | Angel investor matching | Freemium | ⭐⭐⭐⭐ |
| Signal (NFX) | VC discovery | Yes | ⭐⭐⭐⭐⭐ |
| Visible.vc | Investor database | Freemium | ⭐⭐⭐⭐ |

### Tier 2 — Requires More Work

| Source | Type | Gated? | Data Quality |
|--------|------|--------|-------------|
| Crunchbase | Company/investor data | Paid API | ⭐⭐⭐⭐⭐ |
| PitchBook | VC/PE data | Enterprise | ⭐⭐⭐⭐⭐ |
| LinkedIn | Professional network | Anti-bot | ⭐⭐⭐⭐ |
| Twitter/X | Public investor posts | API limits | ⭐⭐⭐ |

### Tier 3 — Supplementary

| Source | Type | Gated? | Data Quality |
|--------|------|--------|-------------|
| Y Combinator | Accelerator alumni list | No | ⭐⭐⭐ |
| AngelList | Startup ecosystem | Partial | ⭐⭐⭐⭐ |
| Product Hunt | Investor profiles | No | ⭐⭐⭐ |
| SEC EDGAR | Public filings | No | ⭐⭐⭐⭐ |

---

## 🗂️ File Structure (Target)

```
crawl/
├── engine.py              # Main orchestrator
├── gameplan.md            # This file
├── config/
│   ├── sites.yaml         # Target site definitions
│   ├── proxies.yaml       # Proxy pool config
│   └── scoring.yaml       # Lead scoring weights
├── adapters/
│   ├── base.py            # BaseSiteAdapter (abstract)
│   ├── openvc.py          # OpenVC adapter
│   ├── angelmatch.py      # AngelMatch adapter
│   └── ...
├── stealth/
│   ├── fingerprint.py     # Browser fingerprint rotation
│   ├── behavior.py        # Human-like mouse/scroll simulation
│   └── proxy.py           # Proxy rotation manager
├── enrichment/
│   ├── email_validator.py # MX / SMTP validation
│   ├── linkedin.py        # LinkedIn profile enrichment
│   └── scoring.py         # Lead scoring engine
├── output/
│   ├── csv_writer.py      # CSV export
│   ├── sheets_sync.py     # Google Sheets integration
│   └── airtable.py        # Airtable CRM push
├── data/
│   ├── raw/               # Raw crawl dumps
│   ├── cleaned/           # Post-dedup/validation
│   └── enriched/          # Final enriched leads
└── tests/
    ├── test_adapters.py
    ├── test_stealth.py
    └── test_enrichment.py
```

---

## ⚡ Quick Wins (Start Here)

1. **Refactor `engine.py`** — Extract the scraping logic into a `BaseSiteAdapter` class
2. **Add one real target** — Pick OpenVC or AngelMatch, write a real adapter with working selectors
3. **Better output** — Add columns: Fund Name, Stage, Sector Focus, Check Size, Lead Score
4. **Proxy support** — Even a single rotating proxy dramatically reduces ban risk
5. **Deduplication** — Simple email-based dedup across runs

---

## 🧠 Philosophy

```
Speed is nothing without accuracy.
Accuracy is nothing without context.
Context is nothing without action.

Crawl smart. Enrich deep. Move fast.
```

---

## 📅 Timeline

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | Foundation | Config-driven engine, 2 adapters, working CSV output |
| 2 | Stealth | Proxy rotation, fingerprinting, human-like delays |
| 3 | Enrichment | Email validation, LinkedIn matching, lead scoring |
| 4 | Integration | Google Sheets sync, webhook alerts, scheduling |
| 5+ | Scale | More adapters, dashboard, auto-outreach pipeline |

---

_Built with Playwright, BeautifulSoup, and a hunger to find the right investors before they find you._
