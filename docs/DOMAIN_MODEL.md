# Domain Model

## Entity Relationships

```
┌──────────┐       ┌──────────┐       ┌─────────────────┐
│  Vendor  │ 1───N │  Offer   │ 1───N │ OfferRequirement│
└──────────┘       └────┬─────┘       └─────────────────┘
                        │ 1
                        ├───N ┌──────────┐
                        │     │  Reward  │
                        │     └──────────┘
                        │ 1
                        ├───N ┌───────────────┐
                        │     │ OfferSnapshot  │
                        │     └───────────────┘
                        │ N
                        ├───1 ┌──────────────┐
                        │     │ SavedOffer   │
                        │     └──────┬───────┘
                        │            │ N
                   ┌────┴────┐  ┌────┴────┐
                   │AdminNote│  │  User   │
                   └─────────┘  └─────────┘
```

## Entities

### Vendor
The software company offering a demo incentive. Identified by domain.
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| name | text | Company name |
| slug | text | URL-safe identifier |
| website | text | Company website |
| domain | text | Canonical domain (unique) |
| logo_url | text | Logo image URL |
| category | text | Industry category |
| description | text | Short vendor description |

### Offer
A specific demo incentive from a vendor.
| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| vendor_id | UUID | FK → vendors |
| title | text | Offer headline |
| slug | text | URL-safe identifier |
| description | text | Full description |
| category | text | Offer category |
| reward_type | enum | gift_card, cash, credit, discount, swag, other |
| reward_value | text | Human-readable: "$50 Amazon Gift Card" |
| cta_url | text | Link to claim the offer |
| status | enum | draft, active, expired, paused, archived |
| region | text | Geographic availability |
| confidence_score | float | 0.0–1.0, set by scoring pipeline |
| last_verified_at | timestamp | When offer was last confirmed active |
| expires_at | timestamp | Optional expiration |

### OfferRequirement
Steps a user must complete to qualify for an offer.

### Reward
The specific reward(s) associated with an offer. An offer may have multiple rewards.

### OfferSnapshot
Raw crawl data from the ingestion pipeline. Preserves historical state.

### OfferSource
A known directory or data source that the pipeline crawls.

### User
Platform user. Role is either `user` or `admin`.

### SavedOffer
Join table: user saves an offer for later (with optional notes).

### AdminNote
Internal admin notes on an offer (editorial/QA).

### CrawlState
Per-domain freshness tracking for the ingestion pipeline.

## Mapping from crawler-26

| Old Concept | New Concept | Notes |
|-------------|-------------|-------|
| InvestorLead | Offer | Primary entity |
| fund / fund_name | Vendor | Organization |
| LeadScorer | OfferScorer | Different criteria |
| LeadDeduplicator | OfferDeduplicator | Different key |
| Campaign | (removed) | Not needed for MVP |
| Lead.email | (removed) | No contact discovery |
| Lead.lead_score | Offer.confidence_score | Quality signal |
