# LeadFactory — VC Lead Generation & Outreach Platform

A full-stack system that discovers investor contacts across VC/PE fund websites, enriches them through a multi-layer email discovery pipeline, scores and deduplicates leads, and delivers them through a Next.js dashboard with campaign management, outreach integrations, and CRM push. Includes a public-facing marketing site ("Honeypot") for founder acquisition.

---

## Project Tree

```
crawl/
├── engine.py                          # Main pipeline orchestrator
├── deep_crawl.py                      # Playwright-based fund website crawler
├── enrich_checkpoint.py               # Checkpoint-based enrichment runner
├── requirements.txt                   # Python dependencies
├── gameplan.md                        # Strategic planning notes
│
├── adapters/                          # VC directory adapters
│   ├── base.py                        #   InvestorLead data model
│   ├── angelmatch.py                  #   AngelMatch scraper
│   ├── crunchbase.py                  #   Crunchbase adapter
│   ├── landscape_vc.py                #   Landscape VC adapter
│   ├── openvc.py                      #   OpenVC API adapter
│   ├── signal_nfx.py                  #   Signal NFX adapter
│   ├── visible_vc.py                  #   Visible VC adapter
│   └── wellfound.py                   #   Wellfound (AngelList) adapter
│
├── api/                               # FastAPI backend
│   ├── main.py                        #   App entry point + middleware
│   ├── auth.py                        #   JWT authentication
│   ├── billing.py                     #   Stripe billing logic
│   ├── database.py                    #   SQLAlchemy async engine
│   ├── models.py                      #   ORM models
│   ├── schemas.py                     #   Pydantic request/response schemas
│   ├── tasks.py                       #   Background task runner
│   ├── import_leads.py                #   CSV-to-database importer
│   └── routers/
│       ├── billing.py                 #   Checkout, portal, plans
│       ├── campaigns.py               #   Campaign CRUD + execution
│       ├── crm.py                     #   HubSpot/Salesforce push
│       ├── leads.py                   #   Lead list, filter, export
│       ├── outreach.py                #   Instantly/SmartLead launch
│       ├── portfolio.py               #   Portfolio company explorer
│       ├── users.py                   #   Register, login, profile
│       └── verticals.py              #   Vertical definitions
│
├── config/                            # YAML configuration
│   ├── proxies.yaml                   #   Proxy rotation pool
│   ├── scoring.yaml                   #   Lead scoring weights
│   ├── search.yaml                    #   Discovery search queries
│   └── sites.yaml                     #   Per-site crawl rules
│
├── dashboard/                         # Next.js 14 analytics dashboard
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   ├── page.tsx                   #   Landing/login redirect
│   │   ├── login/
│   │   ├── privacy/
│   │   ├── terms/
│   │   └── dashboard/
│   │       ├── layout.tsx             #   Sidebar + breadcrumb shell
│   │       ├── page.tsx               #   Overview stats + charts
│   │       ├── campaigns/
│   │       │   ├── page.tsx           #   Campaign list
│   │       │   ├── new/page.tsx       #   3-step creation wizard
│   │       │   └── [id]/page.tsx      #   Campaign detail + leads
│   │       ├── crm/page.tsx           #   CRM integration page
│   │       ├── outreach/
│   │       │   ├── page.tsx           #   Outreach hub
│   │       │   └── [id]/page.tsx      #   Outreach campaign detail
│   │       ├── portfolio/page.tsx     #   Portfolio intelligence
│   │       ├── settings/page.tsx      #   Account + billing
│   │       └── verticals/page.tsx     #   Vertical browser
│   ├── components/
│   │   ├── ActivityFeed.tsx
│   │   ├── CampaignWizard.tsx
│   │   ├── EmptyState.tsx
│   │   ├── LeadTable.tsx
│   │   ├── QuickActions.tsx
│   │   ├── Sidebar.tsx
│   │   ├── StatsCard.tsx
│   │   ├── DataTable/               #   Generic data table system
│   │   │   ├── DataTable.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   ├── BulkActions.tsx
│   │   │   ├── ColumnToggle.tsx
│   │   │   ├── ExportButton.tsx
│   │   │   └── TableSkeleton.tsx
│   │   ├── campaign/
│   │   │   ├── CampaignStatsPanel.tsx
│   │   │   └── LeadScoreDistribution.tsx
│   │   ├── charts/
│   │   │   ├── EmailStatusDonut.tsx
│   │   │   ├── FundCoverageBar.tsx
│   │   │   ├── LeadsOverTimeChart.tsx
│   │   │   └── MiniSparkline.tsx
│   │   ├── crm/
│   │   │   ├── CRMProviderSetup.tsx
│   │   │   ├── CRMPushForm.tsx
│   │   │   └── CRMPushHistory.tsx
│   │   ├── layout/
│   │   │   ├── AppSidebar.tsx
│   │   │   ├── Breadcrumbs.tsx
│   │   │   ├── CommandPalette.tsx
│   │   │   ├── MobileNav.tsx
│   │   │   ├── NotificationBell.tsx
│   │   │   └── UserMenu.tsx
│   │   ├── outreach/
│   │   │   ├── OutreachStatsChart.tsx
│   │   │   └── ProviderCard.tsx
│   │   └── ui/                       #   Shared primitives
│   │       ├── Badge.tsx
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Dialog.tsx
│   │       ├── Input.tsx
│   │       ├── Select.tsx
│   │       ├── Skeleton.tsx
│   │       ├── Toast.tsx
│   │       └── Tooltip.tsx
│   ├── contexts/
│   │   └── SidebarContext.tsx
│   └── lib/
│       ├── api.ts                     #   Typed API client
│       └── cn.ts                      #   clsx + tailwind-merge util
│
├── data/
│   ├── target_funds.txt               #   Fund URLs for deep crawl
│   ├── seen_domains.txt               #   Domain dedup tracking
│   ├── dedup_index.json               #   Cross-run dedup state
│   ├── leadfactory.db                 #   SQLite fallback DB
│   ├── vc_contacts.csv                #   Raw extraction output
│   ├── vc_contacts_checkpoint.csv     #   Mid-pipeline checkpoint
│   ├── seed/
│   │   ├── vc_firms.csv               #   Core VC seed list
│   │   ├── vc_firms_expanded.csv      #   Extended VC list
│   │   ├── vc_firms_supplemental.csv  #   Supplemental entries
│   │   ├── pe_firms.csv               #   Private equity firms
│   │   ├── family_offices.csv         #   Family office contacts
│   │   └── corp_dev.csv               #   Corporate dev teams
│   ├── enriched/
│   │   ├── investor_leads_master.csv  #   Merged master (~12,500 leads)
│   │   ├── leads_YYYYMMDD_*.csv       #   Per-run timestamped exports
│   │   ├── checkpoint_dedup.csv       #   Post-dedup snapshot
│   │   ├── checkpoint_guesser.csv     #   Post-guesser snapshot
│   │   └── checkpoint_validation.csv  #   Post-validation snapshot
│   ├── raw/                           #   Unprocessed scrape data
│   └── screenshots/                   #   Debug screenshots (67 files)
│
├── discovery/                         # Search-engine lead discovery
│   ├── multi_searcher.py              #   Multi-engine search (Google, Bing, DuckDuckGo)
│   ├── searcher.py                    #   Single-engine search wrapper
│   └── aggregator.py                  #   Discovery result aggregation
│
├── enrichment/                        # Email discovery & validation
│   ├── email_guesser.py               #   Pattern-based email generation (8 patterns)
│   ├── email_validator.py             #   Format + MX + SMTP verification
│   ├── email_waterfall.py             #   Multi-provider fallback (Hunter/ZeroBounce/MV)
│   ├── scoring.py                     #   Weighted lead scoring + tier assignment
│   ├── dedup.py                       #   Cross-run deduplication engine
│   ├── incremental.py                 #   Crawl freshness + state tracking
│   ├── dns_harvester.py               #   DMARC/SOA/TXT email extraction
│   ├── google_dorker.py               #   Google dorking for leaked emails
│   ├── github_miner.py                #   Git commit author email discovery
│   ├── gravatar_oracle.py             #   Avatar-based email confirmation
│   ├── pgp_keyserver.py               #   PGP public key email lookup
│   ├── sec_edgar.py                   #   SEC filing email extraction
│   ├── wayback_enricher.py            #   Internet Archive email recovery
│   ├── catchall_detector.py           #   Catch-all detection + JS DOM scraping
│   ├── portfolio_scraper.py           #   Fund portfolio company extraction
│   ├── linkedin_enricher.py           #   LinkedIn profile enrichment
│   ├── fund_intelligence.py           #   Fund metadata extraction
│   └── pdf_parser.py                  #   PDF document email extraction
│
├── integrations/                      # CRM connectors
│   ├── crm_base.py                    #   Abstract CRM interface
│   ├── hubspot.py                     #   HubSpot push
│   ├── salesforce.py                  #   Salesforce push
│   └── manager.py                     #   CRM provider manager
│
├── landing/                           # Honeypot marketing site
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── app/
│   │   ├── globals.css                #   Theme + print styles
│   │   ├── layout.tsx
│   │   └── page.tsx                   #   Full landing page (~900 lines)
│   └── scripts/
│       └── export-pdf.ts              #   Playwright PDF export
│
├── outreach/                          # Email campaign integrations
│   ├── base.py                        #   Abstract outreach interface
│   ├── instantly.py                   #   Instantly.ai integration
│   ├── smartlead.py                   #   SmartLead integration
│   ├── manager.py                     #   Provider manager
│   └── templates.py                   #   Email template engine
│
├── output/                            # Data export
│   ├── csv_writer.py                  #   Master CSV writer + checkpoints
│   └── webhook.py                     #   Discord/Slack notifications
│
├── scripts/
│   └── expand_seed.py                 #   Seed database expansion utility
│
├── sources/                           # Deterministic lead sources
│   ├── aggregator.py                  #   Combines seed + GitHub + directories
│   ├── directory_fetchers.py          #   HTTP-based VC directory scrapers
│   ├── github_lists.py                #   GitHub public VC list fetcher
│   ├── http_discovery.py              #   HTTP-based domain discovery
│   └── seed_db.py                     #   Curated seed database loader
│
├── stealth/                           # Anti-detection layer
│   ├── behavior.py                    #   Human-like browsing patterns
│   ├── fingerprint.py                 #   Browser fingerprint rotation
│   └── proxy.py                       #   Proxy pool management
│
├── tests/                             # Test suite
│   ├── test_crm.py
│   ├── test_dedup.py
│   ├── test_email_discovery.py
│   ├── test_email_waterfall.py
│   ├── test_engine_integration.py
│   ├── test_extraction_coverage.py
│   ├── test_fixes.py
│   ├── test_incremental.py
│   ├── test_multi_searcher.py
│   ├── test_portfolio.py
│   ├── test_scale.py
│   ├── test_smtp_fix.py
│   ├── test_v2.py
│   └── test_v3.py
│
├── verticals/                         # Investor vertical definitions
│   ├── loader.py                      #   YAML vertical loader
│   ├── vc.yaml                        #   VC firm targeting rules
│   ├── pe.yaml                        #   PE firm targeting rules
│   ├── family_office.yaml             #   Family office rules
│   └── corp_dev.yaml                  #   Corp dev rules
│
├── .github/workflows/
│   └── pylint.yml                     # CI linting
└── .vscode/
    ├── extensions.json
    └── settings.json
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  LEAD DISCOVERY                                                   │
│  sources/aggregator.py  →  seed DB + GitHub lists + directories  │
│  discovery/multi_searcher.py  →  Google, Bing, DuckDuckGo        │
│  deep_crawl.py  →  Playwright team page extraction               │
└───────────────────────────┬──────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│  EMAIL ENRICHMENT  (enrichment/)                                  │
│  dns_harvester → google_dorker → gravatar_oracle → pgp_keyserver │
│  → github_miner → sec_edgar → wayback_enricher → catchall       │
│  → email_guesser (8 patterns) → email_validator (SMTP)           │
│  → email_waterfall (Hunter / ZeroBounce / MillionVerifier)       │
└───────────────────────────┬──────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│  SCORING & OUTPUT                                                 │
│  scoring.py  →  weighted rank (stage, sector, check size)        │
│  dedup.py    →  cross-run merge with email quality hierarchy     │
│  csv_writer  →  master CSV + timestamped exports + checkpoints   │
└───────────────────────────┬──────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────┐
│  PLATFORM                                                         │
│  API (FastAPI)  →  campaigns, leads, outreach, CRM, billing     │
│  Dashboard (Next.js 14)  →  stats, charts, tables, wizards      │
│  Outreach  →  Instantly.ai / SmartLead email campaigns           │
│  CRM  →  HubSpot / Salesforce contact push                      │
│  Landing  →  Honeypot marketing site (Next.js)                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Python setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Run the crawl pipeline
python engine.py --deep --headless --force-recrawl

# Run tests
python -m pytest tests/ -x -q

# Start API server
LEADFACTORY_SECRET_KEY=dev-secret uvicorn api.main:app --reload

# Dashboard
cd dashboard && npm install && npm run dev    # localhost:3000

# Landing page
cd landing && npm install && npm run dev      # localhost:3001

# Export landing page as PDF
cd landing && npx tsx scripts/export-pdf.ts
```

