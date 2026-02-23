# LeadFactory API

## Quick Start

### 1. Install dependencies

```bash
cd /Users/davidnichols/Desktop/crawl
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file or export these:

```bash
# Required
export LEADFACTORY_SECRET_KEY="your-secret-key-here"   # JWT signing key

# Optional — defaults to local SQLite if not set
export DATABASE_URL="sqlite+aiosqlite:///./data/leadfactory.db"

# Stripe (test mode keys for billing)
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_PUBLISHABLE_KEY="pk_test_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."

# Outreach providers (optional)
export INSTANTLY_API_KEY="..."
export SMARTLEAD_API_KEY="..."
```

### 3. Start the API server

```bash
uvicorn api.main:app --reload --port 8000
```

Tables auto-create on first startup. API docs at http://localhost:8000/api/docs

### 4. Start the dashboard

```bash
cd dashboard
npm install
npm run dev
```

Dashboard at http://localhost:3000 — proxies `/api` requests to the FastAPI backend.

---

## Key Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/users/register` | No | Create account |
| POST | `/api/users/login` | No | Get JWT token |
| GET | `/api/users/me` | JWT | User profile |
| POST | `/api/campaigns` | JWT | Create campaign |
| GET | `/api/campaigns` | JWT | List campaigns |
| POST | `/api/campaigns/{id}/run` | JWT | Run crawl |
| GET | `/api/leads?campaign_id=X` | JWT | List leads |
| GET | `/api/leads/export?campaign_id=X` | JWT | CSV export |
| GET | `/api/verticals` | JWT | List verticals |
| POST | `/api/billing/checkout` | JWT | Stripe checkout |
| POST | `/api/billing/webhook` | No | Stripe webhook |
| GET | `/api/billing/portal` | JWT | Stripe portal |
| GET | `/api/billing/history` | JWT | Credit history |
| GET | `/api/optout?email=X` | No | Public opt-out |
| GET | `/api/health` | No | Health check |

---

## Importing Leads from a Crawl

After running the crawl engine, import the CSV into the database:

```bash
python -m api.import_leads --campaign-id <UUID> --csv data/enriched/investor_leads_master.csv
```

---

## Running the Crawl Engine

```bash
# Full crawl with deep extraction and SMTP verification
python engine.py --deep --headless --force-recrawl

# Skip SMTP verification (faster)
python engine.py --deep --headless --force-recrawl --skip-smtp

# Crawl specific site only
python engine.py --site openvc --headless

# Dry run (no files written)
python engine.py --deep --headless --dry-run
```

---

## Database

- **Development**: SQLite at `data/leadfactory.db` (auto-created)
- **Production**: Set `DATABASE_URL` to a PostgreSQL connection string

Tables are auto-created on API startup via `Base.metadata.create_all()`. For production, consider using Alembic migrations.

---

## Architecture

```
engine.py (CLI)  ──→  CSV files  ──→  import_leads.py  ──→  Database
                                                               ↑
dashboard (Next.js :3000)  ──→  API (FastAPI :8000)  ──────────┘
```

- The crawl engine is a standalone CLI that outputs CSV
- The API serves the dashboard and reads from the database
- `import_leads.py` bridges the two
- Celery + Redis for async campaign execution (optional — falls back to threading)
