# Ingestion Pipeline

## Overview

The ingestion pipeline discovers, crawls, extracts, and normalizes B2B demo incentive offers. It runs as a standalone Python CLI and writes results to Supabase (or local JSON during development).

## Pipeline Stages

```
┌───────────┐    ┌─────────────┐    ┌───────────┐    ┌──────────┐    ┌────────┐
│ Discovery │ →  │  Aggregator │ →  │   Crawl   │ →  │Normalize │ →  │ Output │
│ (search)  │    │  (sources)  │    │(Playwright)│   │(dedup+   │    │(write) │
│           │    │             │    │           │    │ score)   │    │        │
└───────────┘    └─────────────┘    └───────────┘    └──────────┘    └────────┘
```

### 1. Discovery (`ingestion/discovery/`)
Multi-engine search to find pages likely listing demo incentives.
- Engines: DuckDuckGo (no API key), Google (SerpAPI), Bing, Brave
- Queries: "B2B demo incentive gift card", "get paid to take a software demo", etc.
- Output: Set of base domain URLs

### 2. Source Aggregation (`ingestion/sources/`)
Combines known sources (YAML config) with discovery results.
- Curated seed list in `config/sources.yaml`
- HTTP-based directory fetchers (no browser needed)
- Output: Deduplicated list of URLs to crawl

### 3. Crawl (`ingestion/crawl/`)
Visits pages with Playwright and extracts offer data.
- **OfferCrawler**: Concurrent browser sessions, offer-page detection via URL/link text keywords
- **PageExtractor**: HTML → structured data via JSON-LD parsing and regex pattern matching
- Stealth: Fingerprint rotation, human-like delays, proxy support
- Checkpoint/recovery built into the crawl loop

### 4. Normalize (`ingestion/normalize/`)
- **OfferDeduplicator**: Persistent cross-run dedup using JSON index. Key: `md5(vendor_domain|slugified_title)`. Merges new data into existing records.
- **OfferScorer**: Scores offers 0.0–1.0 based on completeness, reward clarity, source quality, and recency.
- **CrawlStateManager**: Tracks per-domain freshness to avoid unnecessary re-crawls.

### 5. Output (`ingestion/output/`)
Writes to Supabase (when configured) or local JSON files.

## Running

```bash
# Full pipeline
python -m ingestion.main

# Discovery only
python -m ingestion.main --discover-only

# With discovery + crawl
python -m ingestion.main --discover

# Dry run (no writes)
python -m ingestion.main --dry-run

# Custom concurrency
python -m ingestion.main --concurrency 10 --stale-days 14
```

## Configuration

| File | Purpose |
|------|---------|
| `ingestion/config/sources.yaml` | Known offer directories with selectors |
| `ingestion/config/scoring.yaml` | Confidence scoring weights |
| `ingestion/config/proxies.yaml` | Proxy list and rotation strategy |

## Provenance from crawler-26

| New Module | Old Module | Changes |
|------------|------------|---------|
| `discovery/multi_searcher.py` | `discovery/multi_searcher.py` | Queries changed, domain validation adapted |
| `crawl/offer_crawler.py` | `deep_crawl.py` | Looks for offers instead of team pages |
| `crawl/page_extractor.py` | (new) | JSON-LD + regex extraction |
| `normalize/dedup.py` | `enrichment/dedup.py` | Different dedup key, same pattern |
| `normalize/scoring.py` | `enrichment/scoring.py` | Completely different criteria, same structure |
| `normalize/incremental.py` | `enrichment/incremental.py` | Minimal changes, domain-agnostic |
| `sources/aggregator.py` | `sources/aggregator.py` | Same pattern, different sources |
| `sources/base_adapter.py` | `adapters/base.py` | Different data model |
| `stealth/*` | `stealth/*` | Copied as-is |
| `utils/retry.py` | `utils/retry.py` | Copied as-is |
