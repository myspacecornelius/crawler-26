# Task 6: Stripe Billing & Legal Compliance

## Scope
Integrate Stripe for credit-pack purchases and subscription billing. Add basic legal compliance pages (Terms of Service, Privacy Policy, GDPR opt-out endpoint). This task depends on Task 5 (PostgreSQL + working API) being complete first.

## Files to Reference (use @ mentions in Cascade)
When starting this task, tell Cascade:
> Read these files first:
> @api/models.py — CreditTransaction model (lines 123-137), User model with `plan`, `credits_remaining`, `credits_monthly` fields (lines 19-36)
> @api/routers/users.py — user profile and credit-related endpoints
> @api/schemas.py — Pydantic schemas for request/response
> @api/main.py — FastAPI app setup, router mounting
> @dashboard/app/dashboard/settings/page.tsx — settings page with billing UI (plan cards, credit bar, account info)
> @dashboard/lib/api.ts — frontend API client

## DO NOT MODIFY
- `deep_crawl.py`
- `engine.py`
- `enrichment/` directory
- `output/` directory
- `adapters/` directory
- `sources/` directory

## Prerequisites
- Task 5 must be complete (PostgreSQL running, API functional, dashboard connected)
- A Stripe test-mode account (user will provide `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY`)

## Current State
- The User model has `plan` (starter/pro/scale/enterprise), `credits_remaining`, and `credits_monthly` fields
- The CreditTransaction model tracks credit additions and deductions with reasons
- The dashboard settings page has a static UI showing plan cards with upgrade buttons — but they don't do anything
- No Stripe integration exists anywhere in the codebase

## Requirements

### 1. Stripe integration backend
Create `api/billing.py`:
- Initialize Stripe with `STRIPE_SECRET_KEY` env var
- Define products/prices:
  - **Starter**: Free, 500 credits/month
  - **Pro**: $49/month, 5,000 credits/month
  - **Scale**: $149/month, 25,000 credits/month
  - **Enterprise**: Custom pricing, contact sales
- `create_checkout_session(user_id, plan)` → returns Stripe checkout URL
- `handle_webhook(payload, sig)` → processes `checkout.session.completed` and `invoice.paid` events to update user plan and credits
- Credit pack one-time purchases: 1,000 credits for $19, 5,000 for $79, 10,000 for $129

### 2. Billing API router
Create `api/routers/billing.py`:
- `POST /api/billing/checkout` — create Stripe checkout session for plan upgrade or credit pack
- `POST /api/billing/webhook` — Stripe webhook handler
- `GET /api/billing/portal` — redirect to Stripe customer portal for subscription management
- `GET /api/billing/history` — list CreditTransaction history for current user
- Mount in `api/main.py`

### 3. Dashboard billing UI
Update `dashboard/app/dashboard/settings/page.tsx`:
- Plan upgrade buttons call `POST /api/billing/checkout` and redirect to Stripe checkout
- Show credit transaction history
- Show current plan with "Manage Subscription" link (→ Stripe portal)
- Credit pack purchase buttons

### 4. Legal compliance pages
Create in dashboard:
- `dashboard/app/terms/page.tsx` — Terms of Service (template with key provisions for data services)
- `dashboard/app/privacy/page.tsx` — Privacy Policy (GDPR/CCPA compliant template)
- Add footer links to these pages in the dashboard layout

Create in API:
- `POST /api/leads/{id}/optout` — marks a lead as opted-out (add `opted_out: bool` column to Lead model)
- `GET /api/optout?email=X` — public endpoint for anyone to opt out of the database (no auth required)
- Opted-out leads are excluded from all exports and API responses

### 5. Environment variables
Document in `api/README.md`:
- `STRIPE_SECRET_KEY` — Stripe secret key (sk_test_...)
- `STRIPE_PUBLISHABLE_KEY` — Stripe publishable key (pk_test_...)
- `STRIPE_WEBHOOK_SECRET` — Stripe webhook signing secret (whsec_...)

## Acceptance Criteria
- [ ] `POST /api/billing/checkout` returns a valid Stripe checkout URL
- [ ] After completing Stripe checkout (test mode), user's plan and credits update in the database
- [ ] Credit transaction history shows in the dashboard settings page
- [ ] Terms of Service and Privacy Policy pages render at `/terms` and `/privacy`
- [ ] `GET /api/optout?email=test@example.com` marks the lead as opted out
- [ ] Opted-out leads don't appear in CSV exports or API lead listings
- [ ] All existing tests still pass

## Data Contracts
- **Stripe**: Checkout Sessions API, Customer Portal, Webhooks
- **Database**: `users.plan`, `users.credits_remaining`, `credit_transactions` table, `leads.opted_out` column
- **API**: `/api/billing/*` endpoints, `/api/optout` public endpoint
- **Dashboard**: Settings page calls billing API, redirects to Stripe checkout
