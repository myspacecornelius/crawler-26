// ============================================================
// Demo Offers Platform — Domain Types
// Mirrors shared/schema.sql. Keep in sync.
// ============================================================

export type OfferStatus = "draft" | "active" | "expired" | "paused" | "archived";
export type RewardType = "gift_card" | "cash" | "credit" | "discount" | "swag" | "other";
export type UserRole = "user" | "admin";

// ─── Vendor ─────────────────────────────────────────────────

export interface Vendor {
  id: string;
  name: string;
  slug: string;
  website: string | null;
  domain: string | null;
  logoUrl: string | null;
  category: string | null;
  description: string | null;
  createdAt: string;
  updatedAt: string;
}

// ─── Offer ──────────────────────────────────────────────────

export interface Offer {
  id: string;
  vendorId: string;
  title: string;
  slug: string;
  description: string | null;
  category: string | null;
  rewardType: RewardType;
  rewardValue: string | null;
  ctaUrl: string | null;
  status: OfferStatus;
  region: string;
  confidenceScore: number;
  lastVerifiedAt: string | null;
  expiresAt: string | null;
  createdAt: string;
  updatedAt: string;
  // joined
  vendor?: Vendor;
  requirements?: OfferRequirement[];
  rewards?: Reward[];
}

// ─── Offer Requirement ──────────────────────────────────────

export interface OfferRequirement {
  id: string;
  offerId: string;
  label: string;
  sortOrder: number;
  createdAt: string;
}

// ─── Reward ─────────────────────────────────────────────────

export interface Reward {
  id: string;
  offerId: string;
  type: RewardType;
  value: string;
  description: string | null;
  createdAt: string;
}

// ─── Offer Snapshot (raw crawl data) ────────────────────────

export interface OfferSnapshot {
  id: string;
  offerId: string | null;
  sourceUrl: string;
  rawText: string | null;
  parsedJson: Record<string, unknown> | null;
  fetchedAt: string;
  changeSummary: string | null;
}

// ─── Offer Source ───────────────────────────────────────────

export interface OfferSource {
  id: string;
  name: string;
  sourceType: string;
  baseUrl: string | null;
  config: Record<string, unknown>;
  isActive: boolean;
  lastRunAt: string | null;
  createdAt: string;
}

// ─── User ───────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string | null;
  avatarUrl: string | null;
  role: UserRole;
  createdAt: string;
  updatedAt: string;
}

// ─── Saved Offer ────────────────────────────────────────────

export interface SavedOffer {
  id: string;
  userId: string;
  offerId: string;
  notes: string | null;
  createdAt: string;
  // joined
  offer?: Offer;
}

// ─── Admin Note ─────────────────────────────────────────────

export interface AdminNote {
  id: string;
  offerId: string;
  authorId: string;
  content: string;
  createdAt: string;
}

// ─── Crawl State ────────────────────────────────────────────

export interface CrawlState {
  id: string;
  domain: string;
  lastCrawledAt: string;
  offersFound: number;
  status: string;
  crawlDurationS: number | null;
  createdAt: string;
}

// ─── Filter / Query helpers ─────────────────────────────────

export interface OfferFilters {
  search?: string;
  category?: string;
  rewardType?: RewardType;
  region?: string;
  status?: OfferStatus;
  minConfidence?: number;
}

export interface PaginationParams {
  page: number;
  perPage: number;
}