---

## Dashboard Pages

| Route | Description |
|-------|-------------|
| `/dashboard` | Overview — lead volume, email quality charts, activity feed |
| `/dashboard/campaigns` | Campaign list with status filters |
| `/dashboard/campaigns/new` | 3-step creation wizard with targeting |
| `/dashboard/campaigns/[id]` | Campaign detail — stats, score distribution, leads table |
| `/dashboard/outreach` | Outreach hub — Instantly / SmartLead launch + monitoring |
| `/dashboard/outreach/[id]` | Outreach campaign stats |
| `/dashboard/crm` | CRM push (HubSpot / Salesforce) |
| `/dashboard/portfolio` | Portfolio intelligence explorer |
| `/dashboard/verticals` | Vertical browser |
| `/dashboard/settings` | Account, credits, billing (Stripe) |

---

## API Endpoints

| Prefix | Key endpoints |
|--------|---------------|
| `/campaigns` | CRUD, run campaign, stats |
| `/leads` | List, filter, export CSV, freshness |
| `/outreach` | Launch, start, pause, templates |
| `/crm` | Push contacts, field mapping |
| `/funds/{fund}/portfolio` | Portfolio companies with filters |
| `/billing` | Stripe checkout, portal, plans |
| `/users` | Register, login, profile |
| `/verticals` | List, detail |

