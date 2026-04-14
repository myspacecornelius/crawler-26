import { Bookmark, TrendingUp, Gift } from "lucide-react";
import { SavedOffersList } from "@/components/dashboard/SavedOffersList";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard — Demo Offers",
  description: "Your saved offers and activity.",
};

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-12 animate-fade-in">
      <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
      <p className="text-zinc-400 mb-10">Your saved offers and activity.</p>

      {/* ─── Stats row ─────────────────────────────────── */}
      <div className="grid sm:grid-cols-3 gap-5 mb-12">
        {[
          { icon: Bookmark, label: "Saved Offers", value: "3" },
          { icon: Gift, label: "Offers Claimed", value: "1" },
          { icon: TrendingUp, label: "New This Week", value: "12" },
        ].map((stat, i) => (
          <div key={i} className="glass rounded-xl p-6 flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-brand-600/15 text-brand-400">
              <stat.icon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm text-zinc-400">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* ─── Saved offers ──────────────────────────────── */}
      <section>
        <h2 className="text-xl font-semibold mb-5">Saved Offers</h2>
        <SavedOffersList />
      </section>
    </div>
  );
}
