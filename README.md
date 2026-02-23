# LeadFactory — Multi-Vertical Lead Generation Platform

A full-stack lead generation platform that crawls VC/PE fund websites, extracts investment team members, enriches contacts with email discovery & SMTP verification, scores leads, and delivers them through a modern dashboard with outreach and CRM integrations.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard (Next.js 14)                                     │
│  /dashboard  /campaigns  /outreach  /verticals  /settings   │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│  API Server (FastAPI)                                        │
│  /campaigns  /leads  /outreach  /crm  /portfolio  /billing   │
└──────────────────────────┬──────────────────────────────────┘
                           │ PostgreSQL
┌──────────────────────────▼──────────────────────────────────┐
│  Crawl & Enrichment Pipeline                                 │
│  engine.py → deep_crawl.py → email_guesser → email_validator │
└─────────────────────────────────────────────────────────────┘
```

### Key directories

| Directory | Purpose |
|-----------|---------|
| `api/` | FastAPI backend — routers, models, schemas, auth, billing |
| `dashboard/` | Next.js 14 frontend — pages, components, API client |
| `enrichment/` | Email guesser, SMTP validator, scoring |
| `adapters/` | Data model (`InvestorLead`) and fund adapters |
| `output/` | CSV writer |
| `config/` | Scoring weights, vertical configs |
| `integrations/` | CRM push (HubSpot, Salesforce) |
| `outreach/` | Email outreach (Instantly, SmartLead) |
| `data/` | Seed databases, target lists, crawl output |
| `tests/` | Pytest suite (321 tests) |
| `.windsurf/tasks/` | Sub-agent task briefs (see below) |

---

## Quick Start

```bash
# Backend
venv/bin/python -m pytest tests/ -x -q          # Run tests (321 passing)
LEADFACTORY_SECRET_KEY=dev-secret uvicorn api.main:app --reload  # Start API

# Frontend
cd dashboard && npm install && npm run dev       # Start dashboard at localhost:3000
cd dashboard && npm run build                    # Verify production build

# Crawl pipeline
venv/bin/python engine.py --deep --headless --force-recrawl     # Full crawl
venv/bin/python deep_crawl.py --targets data/test_targets.txt --limit 5 --headless  # Test crawl

# Data quality check
wc -l data/enriched/investor_leads_master.csv
awk -F',' 'NR>1 && $1==$4' data/enriched/investor_leads_master.csv | wc -l  # fund-level rows
```

---

## Task Orchestration Guide

Each `.md` file in `.windsurf/tasks/` is a **self-contained brief** for a sub-agent (a fresh Cascade conversation).

### Task Index

| # | File | Description | Status |
|---|------|-------------|--------|
| 01 | `01-scoring-csv-fix.md` | Fix CSV column alignment, add role-weighted scoring | ✅ Done |
| 02 | `02-data-cleaning.md` | Filter fund-level rows, fix garbled roles | ✅ Done |
| 03 | `03-email-verification.md` | Wire SMTP RCPT TO into pipeline, add Email Status column | ✅ Done |
| 04 | `04-deep-crawl-coverage.md` | Improve per-fund extraction (pagination, JS rendering) | ✅ Done |
| 05 | `05-postgres-api-dashboard.md` | PostgreSQL DB, wire API to real data, connect dashboard | ✅ Done |
| 06 | `06-stripe-billing-compliance.md` | Stripe billing, legal compliance, opt-out | ✅ Done |
| 07 | `07-extraction-coverage.md` | Expand team member extraction heuristics in `deep_crawl.py` | ✅ Done |
| 08 | `08-email-guess-verify.md` | SMTP pattern discovery, concurrency, email guesser improvements | ✅ Done |
| 09 | `09-smtp-verification-fix.md` | SMTP self-test, port fallback, HELO config, graceful degradation | ✅ Done |
| 10 | `10-email-status-freshness.md` | Email status badges + freshness panel in LeadTable | ✅ Done |
| 11 | `11-campaign-wizard-enhance.md` | Multi-step campaign creation wizard with targeting | ✅ Done |
| 12 | `12-outreach-integration-page.md` | Outreach page (Instantly / SmartLead) | ✅ Done |
| 13 | `13-crm-integration-page.md` | CRM integration page (HubSpot / Salesforce) | ⏳ Pending |
| 14 | `14-portfolio-intelligence-page.md` | Portfolio intelligence explorer | ⏳ Pending |

### Dependency Graph

```
Track A — Data Pipeline (completed)
  Task 01 (Scoring/CSV) ─┐
                          ├→ Task 03 (Email Verify) → Task 04 (Deep Crawl)
  Task 02 (Cleaning) ────┘
                          ↓
  Task 07 (Extraction) → Task 08 (Email Guesser) → Task 09 (SMTP Fix)

Track B — Platform (completed through Task 12)
  Task 05 (Postgres/API) → Task 06 (Stripe/Compliance)
                          ↓
  Task 10 (Email Status UI) ─┐
  Task 11 (Campaign Wizard) ─┤─→ all independent, no file conflicts
  Task 12 (Outreach Page) ───┘
                          ↓
  Task 13 (CRM Page) ────────→ touches Sidebar.tsx, api.ts (sequential)
  Task 14 (Portfolio Page) ──→ touches Sidebar.tsx, api.ts (sequential)
