/**
 * Supabase client initialization.
 * Connection deferred — will be wired when NEXT_PUBLIC_SUPABASE_URL
 * and NEXT_PUBLIC_SUPABASE_ANON_KEY are set.
 */

// import { createBrowserClient } from "@supabase/ssr";
//
// export function createClient() {
//   return createBrowserClient(
//     process.env.NEXT_PUBLIC_SUPABASE_URL!,
//     process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
//   );
// }

// ─── Placeholder: mock data for MVP development ─────────────

import type { Offer, Vendor } from "./types";

const MOCK_VENDORS: Vendor[] = [
  {
    id: "v1",
    name: "Acme Analytics",
    slug: "acme-analytics",
    website: "https://acme-analytics.io",
    domain: "acme-analytics.io",
    logoUrl: null,
    category: "Analytics",
    description: "Real-time product analytics for B2B SaaS.",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: "v2",
    name: "CloudSync Pro",
    slug: "cloudsync-pro",
    website: "https://cloudsync.pro",
    domain: "cloudsync.pro",
    logoUrl: null,
    category: "Infrastructure",
    description: "Enterprise data sync and integration platform.",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: "v3",
    name: "SecureVault",
    slug: "securevault",
    website: "https://securevault.com",
    domain: "securevault.com",
    logoUrl: null,
    category: "Security",
    description: "Zero-trust secrets management for teams.",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

const MOCK_OFFERS: Offer[] = [
  {
    id: "o1",
    vendorId: "v1",
    title: "$75 Amazon Gift Card for a 30-min Demo",
    slug: "acme-analytics-75-gift-card",
    description:
      "Schedule and complete a personalized 30-minute demo of Acme Analytics with a qualified account executive. Available for companies with 50+ employees.",
    category: "Analytics",
    rewardType: "gift_card",
    rewardValue: "$75 Amazon Gift Card",
    ctaUrl: "https://acme-analytics.io/demo",
    status: "active",
    region: "US",
    confidenceScore: 0.92,
    lastVerifiedAt: new Date().toISOString(),
    expiresAt: null,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    vendor: MOCK_VENDORS[0],
    requirements: [
      { id: "r1", offerId: "o1", label: "Company size 50+ employees", sortOrder: 0, createdAt: new Date().toISOString() },
      { id: "r2", offerId: "o1", label: "Schedule a 30-min live demo", sortOrder: 1, createdAt: new Date().toISOString() },
      { id: "r3", offerId: "o1", label: "Use a business email", sortOrder: 2, createdAt: new Date().toISOString() },
    ],
  },
  {
    id: "o2",
    vendorId: "v2",
    title: "$100 Visa Prepaid for CloudSync Pro Trial",
    slug: "cloudsync-pro-100-visa",
    description:
      "Complete a guided product tour and 14-day trial of CloudSync Pro. Visa prepaid card delivered after trial completion and feedback survey.",
    category: "Infrastructure",
    rewardType: "gift_card",
    rewardValue: "$100 Visa Prepaid",
    ctaUrl: "https://cloudsync.pro/demo-incentive",
    status: "active",
    region: "Global",
    confidenceScore: 0.85,
    lastVerifiedAt: new Date().toISOString(),
    expiresAt: null,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    vendor: MOCK_VENDORS[1],
    requirements: [
      { id: "r4", offerId: "o2", label: "Manager+ title at a B2B company", sortOrder: 0, createdAt: new Date().toISOString() },
      { id: "r5", offerId: "o2", label: "Complete 14-day trial", sortOrder: 1, createdAt: new Date().toISOString() },
    ],
  },
  {
    id: "o3",
    vendorId: "v3",
    title: "Free Team License (1 Year) — SecureVault",
    slug: "securevault-free-team-license",
    description:
      "Get a free team license (up to 10 seats) for one year after completing a 20-minute product demo and security assessment.",
    category: "Security",
    rewardType: "credit",
    rewardValue: "Free 1-year team license",
    ctaUrl: "https://securevault.com/demo",
    status: "active",
    region: "US, EU",
    confidenceScore: 0.78,
    lastVerifiedAt: new Date().toISOString(),
    expiresAt: null,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    vendor: MOCK_VENDORS[2],
    requirements: [
      { id: "r6", offerId: "o3", label: "Engineering or security team lead", sortOrder: 0, createdAt: new Date().toISOString() },
      { id: "r7", offerId: "o3", label: "20-min product demo", sortOrder: 1, createdAt: new Date().toISOString() },
    ],
  },
];

export function getMockOffers(): Offer[] {
  return MOCK_OFFERS;
}

export function getMockOfferBySlug(slug: string): Offer | undefined {
  return MOCK_OFFERS.find((o) => o.slug === slug);
}

export function getMockVendors(): Vendor[] {
  return MOCK_VENDORS;
}