---

## Key Files for AI Briefing

If you need to give another AI the best possible understanding of this codebase from a limited set of files, provide the tree above plus these files in priority order:

### Tier 1 — System Architecture (read these first)

| File | Why |
|------|-----|
| `engine.py` | The brain. Orchestrates the entire pipeline — discovery, crawl, enrichment, scoring, output. Reading this reveals how every module connects. |
| `adapters/base.py` | Defines `InvestorLead`, the core data model that flows through every stage of the pipeline. |
| `api/main.py` | FastAPI app setup — shows all mounted routers, middleware, and how the API layer is structured. |
| `api/models.py` | ORM models — the database schema that underpins campaigns, leads, users, and billing. |

### Tier 2 — Pipeline Internals

| File | Why |
|------|-----|
| `sources/aggregator.py` | How leads enter the system — seed DB + GitHub + directory fetchers, domain-level dedup. |
| `deep_crawl.py` | Playwright-based fund website crawler — team page detection, JS rendering, contact extraction. |
| `enrichment/email_guesser.py` | Pattern-based email generation — the 8 patterns, MX validation, learned pattern matching. |
| `enrichment/email_validator.py` | Multi-layer email verification — format, MX, disposable, SMTP RCPT TO, catch-all detection. |
| `enrichment/scoring.py` | Lead ranking — weighted scoring dimensions, tier assignment (HOT/WARM/COOL/COLD). |
| `enrichment/dedup.py` | Cross-run deduplication — persistent index, email quality hierarchy, merge-not-replace logic. |
| `config/scoring.yaml` | Scoring weight configuration — reveals what the system values in a lead. |
| `config/sites.yaml` | Per-site crawl rules — selectors, pagination, rate limits for each fund directory. |