```

### Launching a Sub-Agent

1. **Open a new Cascade conversation** (fresh context)
2. **Paste this template:**
   ```
   I'm working on a lead generation platform. I need you to complete a specific task.
   Here is the task brief:

   [PASTE THE FULL CONTENTS OF THE TASK .md FILE HERE]

   Before making any changes, read all the files listed in the brief.
   Then propose your approach and wait for my approval before editing.
   ```
3. **Use `@` mentions** for file references (relative to workspace root):
   - `@deep_crawl.py` → `/Users/davidnichols/Desktop/crawl/deep_crawl.py`
   - `@api/models.py` → `/Users/davidnichols/Desktop/crawl/api/models.py`
   - `@dashboard/components/LeadTable.tsx` → etc.
4. **Verify acceptance criteria** after completion (listed in each brief)

### After Each Task: Integration Check

```bash
# Backend tests
venv/bin/python -m pytest tests/ -x -q

# Frontend build
cd dashboard && npm run build

# Quick data quality check (pipeline tasks)
venv/bin/python engine.py --deep --headless --force-recrawl 2>&1 | tail -30
```

---

## File Ownership Map

| File | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 | 12 | 13 | 14 |
|------|----|----|----|----|----|----|----|----|----|----|----|----|----|----|
| `enrichment/scoring.py` | ✏️ | | | | | | | | | | | | | |
| `output/csv_writer.py` | ✏️ | | ✏️ | | | | | | | | | | | |
| `config/scoring.yaml` | ✏️ | | | | | | | | | | | | | |
| `adapters/base.py` | ✏️ | | ✏️ | | | | | | | | | | | |
| `engine.py` | | ✏️ | ✏️ | | | | | | | | | | | |
| `deep_crawl.py` | | ✏️ | | ✏️ | | | ✏️ | | | | | | | |
| `enrichment/email_guesser.py` | | ✏️ | | | | | | ✏️ | | | | | | |
| `enrichment/email_validator.py` | | | ✏️ | | | | | | ✏️ | | | | | |
| `api/models.py` | | | | | ✏️ | ✏️ | | | | | | | | |
| `api/schemas.py` | | | | | ✏️ | ✏️ | | | | ✏️ | | | | |
| `api/routers/leads.py` | | | | | ✏️ | | | | | ✏️ | | | | |
| `api/routers/crm.py` | | | | | ✏️ | | | | | | | | ✏️ | |
| `api/routers/outreach.py` | | | | | ✏️ | | | | | | | ✏️ | | |
| `api/routers/portfolio.py` | | | | | ✏️ | | | | | | | | | ✏️ |
| `api/main.py` | | | | | ✏️ | ✏️ | | | | | | | | |
| `dashboard/components/LeadTable.tsx` | | | | | ✏️ | | | | | ✏️ | | | | |
| `dashboard/components/Sidebar.tsx` | | | | | ✏️ | | | | | | | ✏️ | ✏️ | ✏️ |
| `dashboard/components/CampaignWizard.tsx` | | | | | | | | | | | ✏️ | | | |
| `dashboard/lib/api.ts` | | | | | ✏️ | | | | | ✏️ | ✏️ | ✏️ | ✏️ | ✏️ |
| `dashboard/app/dashboard/campaigns/new/` | | | | | ✏️ | | | | | | ✏️ | | | |
| `dashboard/app/dashboard/campaigns/[id]/` | | | | | ✏️ | | | | | ✏️ | | | | |
| `dashboard/app/dashboard/outreach/` | | | | | | | | | | | | ✏️ | | |
| `dashboard/app/dashboard/crm/` | | | | | | | | | | | | | ✏️ | |
| `dashboard/app/dashboard/portfolio/` | | | | | | | | | | | | | | ✏️ |

---

## Dashboard Pages

| Route | Description | Status |
|-------|-------------|--------|
| `/dashboard` | Overview — campaigns, credits, stats | ✅ Live |
| `/dashboard/campaigns` | Campaign list — run, delete, view | ✅ Live |
| `/dashboard/campaigns/new` | 3-step campaign wizard with targeting | ✅ Live |
| `/dashboard/campaigns/[id]` | Campaign detail — stats, freshness, leads table | ✅ Live |
| `/dashboard/outreach` | Outreach hub — launch, monitor via Instantly/SmartLead | ✅ Live |
| `/dashboard/outreach/[id]` | Outreach campaign stats detail | ✅ Live |
| `/dashboard/verticals` | Vertical browser | ✅ Live |
| `/dashboard/settings` | Account, credits, billing | ✅ Live |
| `/dashboard/crm` | CRM push (HubSpot/Salesforce) | ⏳ Brief 13 |
| `/dashboard/portfolio` | Portfolio intelligence explorer | ⏳ Brief 14 |

## API Endpoints

| Prefix | Router | Key endpoints |
|--------|--------|---------------|
| `/campaigns` | `campaigns.py` | CRUD, run campaign |
| `/leads` | `leads.py` | List, filter, stats, freshness, export CSV |
| `/outreach` | `outreach.py` | Launch, start, pause, stats, templates |
| `/crm` | `crm.py` | Push, status, fields, field-mapping defaults |
| `/funds/{fund}/portfolio` | `portfolio.py` | Portfolio companies with filters |
| `/billing` | `billing.py` | Checkout, portal, history, plans |
| `/users` | `users.py` | Register, login, profile, credits |
| `/verticals` | `verticals.py` | List, detail |
