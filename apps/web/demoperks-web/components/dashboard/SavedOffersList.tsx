import { getMockOffers } from "@/lib/supabase";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Gift, ExternalLink, Trash2 } from "lucide-react";

export function SavedOffersList() {
  const saved = getMockOffers().slice(0, 2); // simulate saved offers

  if (saved.length === 0) {
    return (
      <div className="glass rounded-xl p-10 text-center">
        <p className="text-zinc-400">No saved offers yet.</p>
        <Link
          href="/offers"
          className="mt-3 inline-block text-brand-400 text-sm hover:text-brand-300"
        >
          Browse offers →
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {saved.map((offer) => (
        <div
          key={offer.id}
          className="glass rounded-xl p-5 flex items-center justify-between gap-4 hover:border-zinc-600 transition-colors"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="accent">{offer.category}</Badge>
              {offer.rewardValue && (
                <span className="flex items-center gap-1 text-xs text-brand-300">
                  <Gift className="h-3.5 w-3.5" /> {offer.rewardValue}
                </span>
              )}
            </div>
            <Link
              href={`/offers/${offer.slug}`}
              className="font-medium text-zinc-100 hover:text-brand-400 transition-colors line-clamp-1"
            >
              {offer.title}
            </Link>
            <p className="text-xs text-zinc-500 mt-0.5">
              {offer.vendor?.name}
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {offer.ctaUrl && (
              <a
                href={offer.ctaUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-md hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors"
                title="Visit offer"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            )}
            <button
              className="p-2 rounded-md hover:bg-zinc-700 text-zinc-400 hover:text-red-400 transition-colors"
              title="Remove"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
