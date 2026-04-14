# Architecture

## Overview

The Demo Offers Platform is a monorepo with two independent services:

```
┌──────────────────────────────────────────────────────┐
│  apps/web/            Next.js App (port 3000)        │
│  ┌───────┐  ┌──────────┐  ┌──────────┐              │
│  │Landing│  │ Directory │  │Dashboard │              │
│  │ Page  │  │(offers/) │  │(saved)   │              │
│  └───┬───┘  └────┬─────┘  └────┬─────┘              │
│      └───────────┼──────────────┘                    │
│             Supabase Client                          │
└──────────────┬───────────────────────────────────────┘
               │
   ┌───────────▼───────────────────────┐
   │  Supabase (PostgreSQL + Auth)     │
   │  shared/schema.sql                │
   └───────────▲───────────────────────┘
               │
┌──────────────┴───────────────────────────────────────┐
│  ingestion/            Python Pipeline (CLI)         │
│  ┌─────────┐  ┌─────┐  ┌─────────┐  ┌──────┐       │
│  │Discovery│→ │Crawl│→ │Normalize│→ │Output│       │
│  └─────────┘  └─────┘  └─────────┘  └──────┘       │
└──────────────────────────────────────────────────────┘
```

## Service Boundaries

### Web Application (`apps/web/`)
- **Runtime**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Responsibilities**: User-facing pages, auth, saved offers, admin CRUD
- **Data access**: Supabase client SDK (deferred until project is provisioned)
- **State**: Server components by default; client components only for interactivity

### Ingestion Pipeline (`ingestion/`)
- **Runtime**: Python 3.11+, async (aiohttp, Playwright)
- **Responsibilities**: Discover offer sources → crawl pages → extract offers → normalize → write to DB
- **Execution**: CLI (`python -m ingestion.main`), designed for cron or manual runs
- **Stealth**: Fingerprint rotation, human behavior simulation, proxy support

### Shared Schema (`shared/schema.sql`)
- Source of truth for the data model
- Applied to Supabase via dashboard or `supabase db push`
- TypeScript types in `apps/web/lib/types.ts` mirror this schema

## Key Design Decisions

1. **Monorepo**: Both services live in one repo for simplicity. No shared build tooling — each service has its own dependency management.
2. **Schema-first**: SQL schema is the source of truth. TypeScript types derived from it manually (codegen can come later).
3. **Mock data for development**: `apps/web/lib/supabase.ts` exports mock data so the frontend works without a live database.
4. **Stealth preserved as-is**: The fingerprint/behavior/proxy modules from crawler-26 are domain-agnostic and copied directly.
5. **No overengineering**: No GraphQL, no tRPC, no ORM on the frontend, no microservices. Simple SQL + direct Supabase calls.
