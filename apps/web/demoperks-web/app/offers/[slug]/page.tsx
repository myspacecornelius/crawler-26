import { getMockOfferBySlug, getMockOffers } from "@/lib/supabase";
import { Badge } from "@/components/ui/Badge";
import { confidenceLabel, confidenceColor, formatDate } from "@/lib/utils";
import {
  ExternalLink,
  Shield,
  MapPin,
  Clock,
  CheckCircle2,
  Bookmark,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";

interface Props {
  params: { slug: string };
}

export async function generateStaticParams() {
  return getMockOffers().map((o) => ({ slug: o.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const offer = getMockOfferBySlug(params.slug);
  if (!offer) return { title: "Offer Not Found" };
  return {
    title: `${offer.title} — Demo Offers`,
    description: offer.description ?? undefined,
  };
}

export default function OfferDetailPage({ params }: Props) {
  const offer = getMockOfferBySlug(params.slug);
  if (!offer) notFound();

  const vendor = offer.vendor;
  const scoreLabel = confidenceLabel(offer.confidenceScore);
  const scoreColor = confidenceColor(offer.confidenceScore);

  return (
    <div className="mx-auto max-w-4xl px-6 py-12 animate-fade-in">
      {/* ─── Back link ─────────────────────────────────── */}
      <Link
        href="/offers"
        className="inline-flex items-center gap-1.5 text-sm text-zinc-400 hover:text-white transition-colors mb-8"
      >
        <ArrowLeft className="h-4 w-4" /> All Offers
      </Link>

      {/* ─── Header card ───────────────────────────────── */}
      <div className="glass rounded-2xl p-8 mb-8">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <Badge variant="accent">{offer.category}</Badge>
              <Badge variant="outline">{offer.rewardType.replace("_", " ")}</Badge>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold leading-snug">
              {offer.title}
            </h1>
            {vendor && (
              <p className="text-zinc-400 mt-2">
                by{" "}
                <span className="text-zinc-200 font-medium">{vendor.name}</span>
              </p>
            )}
          </div>

          <div className="flex gap-3 shrink-0">
            <button className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 hover:border-zinc-500 px-4 py-2.5 text-sm font-medium transition-colors">
              <Bookmark className="h-4 w-4" /> Save
            </button>
            {offer.ctaUrl && (
              <a
                href={offer.ctaUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white px-6 py-2.5 text-sm font-semibold transition-colors"
              >
                Get This Offer
                <ExternalLink className="h-4 w-4" />
              </a>
            )}
          </div>
        </div>

        {/* ─── Meta row ──────────────────────────────── */}
        <div className="flex flex-wrap gap-5 text-sm text-zinc-400 border-t border-zinc-800 pt-5">
          <span className="flex items-center gap-1.5">
            <MapPin className="h-4 w-4" /> {offer.region}
          </span>
          <span className={`flex items-center gap-1.5 ${scoreColor}`}>
            <Shield className="h-4 w-4" /> {scoreLabel} confidence
          </span>
          <span className="flex items-center gap-1.5">
            <Clock className="h-4 w-4" /> Verified {formatDate(offer.lastVerifiedAt)}
          </span>
        </div>
      </div>

      {/* ─── Content grid ──────────────────────────────── */}
      <div className="grid md:grid-cols-3 gap-8">
        {/* Main content */}
        <div className="md:col-span-2 space-y-8">
          {/* Description */}
          <section>
            <h2 className="text-lg font-semibold mb-3">About this offer</h2>
            <p className="text-zinc-300 leading-relaxed">{offer.description}</p>
          </section>

          {/* Requirements */}
          {offer.requirements && offer.requirements.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold mb-3">Requirements</h2>
              <ul className="space-y-2.5">
                {offer.requirements.map((req) => (
                  <li
                    key={req.id}
                    className="flex items-start gap-2.5 text-zinc-300"
                  >
                    <CheckCircle2 className="h-5 w-5 text-brand-400 shrink-0 mt-0.5" />
                    {req.label}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>

        {/* Sidebar */}
        <aside className="space-y-6">
          {/* Reward card */}
          <div className="glass rounded-xl p-6">
            <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-3">
              Reward
            </h3>
            <p className="text-xl font-bold text-brand-300">
              {offer.rewardValue}
            </p>
          </div>

          {/* Vendor card */}
          {vendor && (
            <div className="glass rounded-xl p-6">
              <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-3">
                Vendor
              </h3>
              <p className="font-semibold">{vendor.name}</p>
              <p className="text-zinc-400 text-sm mt-1">{vendor.category}</p>
              {vendor.website && (
                <a
                  href={vendor.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-flex items-center gap-1 text-sm text-brand-400 hover:text-brand-300 transition-colors"
                >
                  Visit website <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
