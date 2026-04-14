-- ============================================================
-- Demo Offers Platform — Supabase Schema
-- Source of truth for the data model.
-- ============================================================

-- Enable UUID generation
create extension if not exists "uuid-ossp";

-- ─── Vendors ────────────────────────────────────────────────

create table vendors (
  id            uuid primary key default uuid_generate_v4(),
  name          text not null,
  slug          text unique not null,
  website       text,
  domain        text unique,
  logo_url      text,
  category      text,
  description   text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index idx_vendors_slug on vendors (slug);
create index idx_vendors_domain on vendors (domain);

-- ─── Offers ─────────────────────────────────────────────────

create type offer_status as enum ('draft', 'active', 'expired', 'paused', 'archived');
create type reward_type  as enum ('gift_card', 'cash', 'credit', 'discount', 'swag', 'other');

create table offers (
  id                uuid primary key default uuid_generate_v4(),
  vendor_id         uuid not null references vendors(id) on delete cascade,
  title             text not null,
  slug              text unique not null,
  description       text,
  category          text,
  reward_type       reward_type not null default 'other',
  reward_value      text,                       -- e.g. "$50", "20% off", "Free tier"
  cta_url           text,
  status            offer_status not null default 'draft',
  region            text default 'Global',
  confidence_score  real default 0.0,           -- 0.0–1.0
  last_verified_at  timestamptz,
  expires_at        timestamptz,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create index idx_offers_slug on offers (slug);
create index idx_offers_vendor on offers (vendor_id);
create index idx_offers_status on offers (status);
create index idx_offers_category on offers (category);
create index idx_offers_confidence on offers (confidence_score desc);

-- ─── Offer Requirements ─────────────────────────────────────

create table offer_requirements (
  id          uuid primary key default uuid_generate_v4(),
  offer_id    uuid not null references offers(id) on delete cascade,
  label       text not null,                    -- e.g. "Schedule a 30-min demo"
  sort_order  int not null default 0,
  created_at  timestamptz not null default now()
);

create index idx_offer_requirements_offer on offer_requirements (offer_id);

-- ─── Rewards ────────────────────────────────────────────────

create table rewards (
  id            uuid primary key default uuid_generate_v4(),
  offer_id      uuid not null references offers(id) on delete cascade,
  type          reward_type not null,
  value         text not null,                  -- "$100 Amazon gift card"
  description   text,
  created_at    timestamptz not null default now()
);

create index idx_rewards_offer on rewards (offer_id);

-- ─── Offer Snapshots (raw crawl data) ───────────────────────

create table offer_snapshots (
  id              uuid primary key default uuid_generate_v4(),
  offer_id        uuid references offers(id) on delete set null,
  source_url      text not null,
  raw_text        text,
  parsed_json     jsonb,
  fetched_at      timestamptz not null default now(),
  change_summary  text
);

create index idx_snapshots_offer on offer_snapshots (offer_id);
create index idx_snapshots_fetched on offer_snapshots (fetched_at desc);

-- ─── Offer Sources (where the pipeline found offers) ────────

create table offer_sources (
  id            uuid primary key default uuid_generate_v4(),
  name          text not null,                  -- "G2 Demo Listings"
  source_type   text not null default 'directory', -- directory, search, manual
  base_url      text,
  config        jsonb default '{}',
  is_active     boolean not null default true,
  last_run_at   timestamptz,
  created_at    timestamptz not null default now()
);

-- ─── Users ──────────────────────────────────────────────────

create table users (
  id              uuid primary key default uuid_generate_v4(),
  email           text unique not null,
  name            text,
  avatar_url      text,
  role            text not null default 'user',  -- user, admin
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index idx_users_email on users (email);

-- ─── Saved Offers ───────────────────────────────────────────

create table saved_offers (
  id          uuid primary key default uuid_generate_v4(),
  user_id     uuid not null references users(id) on delete cascade,
  offer_id    uuid not null references offers(id) on delete cascade,
  notes       text,
  created_at  timestamptz not null default now(),
  unique (user_id, offer_id)
);

create index idx_saved_offers_user on saved_offers (user_id);

-- ─── Admin Notes ────────────────────────────────────────────

create table admin_notes (
  id          uuid primary key default uuid_generate_v4(),
  offer_id    uuid not null references offers(id) on delete cascade,
  author_id   uuid not null references users(id),
  content     text not null,
  created_at  timestamptz not null default now()
);

create index idx_admin_notes_offer on admin_notes (offer_id);

-- ─── Crawl State (pipeline freshness tracking) ──────────────

create table crawl_state (
  id              uuid primary key default uuid_generate_v4(),
  domain          text unique not null,
  last_crawled_at timestamptz not null default now(),
  offers_found    int default 0,
  status          text default 'completed',      -- completed, failed, timeout
  crawl_duration_s real,
  created_at      timestamptz not null default now()
);

create index idx_crawl_state_domain on crawl_state (domain);
create index idx_crawl_state_last on crawl_state (last_crawled_at);

-- ─── Row-Level Security (RLS) stubs ─────────────────────────
-- Enable RLS on user-facing tables; policies added when Supabase is connected.

alter table users enable row level security;
alter table saved_offers enable row level security;
alter table admin_notes enable row level security;
