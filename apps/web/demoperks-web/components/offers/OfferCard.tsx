import Link from "next/link";
import type { Offer } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardFooter } from "@/components/ui/Card";
import { truncate, confidenceLabel, confidenceColor } from "@/lib/utils";
import { Gift, MapPin, Shield, ExternalLink } from "lucide-react";

interface OfferCardProps {
  offer: Offer;
}

export function OfferCard({ offer }: OfferCardProps) {
  const scoreLabel = confidenceLabel(offer.confidenceScore);
  const scoreColor = confidenceColor(offer.confidenceScore);

  return (
    <Link href={`/offers/${offer.slug}`}>
      <Card hover className="h-full flex flex-col">
        <CardContent className="flex-1 space-y-3 pt-6">
          {/* Category + reward type */}
          <div className="flex items-center gap-2">
            <Badge variant="accent">{offer.category}</Badge>
            <Badge variant="outline">{offer.rewardType.replace("_", " ")}</Badge>
          </div>

          {/* Title */}
          <h3 className="text-base font-semibold leading-snug">
            {offer.title}
          </h3>

          {/* Vendor */}
          {offer.vendor && (
            <p className="text-sm text-zinc-400">
              by {offer.vendor.name}
            </p>
          )}

          {/* Description */}
          {offer.description && (
            <p className="text-sm text-zinc-500 leading-relaxed">
              {truncate(offer.description, 120)}
            </p>
          )}

          {/* Reward highlight */}
          {offer.rewardValue && (
            <div className="flex items-center gap-2 text-brand-300 text-sm font-medium">
              <Gift className="h-4 w-4" />
              {offer.rewardValue}
            </div>
          )}
        </CardContent>

        <CardFooter>
          <div className="flex items-center justify-between text-xs text-zinc-500 w-full">
            <span className="flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" /> {offer.region}
            </span>
            <span className={`flex items-center gap-1 ${scoreColor}`}>
              <Shield className="h-3.5 w-3.5" /> {scoreLabel}
            </span>
          </div>
        </CardFooter>
      </Card>
    </Link>
  );
}
