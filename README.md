# Demo Offers Platform

A marketplace-style directory for B2B demo incentives. Professionals discover, evaluate, and save vendor-sponsored demo offers — gift cards, credits, and perks for taking product demos.

## Quick Start

### Web App (Next.js)

```bash
cd apps/web
npm install
npm run dev          # → http://localhost:3000
```

### Ingestion Pipeline (Python)

```bash
# From the root directory (crawler-26)
cd ingestion
pip install -r requirements.txt
playwright install chromium
cd ..

# Run pipeline
python -m ingestion.main --dry-run
```

## Project Structure

```
apps/web/        → Next.js frontend (landing, directory, dashboard, admin)
ingestion/       → Python ingestion pipeline (discovery, crawl, normalize)
shared/          → SQL schema (source of truth)
docs/            → Architecture and domain documentation
_legacy/         → Archived crawler-26 code (reference only)
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System overview and design decisions
- [Domain Model](docs/DOMAIN_MODEL.md) — Entity definitions and relationships
- [Ingestion Pipeline](docs/INGESTION_PIPELINE.md) — Pipeline stages and configuration

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Database | Supabase (PostgreSQL) |
| Ingestion | Python 3.11+, Playwright, aiohttp |
| Auth | Supabase Auth (planned) |
