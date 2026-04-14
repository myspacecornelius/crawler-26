import { getMockOffers } from "@/lib/supabase";
import { OfferGrid } from "@/components/offers/OfferGrid";
import { OfferFilters } from "@/components/offers/OfferFilters";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Browse Demo Offers — Demo Offers Platform",
  description:
    "Search and filter B2B demo incentives. Find gift cards, credits, and perks from top software vendors.",
};

export default function OffersPage() {
  const offers = getMockOffers();

  return (
    <div className="mx-auto max-w-7xl px-6 py-12 animate-fade-in">
      {/* ─── Page header ───────────────────────────────── */}
      <div className="mb-10">
        <h1 className="text-3xl sm:text-4xl font-bold">Demo Offers</h1>
        <p className="mt-2 text-zinc-400 text-lg">
          {offers.length} active offers from verified vendors
        </p>
      </div>

      {/* ─── Filters + Grid ────────────────────────────── */}
      <div className="flex flex-col lg:flex-row gap-8">
        <aside className="lg:w-64 shrink-0">
          <OfferFilters />
        </aside>
        <div className="flex-1">
          <OfferGrid offers={offers} />
        </div>
      </div>
    </div>
  );
}