### Tier 3 — Frontend & Integration

| File | Why |
|------|-----|
| `dashboard/app/dashboard/page.tsx` | Main dashboard — shows what data the platform surfaces and how. |
| `dashboard/lib/api.ts` | Typed API client — every endpoint the frontend calls, typed request/response. |
| `dashboard/components/LeadTable.tsx` | Core data display — filtering, sorting, email status badges, export. |
| `landing/app/page.tsx` | Marketing site — product positioning, feature list, pricing (useful for understanding the product). |
| `outreach/manager.py` | Outreach provider abstraction — how campaigns get pushed to Instantly/SmartLead. |
| `integrations/manager.py` | CRM provider abstraction — how leads get pushed to HubSpot/Salesforce. |

### Tier 4 — Enrichment Modules (read if deep-diving email discovery)

| File | Why |
|------|-----|
| `enrichment/dns_harvester.py` | Zero-cost DMARC/SOA email extraction |
| `enrichment/google_dorker.py` | Google dorking for leaked emails on third-party sites |
| `enrichment/github_miner.py` | Git commit author email discovery |
| `enrichment/sec_edgar.py` | SEC filing email extraction |
| `enrichment/email_waterfall.py` | Multi-provider verification fallback chain |
| `enrichment/catchall_detector.py` | Catch-all detection + Playwright JS DOM scraping |

### Minimum Viable Briefing

For the fastest possible onboarding, provide just these 4 files plus the tree:
1. **`engine.py`** — full pipeline flow
2. **`adapters/base.py`** — data model
3. **`api/main.py`** — API structure
4. **`dashboard/app/dashboard/page.tsx`** — what the user sees
