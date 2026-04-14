import { getMockOffers } from "@/lib/supabase";
import { Badge } from "@/components/ui/Badge";
import { formatDate } from "@/lib/utils";
import { Plus, Pencil, Trash2, Eye } from "lucide-react";
import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Admin — Manage Offers",
  description: "Create, edit, and manage demo offers.",
};

export default function AdminOffersPage() {
  const offers = getMockOffers();

  return (
    <div className="mx-auto max-w-6xl px-6 py-12 animate-fade-in">
      <div className="flex items-center justify-between mb-10">
        <div>
          <h1 className="text-3xl font-bold">Manage Offers</h1>
          <p className="text-zinc-400 mt-1">{offers.length} total offers</p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white px-5 py-2.5 font-semibold transition-colors text-sm">
          <Plus className="h-4 w-4" /> New Offer
        </button>
      </div>

      {/* ─── Offers table ──────────────────────────────── */}
      <div className="glass rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 text-left text-zinc-400">
              <th className="px-6 py-4 font-medium">Offer</th>
              <th className="px-6 py-4 font-medium">Vendor</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium">Confidence</th>
              <th className="px-6 py-4 font-medium">Verified</th>
              <th className="px-6 py-4 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {offers.map((offer) => (
              <tr
                key={offer.id}
                className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors"
              >
                <td className="px-6 py-4">
                  <Link
                    href={`/offers/${offer.slug}`}
                    className="font-medium text-zinc-100 hover:text-brand-400 transition-colors"
                  >
                    {offer.title}
                  </Link>
                  <p className="text-zinc-500 text-xs mt-0.5">{offer.category}</p>
                </td>
                <td className="px-6 py-4 text-zinc-300">
                  {offer.vendor?.name ?? "—"}
                </td>
                <td className="px-6 py-4">
                  <Badge
                    variant={offer.status === "active" ? "success" : "outline"}
                  >
                    {offer.status}
                  </Badge>
                </td>
                <td className="px-6 py-4 text-zinc-300">
                  {Math.round(offer.confidenceScore * 100)}%
                </td>
                <td className="px-6 py-4 text-zinc-400">
                  {formatDate(offer.lastVerifiedAt)}
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      className="p-2 rounded-md hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors"
                      title="View"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    <button
                      className="p-2 rounded-md hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors"
                      title="Edit"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      className="p-2 rounded-md hover:bg-zinc-700 text-zinc-400 hover:text-red-400 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
