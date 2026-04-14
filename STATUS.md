# Status — What's Real vs. Scaffold

This is an honest assessment of what works and what doesn't yet.

## ✅ Real (tested, working)

| Component | Status | Evidence |
|-----------|--------|----------|
| **SQL schema** (`shared/schema.sql`) | Complete, valid SQL | 10 tables with indexes, RLS stubs, foreign keys |
| **TypeScript domain types** (`apps/web/lib/types.ts`) | Complete, compiles | Mirrors schema; used by all pages |
| **Offer deduplication** (`ingestion/normalize/dedup.py`) | Working, tested | Change detection: new/unchanged/changed with snapshot metadata |
| **Offer scoring** (`ingestion/normalize/scoring.py`) | Working, tested | 5 dimensions; strong offer = 0.92, weak = 0.36 |
| **Crawl state tracking** (`ingestion/normalize/incremental.py`) | Working, tested | Per-domain freshness tracking |
| **Config loading** (`ingestion/utils/config.py`) | Working | YAML config loader |
| **Page extractor** (`ingestion/crawl/page_extractor.py`) | Logic complete, untested on real pages | JSON-LD filtering + regex patterns |
| **Stealth modules** | Working (carried from crawler-26) | Fingerprint rotation, human behavior, proxy |
| **Next.js app** | Builds successfully, 8 routes | Mock data; no live DB |

## 🟡 Scaffold (structure is real, wiring is not)

| Component | What exists | What's missing |
|-----------|------------|----------------|
| **Offer crawler** | Full crawl loop with Playwright + stealth | Not tested on real sites; no sitemap/checkpoint |
| **Discovery** | Multi-engine search with 4 backends | DDG backend works; others need API keys |
| **Source aggregator** | Orchestration pattern | No real offer source URLs yet |
| **Supabase writer** | JSON fallback with dedup-status routing | No live Supabase connection |
| **Frontend pages** | All 8 routes render with mock data | No auth, no real CRUD, no API routes |
| **Admin CRUD** | Table renders mock data | No create/edit/delete actions |

## ❌ Not Started

| Component | Notes |
|-----------|-------|
| Supabase project setup | Schema SQL is ready; needs `supabase init` + `db push` |
| Auth (Supabase Auth) | Login/signup pages exist as forms; no backend wiring |
| Real offer source adapters | Need to identify and build fetchers for actual directories |
| API routes (`apps/web/app/api/`) | Not created; pages use mock data |
| Ingestion → Supabase pipeline | Writer stub exists; needs Supabase client |
| Schema synchronization discipline | SQL is source of truth; TS types derived manually |

## Schema Drift Risk

The domain model currently exists in three places:
1. **`shared/schema.sql`** — canonical source of truth
2. **`apps/web/lib/types.ts`** — TypeScript interfaces (manually synced)
3. **Ingestion pipeline** — raw dicts with implicit field contracts

**Mitigation**: When schema changes, update schema.sql first, then types.ts.
The ingestion pipeline uses plain dicts (not dataclasses) so field names are
the contract — change them in both page_extractor.py and supabase_writer.py.
A future improvement would be to generate types.ts from schema.sql.
