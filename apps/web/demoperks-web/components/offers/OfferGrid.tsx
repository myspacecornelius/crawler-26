import type { Offer } from "@/lib/types";
import { OfferCard } from "./OfferCard";

interface OfferGridProps {
  offers: Offer[];
}

export function OfferGrid({ offers }: OfferGridProps) {
  if (offers.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-zinc-400 text-lg">No offers found.</p>
        <p className="text-zinc-500 text-sm mt-1">Try adjusting your filters.</p>
      </div>
    );
  }

  return (
    <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-5">
      {offers.map((offer) => (
        <OfferCard key={offer.id} offer={offer} />
      ))}
    </div>
  );
}
