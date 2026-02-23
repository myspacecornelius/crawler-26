# Task 5: PostgreSQL Database + API Wiring + Dashboard Connection

## Scope
Replace CSV-file storage with a real PostgreSQL database, wire the FastAPI endpoints to query/write real data, and connect the React dashboard so the full flow works end-to-end: register → login → create campaign → run crawl → see leads in dashboard → export CSV.

## Files to Reference (use @ mentions in Cascade)
When starting this task, tell Cascade:
> Read these files first:
> @api/models.py — SQLAlchemy models (User, Campaign, Lead, CreditTransaction, ApiKey). Already defined, uses PostgreSQL UUID columns
> @api/database.py — async SQLAlchemy engine setup
> @api/schemas.py — Pydantic request/response schemas
> @api/auth.py — JWT auth + password hashing (uses bcrypt directly, NOT passlib)
> @api/main.py — FastAPI app with CORS, lifespan, router mounting
> @api/tasks.py — Celery task definitions for async campaign execution
> @api/routers/users.py — user registration, login, profile endpoints
> @api/routers/campaigns.py — campaign CRUD + run endpoints
> @api/routers/leads.py — lead listing, filtering, export endpoints
> @api/routers/verticals.py — vertical config listing
> @api/routers/outreach.py — outreach campaign management
> @dashboard/lib/api.ts — frontend API client (fetch wrapper with token management)
> @dashboard/next.config.js — proxies /api to localhost:8000
> @dashboard/app/login/page.tsx — login/register UI
> @dashboard/app/dashboard/page.tsx — main dashboard overview
> @dashboard/app/dashboard/campaigns/page.tsx — campaign list
> @dashboard/app/dashboard/campaigns/[id]/page.tsx — campaign detail with leads

## DO NOT MODIFY
- `deep_crawl.py` (handled by Task 4)
- `enrichment/` directory (handled by Tasks 1, 3)
- `output/csv_writer.py` (handled by Task 1)
- `adapters/` directory
- `sources/` directory
- `stealth/` directory

## Current State

### What exists (scaffolded but not functional)
- **SQLAlchemy models** are defined with proper relationships, indexes, and UUID primary keys
- **Database.py** has async engine setup pointing to a PostgreSQL URL from env var `DATABASE_URL`
- **API routers** have endpoint stubs that reference database sessions but may have bugs
- **Dashboard pages** call the API client (`lib/api.ts`) which proxies through Next.js to FastAPI
- **Celery tasks** are defined but untested

### What's missing/broken
1. **No database exists** — no one has run `CREATE TABLE` or migrations. Need Alembic or a `create_all()` bootstrap.
2. **No DATABASE_URL configured** — need to document setup (local PostgreSQL or SQLite fallback for dev)
3. **API routers may have session handling bugs** — they were scaffolded in one pass, never tested against a real database
4. **Dashboard has never been built or run** — `npm install` and `npm run dev` have not been validated
5. **No seed data flow** — after a crawl completes, leads are written to CSV but NOT inserted into the database. Need a bridge: either the engine writes to DB directly, or there's an import script.
6. **CORS may block requests** — the FastAPI CORS config needs to allow `localhost:3000`

## Requirements

### 1. Database bootstrap
- Add a SQLite fallback for local dev: `DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/leadfactory.db")`
- Add a startup event in `api/main.py` lifespan that runs `Base.metadata.create_all()` to auto-create tables
- Ensure models work with both PostgreSQL (production) and SQLite (dev)

### 2. Fix API routers
Test each endpoint manually with `curl`:
- `POST /api/users/register` — create a user
- `POST /api/users/login` — get JWT token
- `GET /api/users/me` — get profile with token
- `POST /api/campaigns` — create campaign
- `GET /api/campaigns` — list campaigns
- `POST /api/campaigns/{id}/run` — trigger crawl
- `GET /api/leads?campaign_id=X` — list leads
- `GET /api/leads/export?campaign_id=X` — CSV export

Fix any bugs found. Common issues will be:
- Async session context managers not properly awaited
- UUID serialization in JSON responses
- Missing error handling for duplicate emails on register

### 3. Lead import bridge
Create `api/import_leads.py` — a script that reads `data/enriched/investor_leads_master.csv` and inserts leads into the database for a given campaign:
```
python -m api.import_leads --campaign-id <UUID> --csv data/enriched/investor_leads_master.csv
```
This bridges the crawl engine (CSV output) with the API (database reads).

### 4. Dashboard validation
- Run `cd dashboard && npm install && npm run dev`
- Fix any build errors
- Verify login → dashboard → campaigns → leads flow works
- Ensure the API proxy in `next.config.js` correctly routes to `http://127.0.0.1:8000`

### 5. Environment setup documentation
Create `api/README.md` with:
- How to start the API: `uvicorn api.main:app --reload`
- How to start the dashboard: `cd dashboard && npm run dev`
- Environment variables needed: `DATABASE_URL`, `LEADFACTORY_SECRET_KEY`
- How to import leads from a crawl run

## Acceptance Criteria
- [ ] `uvicorn api.main:app --reload` starts without errors
- [ ] Database tables auto-create on first startup
- [ ] Full curl test: register → login → create campaign → import leads → list leads → export CSV
- [ ] Dashboard builds and runs: `cd dashboard && npm run dev` shows login page at localhost:3000
- [ ] Login with registered user → see dashboard with real lead counts
- [ ] Campaign detail page shows leads from database (not hardcoded)
- [ ] All 167 existing tests still pass: `venv/bin/python -m pytest tests/ -x -q`

## Data Contracts
- **Database**: PostgreSQL (prod) or SQLite (dev), schema defined by `api/models.py`
- **API**: JSON REST endpoints documented in router files
- **Dashboard → API**: Fetch calls via `lib/api.ts`, proxied through Next.js rewrites
- **CSV → DB bridge**: `api/import_leads.py` reads CSV, inserts into `leads` table

## Architecture Notes
- The crawl engine (`engine.py`) remains a CLI tool that outputs CSV
- The API serves the dashboard and reads from the database
- The bridge script (`import_leads.py`) connects the two
- Future: the Celery task in `api/tasks.py` should invoke the engine and auto-import results, but that's out of scope for this task
